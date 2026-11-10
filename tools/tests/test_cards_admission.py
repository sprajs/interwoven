"""Offline source-cache and semantic-admission regression tests."""
import copy
import concurrent.futures
import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cards'))
import fetch_page
import check_quotes
import gates
import admit
from tests.test_dataset import FixtureDataset, discovery

QUOTE = 'The workshop constructed a working steam engine in the year eighteen hundred.'
PAGE = 'An institutional catalogue describes a historical workshop and its equipment. ' + QUOTE + ' The source qualifies this as a local demonstration rather than a global priority claim.'


class CachedSources(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name)
        self.patch = patch.object(fetch_page, 'PAGES', self.cache)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def save(self, url='https://example.test/source', text=PAGE):
        fetch_page._save(url, text, 'fetched', 1000)
        return url

    def test_saved_source_precedes_network_and_has_provenance(self):
        url = self.save()
        with patch.object(fetch_page, 'fetch', side_effect=AssertionError('network used')):
            self.assertEqual(fetch_page.page_text(url), PAGE)
        saved = fetch_page.source_snapshot(url)
        self.assertEqual(saved['content_sha256'], fetch_page.sha256(PAGE))
        self.assertEqual(saved['url_sha256'], fetch_page.sha256(url))
        self.assertIn('accessed_at', saved)
        self.assertTrue((self.cache / 'content' / (fetch_page.sha256(PAGE) + '.txt')).exists())

    def test_explicit_saved_import_checks_hash_and_records_import_time(self):
        saved = self.cache / 'frozen.txt'
        saved.write_text(PAGE, encoding='utf-8')
        url = 'https://frozen.test/document'
        imported = fetch_page.import_saved(url, saved, fetch_page.sha256(PAGE),
                                          {'description': 'Frozen institutional page assigned to this URL.'})
        self.assertEqual(imported['text'], PAGE)
        self.assertEqual(imported['acquired_via'], 'saved-import')
        self.assertIsNone(imported['accessed_at'])
        self.assertIn('imported_at', imported)
        with patch.object(fetch_page, 'fetch', side_effect=AssertionError('unexpected request')):
            self.assertEqual(fetch_page.page_text(url), PAGE)
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            fetch_page.import_saved('https://frozen.test/other', saved, '0' * 64, 'Assigned source')
        self.assertEqual(fetch_page.source_snapshot('https://frozen.test/other')['status'], 'missing')
        saved.write_text('Verify you are human', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'blocked'):
            fetch_page.import_saved(url, saved, fetch_page.sha256('Verify you are human'), 'Assigned source')


    def test_long_and_punctuation_collisions_are_distinct(self):
        prefix = 'https://example.test/' + 'a' * 180
        urls = [prefix + '/1?x=a-b', prefix + '/2?x=a_b']
        for url in urls:
            self.save(url, PAGE + url)
        self.assertNotEqual(fetch_page.path_for(urls[0]), fetch_page.path_for(urls[1]))
        self.assertEqual(fetch_page.page_text(urls[0]), PAGE + urls[0])
        self.assertEqual(fetch_page.page_text(urls[1]), PAGE + urls[1])

    def test_botcheck_and_empty_are_negative_cached_then_expire(self):
        for body, expected in [(b'<title>Just a moment...</title> Verify you are human', 'blocked'),
                               (b'<html><script>nothing</script></html>', 'extraction-failed')]:
            with self.subTest(status=expected):
                url = 'https://example.test/' + expected
                with patch.object(fetch_page, 'time') as clock, patch.object(fetch_page, 'fetch', return_value=(body, 'text/html')) as fetch:
                    clock.time.return_value = 1000
                    self.assertEqual(fetch_page.page_text(url), '')
                    self.assertEqual(fetch_page.source_snapshot(url)['status'], expected)
                    clock.time.return_value = 1001
                    self.assertEqual(fetch_page.page_text(url, refresh=True), '')
                    self.assertEqual(fetch.call_count, 1)
                    clock.time.return_value = 1000 + fetch_page.NEGATIVE_TTL + 1
                    fetch.return_value = (PAGE.encode(), 'text/plain')
                    self.assertEqual(fetch_page.page_text(url), PAGE)
                    self.assertEqual(fetch.call_count, 2)

    def test_transient_retry_is_bounded(self):
        with patch.object(fetch_page, 'fetch', side_effect=OSError('offline')) as fetch:
            self.assertEqual(fetch_page.page_text('https://offline.test/source'), '')
            self.assertEqual(fetch.call_count, fetch_page.MAX_ATTEMPTS)
            self.assertEqual(fetch_page.page_text('https://offline.test/source'), '')
            self.assertEqual(fetch.call_count, fetch_page.MAX_ATTEMPTS)

    def test_exhausted_service_defers_other_urls_but_saved_sources_work(self):
        saved = self.save('https://budget.test/saved')
        error = HTTPError('https://budget.test/a', 429, 'exhausted', {}, io.BytesIO())
        self.addCleanup(error.close)
        with patch.object(fetch_page, 'fetch', side_effect=error) as fetch:
            self.assertEqual(fetch_page.page_text('https://budget.test/a'), '')
            self.assertEqual(fetch_page.page_text('https://budget.test/b'), '')
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(fetch_page.source_snapshot('https://budget.test/b')['status'], 'search-budget-exhausted')
            self.assertEqual(fetch_page.page_text(saved), PAGE)

    def test_single_flight_shares_one_request_between_threads(self):
        def retrieve(url):
            time.sleep(.02)
            return PAGE.encode(), 'text/plain'
        with patch.object(fetch_page, 'fetch', side_effect=retrieve) as fetch:
            with concurrent.futures.ThreadPoolExecutor(8) as pool:
                texts = list(pool.map(fetch_page.page_text, ['https://single.test/page'] * 8))
            self.assertEqual(texts, [PAGE] * 8)
            self.assertEqual(fetch.call_count, 1)

    def test_corrupted_content_is_not_used_as_saved_evidence(self):
        url = self.save()
        fetch_page.path_for(url).write_text(PAGE + ' changed')
        self.assertEqual(fetch_page.source_snapshot(url)['text'], '')
        with patch.object(fetch_page, 'fetch', return_value=(PAGE.encode(), 'text/plain')) as fetch:
            self.assertEqual(fetch_page.page_text(url), PAGE)
            self.assertEqual(fetch.call_count, 1)


class AdmissionGates(unittest.TestCase):
    setUp = CachedSources.setUp
    save = CachedSources.save

    def card(self):
        url = self.save()
        return {'name': 'Workshop steam engine', 'description': 'A workshop constructed a working steam engine.',
                'kind': 'technology', 'field': 'energy.steam', 'verdict': 'accept',
                'summary': 'Unsupported extra summary', 'origin': 'independent',
                'impact': {'reach': 3, 'depth': 3, 'generativity': 3},
                'sources': [{'url': url, 'title': 'Workshop catalogue', 'authors': ['Museum']}],
                'events': [{'type': 'invention', 'earliest_year': 1800, 'latest_year': 1800,
                            'status': 'known', 'precision': 'year', 'statement': 'A working steam engine was constructed.',
                            'source': 0, 'quote': QUOTE}]}

    def review(self, card):
        claims = {path: {'decision': 'accept', 'sources': [0], 'rationale': 'The passage supports this scoped claim.'}
                  for path in ('name', 'description', 'kind', 'field', 'events.0.statement', 'events.0.date')}
        return {'schema_version': 1, 'card_digest': gates.digest_card(card),
                'evidence_digest': gates.evidence_digest(card), 'dataset_snapshot': 'snapshot',
                'reviewer': {'id': 'independent-reader', 'independent': True},
                'extractor_id': 'extractor', 'decision': 'accept', 'claims': claims}

    def compile(self, card, review):
        data = FixtureDataset.make([])
        envelope = {'cards': [card], 'semantic_reviews': {gates.digest_card(card): review}}
        return admit.compile_cards([envelope], data, 'snapshot'), data

    def test_exact_is_presence_only_and_short_quotes_do_not_qualify(self):
        card = self.card()
        self.assertEqual(check_quotes.check(card['sources'][0]['url'], QUOTE), 'exact')
        self.assertEqual(check_quotes.check(card['sources'][0]['url'], 'working steam engine'), 'insufficient_quote')
        self.assertTrue(gates.validate_review(card, None, 'snapshot'))
        self.assertEqual(self.compile(card, None)[0][0], {})

    def test_near_quote_is_never_admitted_even_with_semantic_acceptance(self):
        card = self.card()
        card['events'][0]['quote'] = QUOTE + ' This entirely invented sentence changes the claimed meaning.'
        self.assertEqual(check_quotes.check(card['sources'][0]['url'], card['events'][0]['quote']), 'near')
        review = self.review(card)
        self.assertTrue(gates.validate_review(card, review, 'snapshot'))
        self.assertEqual(self.compile(card, review)[0][0], {})

    def test_locate_requires_entire_quote_and_preserves_original_offsets(self):
        misleading = 'The workshop constructed a different contraption in another place. '
        text = misleading + PAGE
        span = gates.locate_span(text, QUOTE)
        self.assertIsNotNone(span)
        self.assertEqual(text[span[0]:span[1]], QUOTE.rstrip('.'))
        self.assertGreater(span[0], len(misleading))
        self.assertIsNone(admit.locate(misleading, QUOTE))
        accented = 'The café &amp; museum constructed a working steam engine during eighteen hundred.'
        quote = 'The cafe and museum constructed a working steam engine during eighteen hundred'
        self.assertIsNone(gates.locate_span(accented, quote))
        quote = 'The cafe museum constructed a working steam engine during eighteen hundred'
        span = gates.locate_span(accented, quote)
        self.assertEqual(accented[span[0]:span[1]], accented.rstrip('.'))

    def test_stale_card_evidence_and_dataset_reviews_block(self):
        card = self.card()
        review = self.review(card)
        self.assertEqual(gates.validate_review(card, review, 'snapshot'), [])
        self.assertIn('missing or stale dataset_snapshot', gates.validate_review(card, review, 'next'))
        changed = copy.deepcopy(card)
        changed['events'][0]['latest_year'] = 1801
        self.assertIn('missing or stale card_digest', gates.validate_review(changed, review, 'snapshot'))
        self.save(card['sources'][0]['url'], PAGE + ' Updated contextual qualification.')
        self.assertIn('missing or stale evidence_digest', gates.validate_review(card, review, 'snapshot'))

    def test_self_review_negative_and_boolean_source_indices_fail_closed(self):
        for index in (-1, True, 100):
            card = self.card()
            card['events'][0]['source'] = index
            self.assertTrue(gates.validate_review(card, self.review(card), 'snapshot'))
        card = self.card()
        review = self.review(card)
        review['reviewer']['id'] = review['extractor_id']
        self.assertIn('review must be independent of extractor', gates.validate_review(card, review, 'snapshot'))
        review['claims'] = []
        self.assertTrue(gates.validate_review(card, review, 'snapshot'))

    def test_minimal_supported_record_omits_unreviewed_facets_and_validates(self):
        card = self.card()
        (records, sources, _, report, problems), data = self.compile(card, self.review(card))
        self.assertEqual(problems, [])
        self.assertEqual(report['accepted'], 1)
        record = next(iter(records.values()))
        for facet in ('summary', 'impact', 'tier', 'grain', 'origin'):
            self.assertNotIn(facet, record)
        self.assertEqual(record['research']['basis']['events'], 'reviewed')
        data.discoveries.update(records)
        data.sources.update(sources)
        data.paths.update({'sources/' + key: admit.ds.source_path(key) for key in sources})
        data.paths.update({'discoveries/' + key: admit.ds.discovery_path(row) for key, row in records.items()})
        self.assertEqual(data.validate(check_files=False), [])

    def test_link_needs_explicit_semantic_relation_direction_and_context(self):
        card = self.card()
        card['links'] = [{'to': 'Earlier engine', 'type': 'builds_on', 'statement': 'Used earlier engine design.',
                          'source': 0, 'quote': QUOTE}]
        review = self.review(card)
        review['claims']['links.0'] = {'decision': 'accept', 'sources': [0], 'rationale': 'Explicit dependence.'}
        self.assertFalse(gates.link_supported(card, review, 0))
        for key in ('relation', 'direction', 'context'):
            review['claims']['links.0'][key] = True
        self.assertTrue(gates.link_supported(card, review, 0))
        review['claims']['links.0']['direction'] = False
        self.assertFalse(gates.link_supported(card, review, 0))

    def test_independence_needs_distinct_independent_source_support(self):
        card = self.card()
        review = self.review(card)
        claim = {'decision': 'accept', 'sources': [0], 'rationale': 'Independent achievement.',
                 'independent_support': True, 'independent_source_groups': {'0': 'museum'}}
        review['claims']['origin'] = claim
        self.assertFalse(gates.claim_supported(card, review, 'origin'))
        second = self.save('https://independent.test/source')
        card['sources'].append({'url': second, 'title': 'Independent study'})
        card['events'].append(dict(card['events'][0], source=1))
        claim['sources'] = [0, 1]
        claim['independent_source_groups']['1'] = 'independent study'
        self.assertTrue(gates.claim_supported(card, review, 'origin'))
        claim['independent_source_groups']['1'] = 'museum'
        self.assertFalse(gates.claim_supported(card, review, 'origin'))

    def test_apply_requires_lease_and_stale_sources_cannot_write(self):
        from workflow import Queue
        card = self.card()
        (records, sources, concepts, _, _), data = self.compile(card, self.review(card))
        with patch.object(admit.ds, 'write_json') as write:
            with self.assertRaisesRegex(ValueError, 'integrator lease'):
                admit.apply_records(records, sources, concepts, data)
            write.assert_not_called()
        queue = Queue(self.cache / 'workflow.sqlite')
        lease = queue.claim_integrator('test-integrator')
        self.addCleanup(lambda: queue.release_integrator(lease))
        self.assertIsNone(queue.claim_integrator('second-writer'))
        self.save(card['sources'][0]['url'], PAGE + ' Changed qualification.')
        with patch.object(admit.ds, 'write_json') as write:
            with self.assertRaisesRegex(ValueError, 'version changed'):
                admit.apply_records(records, sources, concepts, data, root=self.cache,
                                    queue=queue, lease=lease)
            write.assert_not_called()
            self.assertFalse((self.cache / 'evidence').exists())

    def test_apply_preflights_invalid_staged_record_without_writing(self):
        from workflow import Queue
        card = self.card()
        (records, sources, concepts, _, _), data = self.compile(card, self.review(card))
        next(iter(records.values()))['origin'] = 'made-up-origin'
        queue = Queue(self.cache / 'workflow.sqlite')
        lease = queue.claim_integrator('test-integrator')
        self.addCleanup(lambda: queue.release_integrator(lease))
        with patch.object(admit.ds, 'write_json') as write:
            with self.assertRaisesRegex(ValueError, 'staged dataset invalid'):
                admit.apply_records(records, sources, concepts, data, root=self.cache,
                                    queue=queue, lease=lease)
            write.assert_not_called()


    def extension_fixture(self, old_year=1790):
        old = discovery('workshop-steam-engine')
        old['summary'] = 'Original bounded summary.'
        old['research']['basis']['summary'] = 'recalled'
        old['research']['note'] = 'Preserve this original research note.'
        old['events'][0]['id'] = 'invention-1'
        old['events'][0]['date']['earliest'] = {'year': old_year}
        old['events'][0]['date']['latest'] = {'year': old_year}
        old['earliest_record']['event'] = 'invention-1'
        data = FixtureDataset.make([old])
        card = self.card()
        card['extends'] = old['id']
        review = self.review(card)
        review['claims']['extends'] = {'decision': 'accept', 'sources': [0],
                                       'rationale': 'The passage concerns a later event in this exact community capability.'}
        return data, card, review

    def compile_extension(self, data, card, review):
        return admit.compile_cards([{'cards': [card], 'semantic_reviews': {gates.digest_card(card): review}}], data, 'snapshot')

    def test_explicit_reviewed_extension_preserves_old_record_and_input_objects(self):
        data, card, review = self.extension_fixture()
        originals = copy.deepcopy(data.discoveries)
        original_sources = copy.deepcopy(data.sources)
        review['claims']['summary'] = dict(review['claims']['extends'])
        records, sources, _, report, problems = self.compile_extension(data, card, review)
        self.assertEqual(problems, [])
        self.assertEqual(report['extended'], 1)
        self.assertEqual(set(records), {'workshop-steam-engine'})
        extended = records['workshop-steam-engine']
        old = originals['workshop-steam-engine']
        for facet in ('id', 'name', 'description', 'kind', 'domain', 'summary', 'places', 'people', 'earliest_record'):
            self.assertEqual(extended[facet], old[facet])
        self.assertEqual(extended['events'][0], old['events'][0])
        self.assertEqual(extended['events'][1]['id'], 'invention-1-2')
        self.assertEqual(extended['research']['status'], 'draft')
        self.assertEqual(extended['research']['basis']['events'], old['research']['basis']['events'])
        self.assertTrue(extended['research']['note'].startswith(old['research']['note']))
        self.assertEqual(data.discoveries, originals)
        self.assertEqual(data.sources, original_sources)
        again = self.compile_extension(data, card, review)[0]
        self.assertEqual(again, records)

    def test_extension_adds_only_individually_reviewed_optional_facets(self):
        data, card, review = self.extension_fixture()
        card['known_from'] = [next(iter(data.vocab['known_from']['values']))]
        card['fate'] = next(iter(data.vocab['fate']['values']))
        review['card_digest'] = gates.digest_card(card)
        review['claims']['known_from'] = {'decision': 'accept', 'sources': [0], 'rationale': 'The source identifies this evidence type.'}
        records, _, _, _, problems = self.compile_extension(data, card, review)
        self.assertEqual(problems, [])
        record = records['workshop-steam-engine']
        self.assertEqual(record['known_from'], card['known_from'])
        self.assertEqual(record['research']['basis']['known_from'], 'reviewed')
        self.assertNotIn('fate', record)
        self.assertEqual(record['summary'], 'Original bounded summary.')


    def test_bare_duplicate_is_not_inferred_to_be_an_extension(self):
        data, card, _ = self.extension_fixture()
        card.pop('extends')
        review = self.review(card)
        records, _, _, report, problems = self.compile_extension(data, card, review)
        self.assertEqual(records, {})
        self.assertEqual(report['duplicate'], 1)
        self.assertEqual(problems, [])

    def test_extension_requires_independent_target_review_and_current_bindings(self):
        data, card, review = self.extension_fixture()
        review['claims'].pop('extends')
        records, _, _, report, _ = self.compile_extension(data, card, review)
        self.assertEqual(records, {})
        self.assertEqual(report['semantic gate blocked'], 1)
        review = self.review(card)
        review['claims']['extends'] = {'decision': 'accept', 'sources': [0], 'rationale': 'Same community capability.'}
        review['dataset_snapshot'] = 'stale'
        self.assertEqual(self.compile_extension(data, card, review)[0], {})
        review['dataset_snapshot'] = 'snapshot'
        card['extends'] = 'nonexistent-target'
        self.assertEqual(self.compile_extension(data, card, review)[0], {})
        review['card_digest'] = gates.digest_card(card)
        self.assertTrue(self.compile_extension(data, card, review)[4])

    def test_extension_identity_can_be_omitted_and_earlier_event_updates_bounded_anchor(self):
        data, card, _ = self.extension_fixture(old_year=1820)
        for field in ('name', 'description', 'kind', 'field'):
            card.pop(field)
        review = self.review(card)
        review['claims'] = {key: value for key, value in review['claims'].items() if key.startswith('events.')}
        review['claims']['extends'] = {'decision': 'accept', 'sources': [0], 'rationale': 'Earlier scoped evidence for the target capability.'}
        records, sources, _, report, problems = self.compile_extension(data, card, review)
        self.assertEqual(problems, [])
        record = records['workshop-steam-engine']
        self.assertEqual(record['earliest_record']['event'], 'invention-1-2')
        self.assertIn('no claim of global priority', record['earliest_record']['rationale'])
        self.assertEqual(record['events'][0], data.discoveries['workshop-steam-engine']['events'][0])
        self.assertEqual(record['research']['status'], 'draft')
        data.discoveries.update(records)
        data.sources.update(sources)
        data.paths.update({'sources/' + key: admit.ds.source_path(key) for key in sources})
        self.assertEqual(data.validate(check_files=False), [])

    def test_exact_repeated_extension_event_is_a_noop_even_with_another_generated_id(self):
        data, card, review = self.extension_fixture(old_year=1800)
        old_event = data.discoveries['workshop-steam-engine']['events'][0]
        old_event['type'] = card['events'][0]['type']
        old_event['statement'] = card['events'][0]['statement']
        old_event['date']['status'] = card['events'][0]['status']
        old_event['date']['precision'] = card['events'][0]['precision']
        old_event['date']['basis'] = 'Different old review prose is immaterial.'
        records, sources, _, report, problems = self.compile_extension(data, card, review)
        self.assertEqual(records, {})
        self.assertEqual(sources, {})
        self.assertEqual(report['extension unchanged'], 1)
        self.assertEqual(problems, [])


    def test_unsupported_date_interpretation_prevents_admission(self):
        card = self.card()
        review = self.review(card)
        review['claims']['events.0.date']['decision'] = 'defer'
        self.assertEqual(self.compile(card, review)[0][0], {})


if __name__ == '__main__':
    unittest.main()

"""Keep unresolved history out of the established-relationship diagram."""
import unittest
from render_research_round import render


class ResearchRoundRenderTest(unittest.TestCase):
    def fixture(self):
        return {'lanes': {'test': {'title': 'Test', 'next_questions': []}},
                'unresolved_edges': [{'lane': 'test', 'statement': 'Candidate only'}]}

    def test_unresolved_is_text_not_edge(self):
        output = render(self.fixture())
        self.assertIn('Candidate only', output)
        self.assertNotIn('class="edge"', output)

    def test_misclassified_edge_is_rejected(self):
        data = self.fixture()
        data['accepted_established_edges'] = [{'status': 'candidate', 'review_decision': 'accept'}]
        with self.assertRaises(ValueError):
            render(data)

    def test_edge_scope_and_uncertainty_are_visible(self):
        data = self.fixture()
        data['accepted_established_edges'] = [{'lane': 'test', 'status': 'established',
            'review_decision': 'accept', 'type': 'uses_process', 'from_name': 'Process',
            'to_name': 'Product', 'statement': 'A reconstruction.',
            'scope': 'Only four samples <not every vessel>.', 'caveats': 'Preparation remains unknown.'}]
        output = render(data)
        self.assertIn('<strong>Scope:</strong> Only four samples &lt;not every vessel&gt;.', output)
        self.assertIn('<strong>Uncertainty:</strong> Preparation remains unknown.', output)
        self.assertLess(output.index('<strong>Scope:'), output.index('Unresolved questions'))

    def test_source_text_and_urls_are_not_executable(self):
        data = self.fixture()
        data['supported_circumstances'] = [{'lane': 'test', 'review_decision': 'accept',
            'record_name': 'A', 'facet': 'why', 'statement': '<script>bad()</script>',
            'evidence': [{'source': 'x', 'locator': 'p. 1'}]}]
        data['sources'] = {'x': {'title': 'Source', 'url': 'javascript:bad()'}}
        output = render(data)
        self.assertIn('&lt;script&gt;bad()&lt;/script&gt;', output)
        self.assertNotIn('javascript:', output)


if __name__ == '__main__':
    unittest.main()

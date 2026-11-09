import functools
import gzip
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

from serve import Handler, prepare


class HttpCacheTest(unittest.TestCase):
    def test_gzip_etags_revalidation_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            core='data/core/'+'a'*24+'.json'
            (root/core).parent.mkdir(parents=True)
            (root/core).write_text('{"test":1}')
            (root/'data/manifest.json').write_text('{}')
            (root/'index.html').write_text('<p>Test</p>')
            prepare(root)
            server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=directory))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}/'
            try:
                with urlopen(Request(base+core,headers={'Accept-Encoding':'gzip'})) as response:
                    self.assertIn('immutable',response.headers['Cache-Control'])
                    self.assertEqual(response.headers['Content-Encoding'],'gzip')
                    self.assertEqual(json.loads(gzip.decompress(response.read())),{'test':1})
                    etag=response.headers['ETag']
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base+core,headers={'Accept-Encoding':'gzip','If-None-Match':etag}))
                self.assertEqual(caught.exception.code,304)
                caught.exception.close()
                with urlopen(base+'data/manifest.json') as response:
                    self.assertEqual(response.headers['Cache-Control'],'no-cache')
                with urlopen(Request(base+core,headers={'Accept-Encoding':'gzip;q=0'})) as response:
                    self.assertIsNone(response.headers['Content-Encoding'])
                    self.assertEqual(json.loads(response.read()),{'test':1})
                with self.assertRaises(HTTPError) as caught:
                    urlopen(base+'data/details/missing.json')
                self.assertEqual(caught.exception.code,404)
                caught.exception.close()
            finally:
                server.shutdown();thread.join();server.server_close()

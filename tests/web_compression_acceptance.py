"""Regression: compressed HTML must become evidence, never binary-looking text."""
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "core" / "app"))
import main as app


class CompressionTests(unittest.TestCase):
    def test_fetch_compressed_html_becomes_readable_evidence(self):
        html = ("<html><title>Compressed article</title><main><p>"
                + "Python supports readable programs, reusable modules, and practical tools. " * 30
                + "</p><p>Marker 4815.</p></main></html>").encode()
        for encoding, body in [("gzip", gzip.compress(html)), ("deflate", zlib.compress(html))]:
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Encoding", encoding)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def log_message(self, *args):
                    pass
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                # Allow this test's loopback fixture only; production SSRF checks stay unchanged.
                with patch.object(app, "validate_public_url", side_effect=lambda value: value):
                    page = app.fetch_static_url(f"http://127.0.0.1:{server.server_port}/")
                self.assertEqual(page["title"], "Compressed article")
                excerpt = app._clean_web_excerpt(page["text"])
                self.assertIn("Python supports readable programs", excerpt)
                self.assertIn("Marker 4815", excerpt)
                self.assertNotIn("\ufffd", excerpt)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_output_limit_and_truncation(self):
        with self.assertRaises(ValueError):
            app.decode_web_body(gzip.compress(b"A" * 100_000), "gzip", 1000)
        with self.assertRaises(ValueError):
            app.decode_web_body(gzip.compress(b"hello")[:-4], "gzip", 1000)
        with self.assertRaises(ValueError):
            app.decode_web_body(b"unknown", "br", 1000)

    def test_raw_deflate_and_identity(self):
        compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        raw = compressor.compress(b"readable") + compressor.flush()
        self.assertEqual(app.decode_web_body(raw, "deflate", 1000), b"readable")
        self.assertEqual(app.decode_web_body(b"text", "", 4), b"text")

    def test_navigation_filter_retains_its_guard(self):
        navigation = ", ".join("Navigation item " + str(i) for i in range(100))
        self.assertEqual(app._clean_web_excerpt(navigation), "")


if __name__ == "__main__":
    unittest.main()

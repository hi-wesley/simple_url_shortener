#!/usr/bin/env python3
"""
A simple URL shortening web application using Python's built‑in http.server and sqlite3.

Functional requirements follow typical URL shortener design: given a long URL, the service generates a short unique alias and stores the mapping. When a user visits the short URL, they are redirected to the original long URL.
Non‑functional requirements such as short URL unpredictability are addressed by generating a random alphanumeric code.

To run:
    python3 url_shortener.py
The server listens on port 8000 and persists mappings in urls.db in the working directory.
"""
import http.server
import socketserver
import urllib.parse
import string
import random
import sqlite3
import os
from datetime import datetime

DB_FILE = 'urls.db'

# Ensure the database and table exist

def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    with conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS urls (\n"
            "  code TEXT PRIMARY KEY,\n"
            "  long_url TEXT NOT NULL,\n"
            "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            ")"
        )
    conn.close()


def generate_code(length: int = 6) -> str:
    """Generate a random alphanumeric code not already in the database."""
    chars = string.ascii_letters + string.digits
    conn = sqlite3.connect(DB_FILE)
    try:
        while True:
            code = ''.join(random.choice(chars) for _ in range(length))
            row = conn.execute('SELECT 1 FROM urls WHERE code=?', (code,)).fetchone()
            if not row:
                return code
    finally:
        conn.close()


class ShortenerHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the URL shortening service."""

    def do_GET(self) -> None:
        """Handle GET requests: serve the form or redirect to the long URL."""
        # Normalize path without query parameters
        path = urllib.parse.urlparse(self.path).path
        if path == '/' or path == '/index.html':
            self._serve_home()
        else:
            code = path.lstrip('/')
            self._redirect_or_404(code)

    def do_POST(self) -> None:
        """Handle POST requests: create a shortened URL when posting to /shorten."""
        if self.path != '/shorten':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            return

        content_length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(body)
        long_url = params.get('long_url', [None])[0]

        if not long_url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid request')
            return

        code = generate_code()
        conn = sqlite3.connect(DB_FILE)
        with conn:
            conn.execute('INSERT INTO urls (code, long_url) VALUES (?, ?)', (code, long_url))
        conn.close()

        host = self.headers.get('Host') or f'localhost:{PORT}'
        short_url = f"http://{host}/{code}"

        # Respond with a HTML page containing the shortened link
        self.send_response(201)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        html = (
            "<html><head><title>URL Shortener</title></head>"
            "<body>"
            "<h1>Your shortened URL</h1>"
            f"<p>Original URL: {long_url}</p>"
            f"<p>Short URL: <a href='/{code}'>" + short_url + "</a></p>"
            "<p><a href='/'>Shorten another URL</a></p>"
            "</body></html>"
        )
        self.wfile.write(html.encode('utf-8'))

    def _serve_home(self) -> None:
        """Serve a simple form for inputting a long URL."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        html = (
            "<html>"
            "<head><title>URL Shortener</title></head>"
            "<body>"
            "<h1>URL Shortener</h1>"
            "<form method='post' action='/shorten'>"
            "<label for='long_url'>Enter URL:</label>"
            "<input type='url' id='long_url' name='long_url' size='60' required>"
            "<button type='submit'>Shorten</button>"
            "</form>"
            "</body>"
            "</html>"
        )
        self.wfile.write(html.encode('utf-8'))

    def _redirect_or_404(self, code: str) -> None:
        """Redirect to the long URL if found; otherwise return a 404 page."""
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute('SELECT long_url FROM urls WHERE code=?', (code,)).fetchone()
        conn.close()
        if row:
            long_url = row[0]
            self.send_response(302)
            self.send_header('Location', long_url)
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = (
                "<html>"
                "<head><title>Not Found</title></head>"
                "<body>"
                "<h1>404 Not Found</h1>"
                "<p>The shortened URL does not exist.</p>"
                "<p><a href='/'>Go back</a></p>"
                "</body></html>"
            )
            self.wfile.write(html.encode('utf-8'))

    def log_message(self, format: str, *args) -> None:
        """Override to suppress the default console logging for cleaner output."""
        return


PORT = 8000


def run_server(port: int = PORT) -> None:
    init_db()
    with socketserver.TCPServer(('', port), ShortenerHandler) as httpd:
        print(f"URL Shortener server running at http://localhost:{port} (Press Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server…")
            httpd.shutdown()


if __name__ == '__main__':
    run_server()

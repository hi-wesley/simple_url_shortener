# Simple URL Shortener

A simple URL shortening web application using Python's built‑in `http.server` and `sqlite3`.

-----

## Overview

This service generates a short, unique alias for any given long URL. When a user visits the short URL, they are redirected to the original long URL. Short URLs are generated using a random alphanumeric code to ensure they are not predictable.

-----

## Usage

To run the server, execute the following command in your terminal:

```bash
python3 url_shortener.py
```

The server will start listening on port `8000`. All URL mappings are persisted in a `urls.db` file created in the working directory.
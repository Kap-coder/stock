#!/usr/bin/env python3
"""
Small helper to download required vendor files into static/vendor/
Run from project root: python scripts/download_vendors.py
This script uses urllib to avoid extra deps.
"""
import os
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

VENDORS = [
    ('https://cdn.tailwindcss.com', 'static/vendor/tailwind.js'),
    ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css', 'static/vendor/fontawesome.min.css'),
    ('https://unpkg.com/htmx.org@1.9.10', 'static/vendor/htmx.min.js'),
    ('https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js', 'static/vendor/alpine.min.js'),
]


def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def download(url, dest):
    print(f'Downloading {url} → {dest}')
    ensure_dir(dest)
    req = Request(url, headers={'User-Agent': 'G-Business PWA downloader'})
    try:
        with urlopen(req, timeout=30) as r, open(dest, 'wb') as f:
            data = r.read()
            f.write(data)
        print('  OK')
    except HTTPError as e:
        print('  HTTP Error:', e.code, e.reason)
    except URLError as e:
        print('  URL Error:', e.reason)
    except Exception as e:
        print('  Error:', e)


if __name__ == '__main__':
    for url, dest in VENDORS:
        download(url, dest)
    print('\nDone. Verify files exist under static/vendor/ and then restart the dev server.')

#!/usr/bin/env python3
"""One-shot probe of gluebyte's documented Remote Sign endpoint.

The original Shortcut Source Helper sends gzipped .wflow as a POST body and
expects gzip-compressed signed AEA1 data. This probe uses HTTPS only and never
logs donor contents. No Apple credentials are provided.
"""
import gzip
import sys
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

URL = "https://shortcuts.gluebyte.workers.dev/"

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    raw = src.read_bytes()
    if len(raw) > 256_000:
        raise ValueError("Refusing to send unexpectedly large input.")
    request = Request(URL, data=gzip.compress(raw), method="POST",
                      headers={"Content-Type": "application/octet-stream",
                               "Accept": "application/octet-stream",
                               "User-Agent": "iOS-Shortcuts-Lab/0.1"})
    try:
        with urlopen(request, timeout=55) as response:
            body = response.read(4_000_000)
            print("HTTP status:",response.status)
            print("Final URL:",response.url)
            print("Response content type:",response.headers.get("Content-Type"))
            print("Response length:",len(body))
    except HTTPError as err:
        print("HTTP error code:",err.code)
        return 2
    except URLError as err:
        print("Network/TLS error:",type(err.reason).__name__)
        return 3
    try:
        payload = gzip.decompress(body)
    except (EOFError, OSError):
        print("Server returned non-gzip payload.")
        if len(body)<512 and body.decode("utf-8",errors="replace").isprintable():
            print("Remote Sign message:",body.decode("utf-8",errors="replace"))
        return 4
    if not payload.startswith(b"AEA1"):
        print("Decompressed response is not AEA1 signed shortcut.")
        return 5
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(payload)
    print("Success: valid AEA1 header returned by gluebyte Remote Sign.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

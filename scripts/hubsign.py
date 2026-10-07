#!/usr/bin/env python3
"""Official RoutineHub HubSign integration. Requires membership + HubSign key."""
import argparse
import os
import plistlib
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://routinehub.co/api/v1/sign-shortcut"

def sign(src: Path, dest: Path, display_name: str):
    key = os.environ.get("HUBSIGN_API_KEY", "")
    if not key:
        raise RuntimeError("HUBSIGN_API_KEY is not configured")
    workflow = src.read_bytes()
    if len(workflow) > 2_000_000 or not isinstance(plistlib.loads(workflow).get("WFWorkflowActions"), list):
        raise ValueError("invalid unsigned shortcut workflow")
    boundary = "ioslab-" + uuid.uuid4().hex
    def field(name: str, value: str) -> bytes:
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()
    body = (
        field("shortcut_name", display_name)
        + field("api_key", key)
        + f'--{boundary}\r\nContent-Disposition: form-data; name="shortcut_file"; filename="unsigned.shortcut"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
        + workflow + b"\r\n" + f"--{boundary}--\r\n".encode()
    )
    req = Request(API, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/octet-stream",
    })
    try:
        with urlopen(req, timeout=90) as response:
            signed = response.read(3_000_001)
    except HTTPError as err:
        # Deliberately do not log the response body: it could reflect credentials.
        raise RuntimeError(f"HubSign HTTP {err.code} (401 key, 402 membership, 403 access)") from None
    except URLError:
        raise RuntimeError("HubSign unavailable: network or TLS error") from None
    if len(signed) > 3_000_000 or not signed.startswith(b"AEA1"):
        raise ValueError("HubSign did not return signed AEA1 data")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(signed)
    print(f"Signed {display_name}: {len(signed)} bytes (AEA1)")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--name", required=True)
    a = p.parse_args()
    try:
        sign(a.input, a.output, a.name)
    except (OSError, RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)

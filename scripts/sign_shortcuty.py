#!/usr/bin/env python3
"""Sign one unsigned Apple Shortcut through Shortcuty's public, documented API.

API docs: https://github.com/Shortcuty/Signing-Server-API-Documentation
No account, API key, Apple ID, cookies, or special headers are required.
"""
from __future__ import annotations

import argparse
import hashlib
import plistlib
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SERVICE = "https://sign.shortcuty.app/api/v1/sign"
MAX_UPLOAD = 2_000_000
MAX_SIGNED = 4_000_000


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--upload-filename", required=True)
    args = p.parse_args()
    blob = args.input.read_bytes()
    if not blob or len(blob) > MAX_UPLOAD:
        raise ValueError("Missing or oversized unsigned workflow")
    workflow = plistlib.loads(blob)
    if not isinstance(workflow.get("WFWorkflowActions"), list):
        raise ValueError("Invalid workflow: WFWorkflowActions missing")
    filename = args.upload_filename
    if not filename.endswith(".shortcut") or "\r" in filename or "\n" in filename or '"' in filename:
        raise ValueError("Invalid upload filename")
    boundary = "----ShortcutyIOSShortcutsLab" + uuid.uuid4().hex
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        'Content-Type: application/octet-stream\r\n\r\n'
    ).encode("utf-8") + blob + f"\r\n--{boundary}--\r\n".encode("ascii")
    request = Request(
        SERVICE,
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/octet-stream",
            "User-Agent": "iOS-Shortcuts-Lab/1.0",
        },
    )
    try:
        with urlopen(request, timeout=75) as response:
            signed = response.read(MAX_SIGNED + 1)
            print("Shortcuty response status:", response.status)
    except HTTPError as error:
        raise RuntimeError(f"Shortcuty API HTTP {error.code} (422=invalid workflow, 503=signer unavailable)") from None
    except URLError as error:
        raise RuntimeError("Shortcuty API temporarily unavailable (network/TLS)") from None
    if not (20 < len(signed) <= MAX_SIGNED and signed[:4] == b"AEA1"):
        raise RuntimeError("Shortcuty did not return an AEA1-signed Shortcut")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(signed)
    print("SIGNED:", args.output.name)
    print("SOURCE_SHA256:", hashlib.sha256(blob).hexdigest())
    print("SIGNED_SHA256:", hashlib.sha256(signed).hexdigest())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, plistlib.InvalidFileException) as error:
        print("Signing failed:", error, file=sys.stderr)
        sys.exit(1)

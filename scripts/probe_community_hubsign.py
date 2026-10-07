#!/usr/bin/env python3
"""One-shot availability probe for the public HubSign endpoint used by Cherri.

This probes the same public service endpoint as the open-source Cherri compiler
without sending a RoutineHub account key, Apple credentials, or spoofed headers.
Intended only for a manually controlled one-time smoke test; no retries.
"""
from __future__ import annotations
import argparse
import json
import plistlib
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = "https://hubsign.routinehub.services/sign"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    raw = a.workflow.read_bytes()
    data = plistlib.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("WFWorkflowActions"), list):
        raise ValueError("invalid workflow plist")
    xml = plistlib.dumps(data, fmt=plistlib.FMT_XML).decode("utf-8")
    body = json.dumps({"shortcutName": "iOS Shortcuts Lab Signing Test", "shortcut": xml}).encode("utf-8")
    req = Request(ENDPOINT, data=body, headers={"Content-Type": "application/json",
                                                  "User-Agent": "cherri-shortcuts-lab-probe/1.0"}, method="POST")
    try:
        with urlopen(req, timeout=35) as resp:
            signed = resp.read(3_000_001)
            ctype = resp.headers.get("Content-Type", "")
            print("HTTP:", resp.status, "content-type:", ctype, "length:", len(signed))
    except HTTPError as e:
        print("HubSign HTTP", e.code)
        raise SystemExit(2)
    except URLError as e:
        print("HubSign network/TLS error:", type(e.reason).__name__)
        raise SystemExit(3)
    if not signed.startswith(b"AEA1"):
        print("Service did not return a signed AEA1 shortcut")
        raise SystemExit(4)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(signed)
    print("SUCCESS: authenticated-credential-free AEA1 signature returned.")

if __name__ == "__main__":
    main()

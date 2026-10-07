#!/usr/bin/env python3
"""Extract a signed Apple Shortcut (AEA1) into its underlying Shortcut.wflow.

Requires macOS's stock 'aea' and 'aa' commands; only accepts sign-only
profile 0 containers. Does not modify the original signed shortcut.
"""
from __future__ import annotations

import argparse
import plistlib
import subprocess
import sys
from pathlib import Path


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def extract(source: Path, output_dir: Path) -> Path:
    data = source.read_bytes()
    if len(data) < 12 or data[:4] != b"AEA1":
        raise ValueError("expected AEA1 signed shortcut")
    profile = int.from_bytes(data[4:8], "little")
    auth_size = int.from_bytes(data[8:12], "little")
    if profile != 0 or 12 + auth_size >= len(data):
        raise ValueError("unsupported AEA profile or invalid header")
    auth = plistlib.loads(data[12 : 12 + auth_size])
    chain = auth["SigningCertificateChain"]
    if not chain:
        raise ValueError("missing signing certificate")
    output_dir.mkdir(parents=True, exist_ok=True)
    certificate = output_dir / "cert.der"
    certificate.write_bytes(chain[0])
    key_der = output_dir / "pub.der"
    with key_der.open("wb") as handle:
        subprocess.run(
            ["openssl", "x509", "-inform", "DER", "-in", str(certificate), "-pubkey", "-noout"],
            check=True,
            stdout=(output_dir / "pub.pem").open("wb"),
        )
    with key_der.open("wb") as handle:
        subprocess.run(
            ["openssl", "pkey", "-pubin", "-in", str(output_dir / "pub.pem"), "-outform", "DER"],
            check=True,
            stdout=handle,
        )
    pub_x963 = key_der.read_bytes()[-65:]
    if len(pub_x963) != 65 or pub_x963[0] != 4:
        raise ValueError("expected uncompressed P-256 EC public key")
    pubfile = output_dir / "sign.pub"
    pubfile.write_text("hex:" + pub_x963.hex())
    apple_archive = output_dir / "payload.aa"
    run("aea", "decrypt", "-sign-pub", str(pubfile),
        "-i", str(source), "-o", str(apple_archive))
    extracted = output_dir / "extracted"
    extracted.mkdir(exist_ok=True)
    run("aa", "extract", "-i", str(apple_archive), "-d", str(extracted))
    matches = list(extracted.rglob("*.wflow"))
    if len(matches) != 1:
        raise ValueError(f"expected 1 *.wflow; found {len(matches)}")
    result = output_dir / "Shortcut.wflow"
    result.write_bytes(matches[0].read_bytes())
    # Verify the payload looks like a genuine Shortcuts workflow.
    workflow = plistlib.loads(result.read_bytes())
    if not isinstance(workflow.get("WFWorkflowActions"), list):
        raise ValueError("workflow lacks WFWorkflowActions")
    print(f"Extracted {source.name}: {len(workflow['WFWorkflowActions'])} actions")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    arguments = parser.parse_args()
    try:
        extract(arguments.source, arguments.output_dir)
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError) as error:
        print(f"Extraction failed: {error}", file=sys.stderr)
        raise SystemExit(1)

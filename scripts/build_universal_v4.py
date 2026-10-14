#!/usr/bin/env python3
"""Experimental Universal v4: preserve the successfully tested native iOS
audio extraction, but block FFmpeg from selecting the original USAC/xHE-AAC
track. All changes are isolated from the working production shortcuts.

Confirmed by user: iOS 17.3.1 produces a ~124 s AIFF from the xHE-AAC clip.
Confirmed locally: FFmpeg 7.1.5 remuxes that real H.264 clip without re-encoding
the video, when the original input audio is disabled and AIFF supplied as the
only selected audio source. Phone's a-Shell build still needs testing.
"""
from __future__ import annotations

import argparse
import importlib.util
import plistlib
from pathlib import Path

NAME = "⚡ Speed Video Universal v4"
INPUT = "__svuv4_entrada"
AUDIO = "__svuv4_audio.aiff"
OUTPUT = "__svuv4.mp4"
V3 = Path(__file__).with_name("build_universal_v3.py")

def main() -> None:
    arg = argparse.ArgumentParser()
    arg.add_argument("--donor", type=Path, required=True)
    arg.add_argument("--output", type=Path, required=True)
    args=arg.parse_args()

    spec=importlib.util.spec_from_file_location("v3",V3)
    m=importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(m)
    m.NAME=NAME
    m.INPUT=INPUT
    m.AUDIO=AUDIO
    m.OUTPUT=OUTPUT
    import sys
    old_argv=sys.argv
    try:
        sys.argv=[str(V3),"--donor",str(args.donor),"--output",str(args.output)]
        m.main()
    finally:
        sys.argv=old_argv

    shortcut=plistlib.loads(args.output.read_bytes())
    actions=shortcut["WFWorkflowActions"]
    commands=[]
    for a in actions:
        p=a.get("WFWorkflowActionParameters",{})
        cmd=p.get("command","")
        if "ffmpeg " not in cmd:
            continue
        assert f'-i "{INPUT}" -i "{AUDIO}"' in cmd, cmd
        # Demux movie as VIDEO ONLY. A 32-byte probe and no stream analysis
        # minimize the chance that the problematic original xHE-AAC bitstream
        # reaches the bundled FFmpeg decoder before stream mapping is applied.
        # The normal AIFF input is kept untouched.
        new_input=(f'-analyzeduration 0 -probesize 32 -an -i "{INPUT}" '
                   f'-i "{AUDIO}"')
        p["command"]=cmd.replace(f'-i "{INPUT}" -i "{AUDIO}"',new_input)
        assert p["command"]!=cmd
        assert '-map 0:v:0 -map 1:a:0 -c:v copy' in p["command"]
        assert 'atempo=' in p["command"]
        commands.append(p["command"])

    assert len(commands)==5, f"expected 5 speed options, got {len(commands)}"
    media=next(a["WFWorkflowActionParameters"] for a in actions
               if a["WFWorkflowActionIdentifier"]=="is.workflow.actions.encodemedia")
    assert media["WFMedia"]["Value"]["Type"]=="ExtensionInput"
    assert media["WFMediaAudioOnly"] is True
    assert media["WFMediaAudioFormat"]=="AIFF"
    assert len(actions)==24
    args.output.write_bytes(plistlib.dumps(shortcut,fmt=plistlib.FMT_BINARY,sort_keys=False))
    print("PASS: v4 copies video without source audio, 5 choices, known-good native WFMedia.")
    print("No change to production Voice → Status or Speed Video.")

if __name__=="__main__":
    main()

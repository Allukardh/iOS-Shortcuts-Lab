#!/usr/bin/env python3
"""Experimental Universal v3: run native audio decoding BEFORE any a-Shell intent.

The prior v1/v2 versions put native Encode Media AFTER a-Shell's PutFileIntent
and used an unverified implicit or localized output reference. Both returned
no AIFF even for standard camera videos. This version:
 - resolves the video via the original trusted ExtensionInput token;
 - runs native Encode Media FIRST, with a predictable CustomOutputName;
 - explicitly connects native result -> Rename -> a-Shell Put File;
 - then uploads the video via the donor's proven original Rename -> Put File;
 - uses the tested ffmpeg + FINALIZAR shell callback.
The original published shortcuts and previous Universal variants are untouched.
"""
from __future__ import annotations
import argparse
import importlib.util
import plistlib
from pathlib import Path

NAME = "⚡ Speed Video Universal v3"
INPUT = "__svuv3_entrada"
AUDIO = "__svuv3_audio.aiff"
OUTPUT = "__svuv3.mp4"


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--donor", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args=p.parse_args()

    module_path=Path(__file__).with_name("build_speed_universal.py")
    spec=importlib.util.spec_from_file_location("speed_universal",module_path)
    m=importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(m)

    m.APP=NAME
    m.INPUT=INPUT
    m.AUDIO=AUDIO
    m.OUTPUT=OUTPUT

    donor=plistlib.loads(args.donor.read_bytes())
    result=m.create(donor)
    actions=result["WFWorkflowActions"]
    assert len(actions)==24

    # Generated v2 flow: 0:7 callback/conditional; 7:9 video transfer;
    # 9:12 native audio conversion/transfer; 12+: menu and speed branches.
    original_pre=actions[:7]
    video_transfer=actions[7:9]
    audio_transfer=actions[9:12]
    speed_menu=actions[12:]
    assert audio_transfer[0]["WFWorkflowActionIdentifier"]=="is.workflow.actions.encodemedia"
    assert audio_transfer[1]["WFWorkflowActionIdentifier"]=="is.workflow.actions.setitemname"
    assert audio_transfer[2]["WFWorkflowActionIdentifier"]=="AsheKube.app.a-Shell-mini.PutFileIntent"
    assert video_transfer[0]["WFWorkflowActionIdentifier"]=="is.workflow.actions.setitemname"
    assert video_transfer[1]["WFWorkflowActionIdentifier"]=="AsheKube.app.a-Shell-mini.PutFileIntent"

    native=audio_transfer[0]["WFWorkflowActionParameters"]
    native["CustomOutputName"]="Converted Audio"
    # ShareSheet token is the same proven token used by original
    # Set Item Name. No a-Shell context switch occurs beforehand.
    assert native["WFInput"]==donor["WFWorkflowActions"][7]["WFWorkflowActionParameters"]["WFInput"]
    # Explicit magic variable: Never rely on implicit previous action input.
    # CustomOutputName mirrors OutputName to keep binding deterministic.
    named=audio_transfer[1]["WFWorkflowActionParameters"]
    named["WFInput"]=m.output_ref(native["UUID"],"Converted Audio")
    put=audio_transfer[2]["WFWorkflowActionParameters"]
    put["overwrite"]=True
    # Original donor file transfer is kept unchanged except versioned name.
    video_transfer[1]["WFWorkflowActionParameters"]["overwrite"]=True

    result["WFWorkflowActions"]=original_pre+audio_transfer+video_transfer+speed_menu
    assert len(result["WFWorkflowActions"])==24
    assert [a["WFWorkflowActionIdentifier"] for a in result["WFWorkflowActions"][7:12]] == [
        "is.workflow.actions.encodemedia",
        "is.workflow.actions.setitemname",
        "AsheKube.app.a-Shell-mini.PutFileIntent",
        "is.workflow.actions.setitemname",
        "AsheKube.app.a-Shell-mini.PutFileIntent"
    ]
    assert len([a for a in result["WFWorkflowActions"] if a["WFWorkflowActionIdentifier"]=="AsheKube.app.a-Shell-mini.ExecuteCommandIntent"])==6
    assert result["WFWorkflowMinimumClientVersion"]==donor["WFWorkflowMinimumClientVersion"]
    assert result["WFWorkflowInputContentItemClasses"]==donor["WFWorkflowInputContentItemClasses"]
    raw=plistlib.dumps(result,fmt=plistlib.FMT_BINARY,sort_keys=False)
    assert plistlib.loads(raw)==result
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(raw)
    print(f"Built {NAME}: {len(result['WFWorkflowActions'])} actions, native audio decoding BEFORE a-Shell")
    print("Explicit CustomOutputName: Converted Audio; Rename input references native encoder UUID")
    print("Preserved original input/callback, protected original published releases")


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Temporary iOS 17.3.1 diagnostic, never changes released shortcuts.

Show native Encode Media output in Quick Look before attempting to copy it
to a-Shell. If the preview appears and audio plays, native extraction works.
If the subsequent shell still lacks AIFF, the transfer/references are wrong.
"""
import argparse
import importlib.util
import plistlib
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--donor",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location("speed_universal",Path(__file__).with_name("build_speed_universal.py"))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.APP = "⚡ Speed Video Audio Test"
    m.INPUT = "__audiotest_entrada"
    m.AUDIO = "__audiotest_audio.aiff"
    m.OUTPUT = "__audiotest_saida.mp4"
    donor=plistlib.loads(a.donor.read_bytes())
    workflow=m.create(donor)
    actions=workflow["WFWorkflowActions"]
    idx=next(i for i,x in enumerate(actions) if x["WFWorkflowActionIdentifier"]=="is.workflow.actions.encodemedia")
    codec=actions[idx]
    codec_uuid=codec["WFWorkflowActionParameters"]["UUID"]
    look=m.action("is.workflow.actions.previewdocument",{
      "WFInput":m.output_ref(codec_uuid,"Encoded Media"),
      "UUID":m.uid()
    })
    actions.insert(idx+1,look)
    assert len(actions)==25
    assert actions[idx+1]["WFWorkflowActionIdentifier"]=="is.workflow.actions.previewdocument"
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(plistlib.dumps(workflow,fmt=plistlib.FMT_BINARY,sort_keys=False))
    print("Signed diagnostic source ready: native Encode Media -> Quick Look -> Put File -> existing FFmpeg pipeline")
    print("25 actions; interactive audio preview is expected before speed menu.")
if __name__=="__main__":main()

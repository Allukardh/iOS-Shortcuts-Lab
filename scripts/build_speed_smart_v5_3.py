#!/usr/bin/env python3
"""Speed Video Smart v5.3: one foreground a-Shell launch (experimental).

Based on the physically functioning Smart v5.2 iOS if-then branch graph,
with ffprobe moved into a-Shell's Intent Extension (openWindow=close).
a-Shell's upstream Swift ExecuteCommandIntentHandler explicitly says the
extension runs fast commands directly through ios_system in the shared app
group and returns to Shortcuts without opening the UI.  The ffprobe command
is a short read-only profile scan: it must fit the extension's ~5s limit.

After native GetFile -> Get Text -> If, only the chosen *conversion* path
launches a-Shell: direct FFmpeg for AAC-LC, native iOS audio-first + FFmpeg
for other profiles. No shell if/fi, OR chains, or repeated self-callbacks.
The proven legacy shortcuts are untouched.
"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import plistlib
from pathlib import Path

BASE=Path(__file__).with_name("build_speed_smart_v5_2.py")
NAME="⚡ Speed Video Smart v5.3"

def load_base():
    spec=importlib.util.spec_from_file_location("smart_v52",BASE)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.NAME=NAME
    return m

def build(donor:dict, ios:dict)->dict:
    m=load_base()
    base=donor["WFWorkflowActions"]
    assert len(base)==15
    encoder=next(x for x in ios["WFWorkflowActions"]
                 if x["WFWorkflowActionIdentifier"]=="is.workflow.actions.encodemedia")
    assert encoder["WFWorkflowActionParameters"]["WFMedia"]["Value"]["Type"]=="ExtensionInput"
    assert base[1]["WFWorkflowActionIdentifier"]==m.GET
    assert base[7]["WFWorkflowActionIdentifier"]=="is.workflow.actions.setitemname"
    assert base[8]["WFWorkflowActionIdentifier"]==m.PUT
    assert base[11]["WFWorkflowActionIdentifier"]==m.EXEC
    result=copy.deepcopy(donor)

    # Preserve physically validated success callback: Get MP4 -> Save Photos ->
    # remove temporary files -> Stop Shortcut.
    steps=copy.deepcopy(base[:7])
    steps[1]["WFWorkflowActionParameters"]["fileName"]=m.OUTPUT
    steps[3]["WFWorkflowActionParameters"]["command"]=(f'rm -f "{m.SOURCE}" '
                                                      f'"{m.REPORT}" "{m.AUDIO}" "{m.OUTPUT}"')

    # Save source into a-Shell's shared directory once (not an app launch).
    putname=copy.deepcopy(base[7])
    putname["WFWorkflowActionParameters"].update(WFName=m.SOURCE,WFDontIncludeFileExtension=False)
    put=copy.deepcopy(base[8])
    put["WFWorkflowActionParameters"]["overwrite"]=True
    steps.extend((putname,put))

    menu=copy.deepcopy(base[9])
    menu["WFWorkflowActionParameters"]["WFMenuItems"]=[x+"×" for x in m.SPEEDS]
    steps.append(menu)

    for speed in m.SPEEDS:
        option=copy.deepcopy(base[10])
        option["WFWorkflowActionParameters"]["WFMenuItemTitle"]=speed+"×"
        steps.append(option)

        # The critical change from v5.2: force the lightweight command into
        # the a-Shell mini Intent Extension. The Swift handler's .close mode
        # explicitly avoids launching the app, even though ffprobe is not
        # listed among its auto-selected "localCommands".
        # No sh -c, no open callback, just plain ffprobe output to a text file.
        preflight=(f'ffprobe -v error -select_streams a:0 '
                   f'-show_entries stream=codec_name,profile '
                   f'-of default=noprint_wrappers=1 "{m.SOURCE}" > "{m.REPORT}"')
        check=copy.deepcopy(base[11])
        check["WFWorkflowActionParameters"].update(
            command=preflight,
            openWindow="close",
            ShowWhenRun=False,
            UUID=m.uid(),
            keepGoing=False,
        )
        steps.append(check)

        report=copy.deepcopy(base[1])
        report_id=m.uid()
        report["WFWorkflowActionParameters"].update(fileName=m.REPORT,UUID=report_id)
        steps.append(report)

        text_id=m.uid()
        extract=m.a("is.workflow.actions.detect.text",{
            "WFInput":m.reference(report_id,"Arquivo"),
            "UUID":text_id
        })
        steps.append(extract)

        condition,group=m.if_action(m.reference(text_id,"Text"),contains="profile=LC")
        steps.append(condition)
        steps.append(m.execution(m.direct(speed),base[11]))

        steps.append(m.marker(group,1))
        # Unlike v5.2, no Get original video from a-Shell is required. The
        # Share Sheet ExtensionInput still exists in the same Shortcut run;
        # use the real iOS-exported native parameter from the validated v4.
        enc=copy.deepcopy(encoder)
        p=enc["WFWorkflowActionParameters"]
        enc_id=m.uid()
        p["UUID"]=enc_id
        p["WFMedia"]=copy.deepcopy(base[7]["WFWorkflowActionParameters"]["WFInput"])
        p["WFInput"]=copy.deepcopy(p["WFMedia"])
        p.update(CustomOutputName="Converted Audio",WFMediaAudioOnly=True,
                 WFMediaAudioFormat="AIFF",WFMediaSpeed="Normal",Metadata=False)
        assert p["WFMedia"]["Value"]["Type"]=="ExtensionInput"
        steps.append(enc)

        name_id=m.uid()
        rename=m.a("is.workflow.actions.setitemname",{
            "WFName":m.AUDIO,
            "WFInput":m.reference(enc_id,"Converted Audio"),
            "WFDontIncludeFileExtension":False,"UUID":name_id,
        })
        steps.append(rename)
        upload=copy.deepcopy(base[8])
        upload["WFWorkflowActionParameters"].update(
            file=m.reference(name_id,"Item Renomeado"),overwrite=True,UUID=m.uid()
        )
        steps.append(upload)
        steps.append(m.execution(m.universal(speed),base[11]))
        steps.append(m.marker(group,2))

    steps.append(copy.deepcopy(base[14]))
    result["WFWorkflowActions"]=steps
    # Guard against silent workflow creation regressions.
    cond_open=[x["WFWorkflowActionParameters"]["GroupingIdentifier"] for x in steps
               if x["WFWorkflowActionIdentifier"]==m.COND
               and x["WFWorkflowActionParameters"].get("WFControlFlowMode")==0]
    cond_close=[x["WFWorkflowActionParameters"]["GroupingIdentifier"] for x in steps
                if x["WFWorkflowActionIdentifier"]==m.COND
                and x["WFWorkflowActionParameters"].get("WFControlFlowMode")==2]
    assert sorted(cond_open)==sorted(cond_close) and len(cond_open)==6
    total_probes=[x for x in steps if x["WFWorkflowActionIdentifier"]==m.EXEC
                  and "ffprobe " in x["WFWorkflowActionParameters"].get("command","")]
    assert len(total_probes)==5
    assert all(x["WFWorkflowActionParameters"]["openWindow"]=="close" for x in total_probes)
    assert all("open \"shortcuts:" not in x["WFWorkflowActionParameters"]["command"] for x in total_probes)
    assert all(not x["WFWorkflowActionParameters"]["command"].startswith("sh -c") for x in total_probes)
    ffmpeg=[x for x in steps if x["WFWorkflowActionIdentifier"]==m.EXEC
            and "ffmpeg " in x["WFWorkflowActionParameters"].get("command","")]
    assert len(ffmpeg)==10
    assert all(x["WFWorkflowActionParameters"]["openWindow"]=="open" for x in ffmpeg)
    assert not any("if ffmpeg" in x["WFWorkflowActionParameters"]["command"] or " || " in x["WFWorkflowActionParameters"]["command"] for x in steps if x["WFWorkflowActionIdentifier"]==m.EXEC)
    assert len([x for x in steps if x["WFWorkflowActionIdentifier"]=="is.workflow.actions.encodemedia"])==5
    assert result["WFWorkflowMinimumClientVersion"]==donor["WFWorkflowMinimumClientVersion"]
    ids=[x["WFWorkflowActionParameters"].get("UUID") for x in steps]
    ids=[i for i in ids if i]
    assert len(ids)==len(set(ids))
    assert len(steps)==71, len(steps)
    print(f"PASS: {len(steps)} actions, five foreground-free ffprobe preflights, five direct & five native fallback FFmpeg jobs.")
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--donor",required=True,type=Path)
    ap.add_argument("--ios-ref",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    p=build(plistlib.loads(args.donor.read_bytes()),plistlib.loads(args.ios_ref.read_bytes()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(plistlib.dumps(p,fmt=plistlib.FMT_BINARY,sort_keys=False))

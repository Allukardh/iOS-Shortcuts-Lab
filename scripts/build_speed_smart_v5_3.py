#!/usr/bin/env python3
"""Smart v5.3: one visible a-Shell visit via a forced offscreen ffprobe preflight.

This is a precise, separately named experiment based on the proven v5.2
logic. Do not replace stable v4 / v5.2 until on-device verification.

a-Shell mini's ExecuteCommandIntentHandler.swift: intent.openWindow == .close
runs executeCommandInExtension in shared app-group directory. Unlike 'auto',
forcing 'close' bypasses the localCommands whitelist (which excludes ffprobe).
However, successful execution of the ffprobe binary and extension runtime
limits STILL require a physical iOS 17.3.1 test.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import plistlib
from pathlib import Path

NAME = "⚡ Speed Video Smart v5.3"


def construct(donor, ios):
    module_path = Path(__file__).with_name("build_speed_smart_v5_2.py")
    spec=importlib.util.spec_from_file_location("v52",module_path)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.NAME=NAME
    original=m.build(donor,ios)
    actions=original["WFWorkflowActions"]
    src=donor["WFWorkflowActions"]
    assert len(actions)==96, f"Unexpected original action count: {len(actions)}"
    assert len(src)==15

    # Original v5.2 sections: 7 FINALIZAR actions; 5 complete 15-action
    # PROBE callback handlers; 2 source upload; 1 menu head;
    # 5x menu item + ffprobe/open callback; final menu close.
    callback=copy.deepcopy(actions[:7])
    blocks=[copy.deepcopy(actions[7+15*i:7+15*(i+1)]) for i in range(5)]
    shared_input=copy.deepcopy(actions[82:84])
    menu_start=copy.deepcopy(actions[84])
    menu_end=copy.deepcopy(actions[95])
    assert all(len(b)==15 for b in blocks)
    assert actions[82]["WFWorkflowActionIdentifier"]=="is.workflow.actions.setitemname"
    assert actions[83]["WFWorkflowActionIdentifier"]==m.PUT
    assert menu_start["WFWorkflowActionIdentifier"]=="is.workflow.actions.choosefrommenu"
    assert menu_end["WFWorkflowActionIdentifier"]=="is.workflow.actions.choosefrommenu"
    assert menu_end["WFWorkflowActionParameters"]["WFControlFlowMode"]==2

    res=callback+shared_input+[menu_start]

    for i,rate in enumerate(m.SPEEDS):
        block=blocks[i]
        identifiers=[b["WFWorkflowActionIdentifier"] for b in block]
        expected=[m.COND,m.GET,"is.workflow.actions.detect.text",m.COND,
                  m.EXEC,m.COND,m.GET,"is.workflow.actions.encodemedia",
                  "is.workflow.actions.setitemname",m.PUT,m.EXEC,m.COND,
                  "is.workflow.actions.stop",m.COND,m.COND]
        assert identifiers==expected, (rate,identifiers)
        # Use already verified v5.2 branch graph, but move it directly
        # underneath the matching menu option. Remove PROBE_x callback
        # wrapper: a-Shell will NOT open the app to call that shortcut again.
        # Execute probe in extension, then native Get File -> Text -> If.
        item=copy.deepcopy(actions[85+2*i])
        assert item["WFWorkflowActionIdentifier"]=="is.workflow.actions.choosefrommenu"
        assert item["WFWorkflowActionParameters"]["WFMenuItemTitle"]==rate+"×"

        preflight=copy.deepcopy(actions[86+2*i])
        assert preflight["WFWorkflowActionIdentifier"]==m.EXEC
        p=preflight["WFWorkflowActionParameters"]
        command=f'ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,profile -of default=noprint_wrappers=1 "{m.SOURCE}" > "{m.REPORT}"'
        # IMPORTANT: no "sh -c", no shell 'if', no callback URL. In extension
        # ios_system executes the simple command and redirects its output.
        p["command"]=command
        p["openWindow"]="close"   # a-Shell documented .close = in-extension
        p["ShowWhenRun"]=False
        p["keepGoing"]=False

        core=[copy.deepcopy(a) for a in block[1:12]]
        # core: get-report, detect-text, if, direct exec, else,
        # get-movie, encode-media, rename, put, universal exec, end-if
        assert len(core)==11
        cond=core[2]["WFWorkflowActionParameters"]
        assert cond["WFCondition"]==99 and cond["WFConditionalActionString"]=="profile=LC"
        enc=core[6]["WFWorkflowActionParameters"]
        assert enc["WFMediaAudioOnly"] is True and enc["WFMediaAudioFormat"]=="AIFF"
        assert enc["WFMedia"]["Value"]["Type"]=="ActionOutput"
        direct=core[3]["WFWorkflowActionParameters"]["command"]
        safe=core[9]["WFWorkflowActionParameters"]["command"]
        for c in (direct,safe):
            assert f'atempo={rate}' in c and "&& open " in c
            assert NAME.replace(" ","%20") in c
        res.extend([item,preflight,*core])

    res.append(menu_end)
    original["WFWorkflowActions"]=res

    assert len(res)==76,len(res)
    assert len([a for a in res if a["WFWorkflowActionIdentifier"]==m.EXEC
                and "ffprobe " in a["WFWorkflowActionParameters"].get("command","")])==5
    probe_actions=[a for a in res if a["WFWorkflowActionIdentifier"]==m.EXEC
                   and "ffprobe " in a["WFWorkflowActionParameters"].get("command","")]
    assert all(a["WFWorkflowActionParameters"]["openWindow"]=="close" for a in probe_actions)
    assert all("open " not in a["WFWorkflowActionParameters"]["command"] for a in probe_actions)
    assert len([a for a in res if a["WFWorkflowActionIdentifier"]==m.EXEC and
                "ffmpeg " in a["WFWorkflowActionParameters"].get("command","")])==10
    groups_open=[a["WFWorkflowActionParameters"]["GroupingIdentifier"] for a in res
                 if a["WFWorkflowActionIdentifier"]==m.COND and
                 a["WFWorkflowActionParameters"]["WFControlFlowMode"]==0]
    groups_close=[a["WFWorkflowActionParameters"]["GroupingIdentifier"] for a in res
                  if a["WFWorkflowActionIdentifier"]==m.COND and
                  a["WFWorkflowActionParameters"]["WFControlFlowMode"]==2]
    assert sorted(groups_open)==sorted(groups_close) and len(groups_open)==6
    ids=[a.get("WFWorkflowActionParameters",{}).get("UUID") for a in res]
    ids=[x for x in ids if x]
    assert len(ids)==len(set(ids))
    assert original["WFWorkflowMinimumClientVersion"]==donor["WFWorkflowMinimumClientVersion"]
    print("PASS: 76 actions, 5 offscreen extension probes, five fast and five iOS audio branches")
    return original


def main():
    args=argparse.ArgumentParser()
    args.add_argument("--donor",type=Path,required=True)
    args.add_argument("--ios-ref",type=Path,required=True)
    args.add_argument("--output",type=Path,required=True)
    a=args.parse_args()
    result=construct(plistlib.loads(a.donor.read_bytes()),plistlib.loads(a.ios_ref.read_bytes()))
    data=plistlib.dumps(result,fmt=plistlib.FMT_BINARY,sort_keys=False)
    assert plistlib.loads(data)==result
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(data)
    print("Generated",a.output,len(data),"bytes")

if __name__=="__main__":main()

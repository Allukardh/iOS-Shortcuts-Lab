#!/usr/bin/env python3
"""Smart v5.2 -- NO a-Shell shell conditionals.

An explicit ffprobe preflight determines whether a video's audio has the
known-good AAC-LC profile. The Shortcut itself handles branch selection.
a-Shell only runs proven single pipelines joined with && open callbacks.

iOS 17.3.1. Keep the validated Universal v4 and original Speed unchanged.
"""
from __future__ import annotations
import argparse, copy, plistlib, uuid
from pathlib import Path
from urllib.parse import quote

NAME="⚡ Speed Video Smart v5.2"
SOURCE="__smart_source.mp4"
REPORT="__smart_profile.txt"
AUDIO="__smart_audio.aiff"
OUTPUT="__smart_result.mp4"
SPEEDS=("1.1","1.2","1.3","1.4","1.5")
GET="AsheKube.app.a-Shell-mini.GetFileIntent"
PUT="AsheKube.app.a-Shell-mini.PutFileIntent"
EXEC="AsheKube.app.a-Shell-mini.ExecuteCommandIntent"
COND="is.workflow.actions.conditional"

def uid(): return str(uuid.uuid4()).upper()

def reference(action_uuid,name,media=False):
    v={"Type":"ActionOutput","OutputUUID":action_uuid,"OutputName":name}
    if media: v["Aggrandizements"]=[{"Type":"WFCoercionVariableAggrandizement","CoercionItemClass":"WFAVAssetContentItem"}]
    return {"Value":v,"WFSerializationType":"WFTextTokenAttachment"}

def a(ident,params): return {"WFWorkflowActionIdentifier":ident,"WFWorkflowActionParameters":params}

def callback(ev):
    return "shortcuts://run-shortcut?name="+quote(NAME,safe="")+"&input=text&text="+quote(ev,safe="")

def execution(cmd,template):
    assert "'" not in cmd
    out=copy.deepcopy(template); p=out["WFWorkflowActionParameters"]
    p.update(command="sh -c '"+cmd+"'",UUID=uid(),openWindow="open",ShowWhenRun=False)
    return out

def direct(speed):
    # Same structure as the reliable production Speed Video.
    return " ".join((
        "ffmpeg -hide_banner -loglevel info -stats -y",
        f'-i "{SOURCE}" -map 0:v:0 -map 0:a:0? -c:v copy',
        f'-bsf:v "setts=pts=PTS/{speed}:dts=DTS/{speed}:duration=DURATION/{speed}"',
        f'-af "atempo={speed}" -c:a aac -b:a 192k',
        f'-movflags +faststart "{OUTPUT}" && open "{callback("FINALIZAR")}"'
    ))

def universal(speed):
    # EXACT Universal v4 input recipe that was user-verified on xHE-AAC.
    return " ".join((
        f'ls -lh "{SOURCE}" "{AUDIO}" &&',
        'ffmpeg -hide_banner -loglevel info -stats -y',
        f'-analyzeduration 0 -probesize 32 -an -i "{SOURCE}" -i "{AUDIO}"',
        '-map 0:v:0 -map 1:a:0 -c:v copy',
        f'-bsf:v "setts=pts=PTS/{speed}:dts=DTS/{speed}:duration=DURATION/{speed}"',
        f'-af "atempo={speed}" -c:a aac -b:a 192k',
        f'-movflags +faststart "{OUTPUT}" && open "{callback("FINALIZAR")}"'
    ))

def probe(speed):
    # ios_system handles IO redirection and '&&' but not if/then/else.
    # The native Shortcuts engine will read REPORT and choose the branch.
    return ("ffprobe -v error -select_streams a:0 "
            "-show_entries stream=codec_name,profile "
            f'-of default=noprint_wrappers=1 "{SOURCE}" > "{REPORT}" '
            f'&& open "{callback("PROBE_"+speed)}"')

def if_action(operand,contains=None,string=None):
    group=uid()
    p={"WFInput":{"Type":"Variable","Variable":copy.deepcopy(operand)},
       "WFControlFlowMode":0,"GroupingIdentifier":group,"UUID":uid(),
       "WFCondition":99 if contains is not None else 4,
       "WFConditionalActionString":contains if contains is not None else string}
    return a(COND,p),group

def marker(group,mode):
    return a(COND,{"GroupingIdentifier":group,"WFControlFlowMode":mode,"UUID":uid()})

def build(donor,ios):
    src=donor["WFWorkflowActions"]
    assert len(src)==15
    encoder=next(x for x in ios["WFWorkflowActions"] if x["WFWorkflowActionIdentifier"]=="is.workflow.actions.encodemedia")
    assert encoder["WFWorkflowActionParameters"]["WFMedia"]["Value"]["Type"]=="ExtensionInput"
    assert src[1]["WFWorkflowActionIdentifier"]==GET
    assert src[8]["WFWorkflowActionIdentifier"]==PUT
    assert src[11]["WFWorkflowActionIdentifier"]==EXEC
    out=copy.deepcopy(donor)
    steps=copy.deepcopy(src[:7])
    steps[1]["WFWorkflowActionParameters"]["fileName"]=OUTPUT
    steps[3]["WFWorkflowActionParameters"]["command"]=f'rm -f "{SOURCE}" "{REPORT}" "{AUDIO}" "{OUTPUT}"'

    for speed in SPEEDS:
        # Probe callback -- request text report from the a-Shell shared folder.
        gate=copy.deepcopy(src[0]);grp=uid()
        pg=gate["WFWorkflowActionParameters"]
        pg["WFConditionalActionString"]="PROBE_"+speed
        pg["GroupingIdentifier"]=grp
        qget=copy.deepcopy(src[1]); qgetid=uid()
        qget["WFWorkflowActionParameters"].update(fileName=REPORT,UUID=qgetid)
        # Get Text from Input: Apple built-in coercion action for text files.
        # It reads the file contents, not just the name.
        txtid=uid()
        gettext=a("is.workflow.actions.detect.text",{
            "WFInput":reference(qgetid,"Arquivo"),
            "UUID":txtid})
        # The native If action decides; a-Shell executes no conditionals.
        condition,cgroup=if_action(reference(txtid,"Text"),contains="profile=LC")
        steps.extend((gate,qget,gettext,condition,execution(direct(speed),src[11]),marker(cgroup,1)))

        # Conservative path for xHE-AAC, HE-AAC, OPUS etc. Pull original movie
        # from a-Shell and let native iOS 17.3.1 decode audio to AIFF.
        movie=copy.deepcopy(src[1]); mid=uid()
        movie["WFWorkflowActionParameters"].update(fileName=SOURCE,UUID=mid)
        convert=copy.deepcopy(encoder);cp=convert["WFWorkflowActionParameters"]
        encid=uid();cp["UUID"]=encid
        cp["WFMedia"]=reference(mid,"Arquivo",media=True)
        cp["WFInput"]=copy.deepcopy(cp["WFMedia"])
        cp.update(CustomOutputName="Converted Audio",WFMediaAudioOnly=True,
                  WFMediaAudioFormat="AIFF",WFMediaSpeed="Normal",Metadata=False)
        renamed=uid()
        rename=a("is.workflow.actions.setitemname",{
            "WFName":AUDIO,"WFInput":reference(encid,"Converted Audio"),
            "WFDontIncludeFileExtension":False,"UUID":renamed})
        put=copy.deepcopy(src[8])
        put["WFWorkflowActionParameters"].update(file=reference(renamed,"Item Renomeado"),UUID=uid(),overwrite=True)
        steps.extend((movie,convert,rename,put,execution(universal(speed),src[11]),
                      marker(cgroup,2),copy.deepcopy(src[4]),marker(grp,1)))
        close=copy.deepcopy(src[6])
        close["WFWorkflowActionParameters"].update(GroupingIdentifier=grp,UUID=uid())
        steps.append(close)

    # Initial Share Sheet transaction copies the video exactly once.
    origrename=copy.deepcopy(src[7])
    origrename["WFWorkflowActionParameters"].update(WFName=SOURCE,WFDontIncludeFileExtension=False)
    origput=copy.deepcopy(src[8])
    origput["WFWorkflowActionParameters"].update(overwrite=True)
    steps.extend((origrename,origput))
    menu=copy.deepcopy(src[9]);menu["WFWorkflowActionParameters"]["WFMenuItems"]=[s+"×" for s in SPEEDS]
    steps.append(menu)
    for speed in SPEEDS:
        choice=copy.deepcopy(src[10])
        choice["WFWorkflowActionParameters"]["WFMenuItemTitle"]=speed+"×"
        steps.extend((choice,execution(probe(speed),src[11])))
    steps.append(copy.deepcopy(src[14]))
    out["WFWorkflowActions"]=steps

    open_groups=[x["WFWorkflowActionParameters"]["GroupingIdentifier"] for x in steps
                 if x["WFWorkflowActionIdentifier"]==COND and x["WFWorkflowActionParameters"].get("WFControlFlowMode")==0]
    closed=[x["WFWorkflowActionParameters"]["GroupingIdentifier"] for x in steps
            if x["WFWorkflowActionIdentifier"]==COND and x["WFWorkflowActionParameters"].get("WFControlFlowMode")==2]
    assert sorted(open_groups)==sorted(closed) and len(open_groups)==11
    cmds=[x["WFWorkflowActionParameters"]["command"] for x in steps if x["WFWorkflowActionIdentifier"]==EXEC and "command" in x["WFWorkflowActionParameters"]]
    assert len(cmds)==16, len(cmds)  # 5 fast + 5 universal + 5 probes + cleanup
    assert not any("; then" in c or " || " in c or "if ffmpeg" in c for c in cmds)
    assert sum("ffprobe " in c for c in cmds)==5
    assert sum("profile=LC" in str(x) for x in steps)==5
    assert out["WFWorkflowMinimumClientVersion"]==donor["WFWorkflowMinimumClientVersion"]
    uuids=[x.get("WFWorkflowActionParameters",{}).get("UUID") for x in steps]
    uuids=[x for x in uuids if x]
    assert len(uuids)==len(set(uuids))
    print("VALIDATED",len(steps),"actions, fast AAC-LC, native iOS audio for all other profiles")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--donor",type=Path,required=True)
    p.add_argument("--ios-ref",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    tree=build(plistlib.loads(x.donor.read_bytes()),plistlib.loads(x.ios_ref.read_bytes()))
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_bytes(plistlib.dumps(tree,fmt=plistlib.FMT_BINARY,sort_keys=False))

#!/usr/bin/env python3
"""Produce an iOS 17.3.1-compatible Speed Video variant using Apple's media decoder.

The normal Speed Video and Voice to Status source files are NOT modified.
The new shortcut asks native Encode Media to export audio-only AIFF (lossless),
then a-Shell FFmpeg only copies/re-times the *original video* and processes
the normalized uncompressed audio (atempo, single final AAC encode).

This handles xHE-AAC/USAC provided the user's iOS AVFoundation can decode it.
For AV1 videos, MP4 remuxing and Photos import still require device validation.
"""
from __future__ import annotations
import argparse
import copy
import plistlib
import uuid
from pathlib import Path
from urllib.parse import quote

APP = "⚡ Speed Video Universal"
FR = ("1.1", "1.2", "1.3", "1.4", "1.5")
INPUT = "__universal_entrada"
AUDIO = "__universal_audio.aiff"
OUTPUT = "__universal.mp4"


def uid() -> str:
    return str(uuid.uuid4()).upper()


def action(identifier: str, params: dict) -> dict:
    return {"WFWorkflowActionIdentifier": identifier,
            "WFWorkflowActionParameters": params}


def output_ref(action_uuid: str, name: str) -> dict:
    return {"Value": {"Type": "ActionOutput", "OutputUUID": action_uuid,
                      "OutputName": name},
            "WFSerializationType": "WFTextTokenAttachment"}


def create(donor: dict) -> dict:
    out = copy.deepcopy(donor)
    original = donor["WFWorkflowActions"]
    assert len(original) == 15
    assert original[7]["WFWorkflowActionIdentifier"] == "is.workflow.actions.setitemname"
    assert original[8]["WFWorkflowActionIdentifier"] == "AsheKube.app.a-Shell-mini.PutFileIntent"
    assert original[9]["WFWorkflowActionIdentifier"] == "is.workflow.actions.choosefrommenu"
    assert original[11]["WFWorkflowActionIdentifier"] == "AsheKube.app.a-Shell-mini.ExecuteCommandIntent"

    # Original share-sheet and FINALIZAR callback are preserved.
    common = copy.deepcopy(original[:9])
    common[1]["WFWorkflowActionParameters"]["fileName"] = OUTPUT
    common[3]["WFWorkflowActionParameters"]["command"] = (
        f'rm -f "{INPUT}" "{AUDIO}" "{OUTPUT}"'
    )
    common[7]["WFWorkflowActionParameters"]["WFName"] = INPUT

    # Give the native media decoder the original shared file, NOT the output
    # of the preceding a-Shell upload action (which is not a media object).
    encode_id = uid()
    wf_input = copy.deepcopy(original[7]["WFWorkflowActionParameters"]["WFInput"])
    wf_input["Value"]["Aggrandizements"] = [{
        "Type": "WFCoercionVariableAggrandizement",
        "CoercionItemClass": "WFAVAssetContentItem"
    }]
    native_audio = action("is.workflow.actions.encodemedia", {
        "WFInput": wf_input,
        "UUID": encode_id,
        "WFMediaAudioOnly": True,
        "WFMediaAudioFormat": "AIFF",
        "WFMediaSpeed": "Normal",
        "Metadata": False,
    })

    named_audio_id = uid()
    rename_audio = action("is.workflow.actions.setitemname", {
        "WFName": AUDIO,
        "WFDontIncludeFileExtension": False,
        "WFInput": output_ref(encode_id, "Encoded Media"),
        "UUID": named_audio_id,
    })
    put_audio = action("AsheKube.app.a-Shell-mini.PutFileIntent", {
        "file": output_ref(named_audio_id, "Item Renomeado"),
        "UUID": uid(),
        "ShowWhenRun": False
    })

    menu = copy.deepcopy(original[9])
    menu["WFWorkflowActionParameters"]["WFMenuItems"] = [f"{x}×" for x in FR]
    flow = common + [native_audio, rename_audio, put_audio, menu]

    for rate in FR:
        branch = copy.deepcopy(original[10])
        branch["WFWorkflowActionParameters"]["WFMenuItemTitle"] = f"{rate}×"
        exec_action = copy.deepcopy(original[11])
        exec_action["WFWorkflowActionParameters"]["UUID"] = uid()

        url = "shortcuts://run-shortcut?name=" + quote(APP, safe="") + "&input=text&text=FINALIZAR"
        cmd = " ".join((
            f'ls -lh "{INPUT}" "{AUDIO}" &&',
            'ffmpeg -hide_banner -loglevel info -stats -y',
            f'-i "{INPUT}" -i "{AUDIO}"',
            '-map 0:v:0 -map 1:a:0 -c:v copy',
            f'-bsf:v "setts=pts=PTS/{rate}:dts=DTS/{rate}:duration=DURATION/{rate}"',
            f'-af "atempo={rate}" -c:a aac -b:a 192k',
            '-movflags +faststart',
            f'"{OUTPUT}" && open "{url}"',
        ))
        assert "'" not in cmd
        exec_action["WFWorkflowActionParameters"]["command"] = "sh -c '" + cmd + "'"
        exec_action["WFWorkflowActionParameters"]["openWindow"] = "open"
        exec_action["WFWorkflowActionParameters"]["ShowWhenRun"] = False
        flow += [branch, exec_action]

    flow.append(copy.deepcopy(original[14]))
    out["WFWorkflowActions"] = flow
    expected_ids = {a["WFWorkflowActionIdentifier"] for a in original}
    new_ids = {a["WFWorkflowActionIdentifier"] for a in flow} - expected_ids
    assert new_ids == {"is.workflow.actions.encodemedia"}, new_ids
    uuids = [a["WFWorkflowActionParameters"].get("UUID")
             for a in flow if a.get("WFWorkflowActionParameters", {}).get("UUID")]
    assert len(uuids) == len(set(uuids)), "Duplicate UUID"
    assert len(flow) == 24, len(flow)
    assert out["WFWorkflowMinimumClientVersion"] == donor["WFWorkflowMinimumClientVersion"]
    assert out["WFWorkflowInputContentItemClasses"] == donor["WFWorkflowInputContentItemClasses"]
    assert [a["WFWorkflowActionParameters"].get("WFMenuItemTitle") for a in flow
            if a["WFWorkflowActionIdentifier"] == "is.workflow.actions.choosefrommenu"
            and a["WFWorkflowActionParameters"].get("WFControlFlowMode") == 1] == [
                f"{x}×" for x in FR]
    print("Validated:", len(flow), "actions, 5 speed branches, iOS 17 media encoder")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--donor", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    donor = plistlib.loads(a.donor.read_bytes())
    payload = plistlib.dumps(create(donor), fmt=plistlib.FMT_BINARY, sort_keys=False)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(payload)
    print("Unsigned:", a.output, len(payload), "bytes")

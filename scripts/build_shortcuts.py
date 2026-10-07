#!/usr/bin/env python3
"""Build two iOS 17.3.1-compatible Shortcuts from trusted local donor .wflow files.

Only the action types present in the original iOS 17.3.1 exports are used.
Requires macOS only for donor extraction, not for editing/validation.
"""
from __future__ import annotations
import argparse
import copy
import plistlib
import uuid
from pathlib import Path
from urllib.parse import quote

DONOR_SPEED = "Speed-Video.original.wflow"
DONOR_VOICE = "Voice-to-Status.original.wflow"


def callback(name: str) -> str:
    return ("shortcuts://run-shortcut?name="
            + quote(name, safe="") + "&input=text&text=FINALIZAR")


def shell(command: str) -> str:
    # Shortcut donor already configures a-Shell mini: openWindow=open,
    # ShowWhenRun=false, callback to Shortcuts once output is complete.
    if "'" in command:
        raise ValueError("single quote in shell command")
    return "sh -c '" + command + "'"


def validate(original: dict, updated: dict, expected_count: int) -> None:
    donor_actions = original["WFWorkflowActions"]
    output_actions = updated["WFWorkflowActions"]
    assert len(output_actions) == expected_count
    allowed = {a["WFWorkflowActionIdentifier"] for a in donor_actions}
    assert all(a["WFWorkflowActionIdentifier"] in allowed for a in output_actions)
    for key in ("WFWorkflowMinimumClientVersion", "WFWorkflowClientVersion",
                "WFWorkflowInputContentItemClasses", "WFWorkflowTypes"):
        assert updated[key] == original[key], key
    ids = [a.get("WFWorkflowActionParameters", {}).get("UUID") for a in output_actions]
    ids = [x for x in ids if x]
    assert len(ids) == len(set(ids)), "duplicate action UUID"
    for a in output_actions:
        c = a.get("WFWorkflowActionParameters", {}).get("command", "")
        assert "Acelerar%20Video" not in c
        assert "%C3%81udio" not in c


def voice_build(original: dict) -> dict:
    out = copy.deepcopy(original)
    name = "🎙️ Voice → Status"
    # Preserve the iOS-proven minimal `sh -c 'ffmpeg && open'` control flow.
    # Showwaves creates animated cyan waveform while keeping the AAC audio.
    # No Shortcuts action was added: only the a-Shell command changes.
    command = " ".join((
        'ls -lh "__audio.m4a" &&',
        'ffmpeg -hide_banner -loglevel info -stats -y',
        '-f lavfi -i color=c=0x080C13:s=720x1280:r=24',
        '-i "__audio.m4a"',
        '-filter_complex "[1:a]asplit=2[aout][aw];'
        '[aw]showwaves=s=640x220:mode=cline:rate=24:colors=0x00D9FF,'
        'format=rgba[wave];'
        '[0:v][wave]overlay=(W-w)/2:(H-h)/2:shortest=1[v]"',
        '-map "[v]" -map "[aout]"',
        '-c:v h264_videotoolbox -b:v 950k -pix_fmt yuv420p',
        '-c:a aac -b:a 160k -ar 44100',
        '-movflags +faststart -shortest "__status.mp4" &&',
        f'open "{callback(name)}"',
    ))
    target = out["WFWorkflowActions"][9]
    assert target["WFWorkflowActionIdentifier"] == "AsheKube.app.a-Shell-mini.ExecuteCommandIntent"
    target["WFWorkflowActionParameters"]["command"] = shell(command)
    validate(original, out, 10)
    return out


def speed_build(original: dict) -> dict:
    out = copy.deepcopy(original)
    actions = out["WFWorkflowActions"]
    name = "⚡ Speed Video"
    assert len(actions) == 15
    menu = actions[9]
    proto_branch = actions[10]
    proto_execute = actions[11]
    menu_end = actions[14]
    labels = ["1.1×", "1.2×", "1.3×", "1.4×", "1.5×"]
    menu["WFWorkflowActionParameters"]["WFMenuItems"] = labels
    rebuilt = actions[:10]
    for label, speed in zip(labels, ("1.1", "1.2", "1.3", "1.4", "1.5")):
        branch = copy.deepcopy(proto_branch)
        branch["WFWorkflowActionParameters"]["WFMenuItemTitle"] = label
        execute = copy.deepcopy(proto_execute)
        execute["WFWorkflowActionParameters"]["UUID"] = str(uuid.uuid4()).upper()
        # Preserve original proven `sh -c 'ffmpeg && open'` control flow.
        # Preserve existing proven speed logic: packet timestamps change,
        # but the H.264/HEVC video bitstream is copied, not transcoded.
        command = " ".join((
            'ls -lh "__entrada" &&',
            'ffmpeg -hide_banner -loglevel info -stats -y',
            '-i "__entrada" -map 0:v:0 -map 0:a:0?',
            '-c:v copy',
            f'-bsf:v "setts=pts=PTS/{speed}:dts=DTS/{speed}:duration=DURATION/{speed}"',
            f'-af "atempo={speed}" -c:a aac -b:a 192k',
            '-movflags +faststart "__acelerado.mov" &&',
            f'open "{callback(name)}"',
        ))
        execute["WFWorkflowActionParameters"]["command"] = shell(command)
        rebuilt.extend([branch, execute])
    rebuilt.append(menu_end)
    out["WFWorkflowActions"] = rebuilt
    validate(original, out, 21)
    actual = [a.get("WFWorkflowActionParameters", {}).get("WFMenuItemTitle")
              for a in rebuilt if a["WFWorkflowActionIdentifier"] == "is.workflow.actions.choosefrommenu"
              and str(a.get("WFWorkflowActionParameters", {}).get("WFControlFlowMode")) == "1"]
    assert actual == labels, actual
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", type=Path, default=Path("build/extracted"))
    p.add_argument("--out-dir", type=Path, default=Path("build/unsigned"))
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    specs = (
        (DONOR_VOICE, "Voice-to-Status", voice_build),
        (DONOR_SPEED, "Speed-Video", speed_build),
    )
    for donor_filename, stem, build in specs:
        with (args.in_dir / donor_filename).open("rb") as f:
            original = plistlib.load(f)
        updated = build(original)
        binary = plistlib.dumps(updated, fmt=plistlib.FMT_BINARY, sort_keys=False)
        xml = plistlib.dumps(updated, fmt=plistlib.FMT_XML, sort_keys=False)
        (args.out_dir / (stem + ".wflow")).write_bytes(binary)
        (args.out_dir / (stem + ".plist")).write_bytes(xml)
        assert plistlib.loads(binary)["WFWorkflowActions"] == updated["WFWorkflowActions"]
        print(f"{stem}: {len(updated['WFWorkflowActions'])} actions; iOS 17.3.1 donor-safe")


if __name__ == "__main__":
    main()

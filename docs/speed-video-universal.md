# ⚡ Speed Video Universal v4 — validated on iOS 17.3.1

**User-tested successful** with the problematic Instagram H.264 + xHE-AAC/USAC source and with ordinary videos previously processed by Speed Video.

## Why v4 exists

The a-Shell mini FFmpeg AAC decoder aborts on some xHE-AAC/USAC inputs (`aacdec_usac.c:1646`). Native iOS 17.3.1 **Encode Media** can decode this clip's xHE-AAC to a 123.994558-second, approximately 21 MiB AIFF file. Initial Universal v1–v3 attempts were broken in part because the generated Encode Media action had `WFInput` but was missing its true `WFMedia` input parameter. The correct parameter and serialization were obtained by comparing an **iOS 17.3.1-exported, manually edited .shortcut** with the generated one. See [issue #1](../issues/1).

## v4 pipeline

1. Receive a video from the iOS Share Sheet.
2. Native `Encode Media → Audio Only → AIFF` extracts/decodes audio **before** calling a-Shell mini. Uses iOS-proven `WFMedia = ExtensionInput`.
3. Copy AIFF and original source video to a-Shell mini using separate, named files.
4. Offer five presets: 1.1×, 1.2×, 1.3×, 1.4×, 1.5×.
5. FFmpeg opens the original video with **`-analyzeduration 0 -probesize 32 -an`**, copies only video packets with **`-c:v copy`**, retimes using `setts`; takes audio solely from AIFF, speeds it with `atempo`, outputs AAC ~192 kbps.
6. Save resulting MP4 to Photos with the original proven `FINALIZAR` callback and clean temporary files on success. Failed conversions may leave temporaries until the next successful run.

## Device acceptance, 2026-10-14

- Tested on physical iOS 17.3.1 with a-Shell mini.
- Source: ~124s, H.264 High 720×1280 30fps, xHE-AAC/USAC stereo 44.1kHz.
- Output: **H.264 High 720×1280 30fps, AAC-LC stereo 44.1 kHz, duration 00:01:22.67 at 1.5×**.
- Terminal: `frame=3724`, `q=-1.0`, `Lsize=121167KiB`, `speed=36.4x`. No USAC assertion in successful run.
- User also verified regular compatible videos work on v4.

## Limitations

- Compatibility with AV1 video, all media containers and videos without audio remains unverified.
- Native audio extraction and AIFF may increase total processing time and temporary disk usage relative to traditional Speed Video.
- The original `⚡ Speed Video` and `🎙️ Voice → Status` remain preserved and functional.
- Signed .shortcut: [Speed Video Universal v4](../shortcuts/%E2%9A%A1%20Speed%20Video%20Universal%20v4.shortcut).
- Source: `scripts/build_universal_v4.py`; signed and source-verified in [GitHub Actions](https://github.com/Allukardh/iOS-Shortcuts-Lab/actions/runs/38506099255).

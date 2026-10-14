# ⚡ Speed Video Universal — experimental iOS 17.3.1 build

**Install next to your existing ⚡ Speed Video. Do not replace the proven version.**

This is a separately named Shortcuts variant for Instagram downloads or other
videos whose audio fails inside the FFmpeg AAC/USAC decoder.

## Pipeline

1. Shared video is copied unchanged into a-Shell mini.
2. The native iOS **Encode Media → Audio Only → AIFF** action extracts and
   decodes audio into uncompressed, lossless PCM AIFF using Apple media APIs.
   iOS itself must support the source codec; xHE-AAC is the main test target.
3. The AIFF is copied to a-Shell mini.
4. The existing fine-control menu offers 1.1×, 1.2×, 1.3×, 1.4×, 1.5×.
5. FFmpeg remuxes original H.264/HEVC/AV1 video packets with `-c:v copy`,
   retimes video timestamps with `setts`, and speeds the AIFF with `atempo`.
   Only the final output audio is encoded to AAC (192 kb/s).
6. Saves output via the original silent `FINALIZAR` callback, then cleans
   `__universal_entrada`, `__universal_audio.aiff`, `__universal.mp4`.

## Compatibility limits

- Donor: user's signed iOS **17.3.1** Speed Video (all original callback,
  share-sheet, camera-roll, and a-Shell intent structures preserved).
- One extra **Encode Media** action (built into iOS 17) plus original donor
  **Rename File** and **Put File** action types.
- Native AVFoundation must support decoding the source audio. AV1 video
  copied to MP4 must be accepted by the iPhone's Photos library.
- The tool is experimental until **the exact problem video is tested
  on the phone**. A signed file and syntactically valid actions are not
  proof that iOS audio export and callback will succeed.
- A **video without audio** will fail at the native audio-only export;
  keep the standard Speed Video for silent videos.
- No login, subscription, jailbreak trick, or unsupported iOS 18 feature.

Source: `scripts/build_speed_universal.py`.
The build workflow touches only the new `shortcuts/⚡ Speed Video Universal.shortcut`
file and leaves `⚡ Speed Video` and `🎙️ Voice → Status` unchanged.

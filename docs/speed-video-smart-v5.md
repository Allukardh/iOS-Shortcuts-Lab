# Speed Video Smart v5 — staged test candidate (NOT the final Speed Video)

The validated **⚡ Speed Video Universal v4** and the traditional
**⚡ Speed Video** remain untouched and available in the user's clean
three-shortcut Drive folder.

## Automatic algorithm

1. Share the video to **⚡ Speed Video Smart Test**.
2. Copy the original video once to the a-Shell file **`__smart_source.mp4`**.
3. User selects a fine speed: **1.1×, 1.2×, 1.3×, 1.4×, 1.5×**.
4. Try the proven **fast** FFmpeg pipeline, copying video packets and
   speeding audio without asking iOS to extract it first.
5. **If and only if FFmpeg returns an error**, call this Shortcut again with
   a precise **`FALLBACK_<speed>`** text token.
6. During fallback, retrieve the original video from a-Shell, use native
   **iOS 17 Encode Media** to decode its audio as lossless AIFF, then run the
   Universal v4 command and save result.
7. Both successes use the proven **`FINALIZAR`** photo-save callback and
   success cleanup. There is **no infinite fallback loop**.

## Pending real device tests

- A standard iPhone camera video should take the fast route without
  running the Apple Encode Media step.
- The known 118-MiB Instagram H.264 + xHE-AAC clip should fail the fast
  path and seamlessly enter Apple's AIFF conversion fallback, then succeed.
- The fallback retrieval (`Get file` from a-Shell mini, then native
  media conversion) has **not yet been validated on the physical phone**.
- If the iOS shell FFmpeg assertion terminates the parent app before our
  `else` branch, the fallback callback cannot fire; the user must report
  the terminal screenshot.
- The temporary `.mp4` filename might be unsuitable for some source
  containers, even if FFmpeg accepts their video data.
- No guarantee for AV1 or videos without audio yet.

Once both actual phone tests pass, promote the Smart version to
**⚡ Speed Video** and keep Universal v4 and Voice → Status as separate
backups in the Drive; clean the test versions afterwards.

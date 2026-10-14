# ⚡ Speed Video Smart v5.3 — one foreground appearance experiment

The current v5.2 **works** for normal AAC-LC and USAC according to actual device testing, but **opens a-Shell mini twice**: once for ffprobe and once for FFmpeg. Production v4 uses one foreground appearance but always performs the slower Apple AIFF audio extraction.

## What we learned by reading the upstream app code
[`ExecuteCommandIntentHandler.swift`](https://github.com/holzschu/a-shell/blob/master/a-Shell-Intents/ExecuteCommandIntentHandler.swift) confirms:
- `openWindow=.close` **forces extension execution**, rather than presenting the app interface.
- Extension commands run within the **same app group** files as the normal app.
- Auto-choice `localCommands` omits ffprobe, but `openWindow=.close` bypasses that automatic selection and executes via `ios_system`.
- The developer warns extension jobs should finish in ~5 seconds.
- `GetFileIntentHandler` reads from the same app-group folder without launching the app.

Thus an extension-only **read-only ffprobe** is technically promising, but ffprobe's extension-time framework loading and codecs are not yet device-verified.

## v5.3 algorithm
1. Receive video, copy to a-Shell mini via PutFile intent (no UI launch).
2. User selects speed 1.1×–1.5×.
3. Execute `ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,profile ... > __smart_profile.txt` with **Run in Extension / openWindow=close**.
4. Native GetFile / Get Text / If reads the report.
5. If AAC profile LC, launch a-Shell for direct fast FFmpeg (no AIFF).
6. Otherwise Apple's native Encode Media **directly from the original Share Sheet input** creates AIFF, then launch a-Shell to do the physically successful Universal v4 video-only / audio-AIFF method.
7. FIN callback saves to Photos and cleans temporary files.

## Acceptance conditions
- First test a short iPhone camera AAC-LC video and then the already-known Instagram H.264/USAC video. Each should show **at most one foreground a-Shell interface appearance** for FFmpeg.
- If the first test fails at the ffprobe step, that indicates ffprobe cannot execute within the a-Shell mini Intent Extension; stop testing and do not replace v4 or v5.2.
- If probe succeeds but output fails, inspect whether Get File → Get Text → If worked and whether native Encode Media got the share input.
- A signed .shortcut and structurally correct 64 actions **do not verify the extension runtime**.
- We have not verified AV1, audio-less movies or every media container.
- Do not delete the 3 real-world-validated release shortcuts. Drive root carries beta only; release folder must stay at exactly three files.

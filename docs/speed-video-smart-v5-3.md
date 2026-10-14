# ⚡ Smart Speed v5.3 (one-foreground-app experiment)

This is a **beta** for iOS **17.3.1**, separate from the proven v4 and v5.2.

## Why the double appearance could be eliminated

According to the [a-Shell mini upstream ExecuteCommandIntentHandler.swift](https://github.com/holzschu/a-shell/blob/master/a-Shell-Intents/ExecuteCommandIntentHandler.swift), an Execute command with **openWindow = close** runs in an iOS Intent extension, in the same app-group folder where the **PutFile** and **GetFile** intents operate. In *auto* mode, ffprobe is absent from the list of lightweight localCommands and therefore the app opens. Explicit *close* forces the extension execution path.

The extension has limited runtime, and the developer only describes it as appropriate for commands that do not require UI and run in **under 5 seconds**. No guarantee that the bundled ffprobe works from an app extension on a physical iOS 17.3.1 device.

## Data path

Video Share Sheet → copy file using original working PutFile → pick 1.1× through 1.5× → **offscreen** ffprobe → native Get File / Detect Text / If → fast ffmpeg for AAC-LC or native audio AIFF plus proven Universal-v4 ffmpeg for other profiles → FINALIZAR Photo save/cleanup.

Normal AAC-LC and source H.264+xHE-AAC were confirmed on prior **v5.2**, which opened a-Shell twice. This build changes only the placement, code path and foreground setting of the ffprobe probe. Every video still receives a single FFmpeg conversion; there should be exactly one foreground a-Shell appearance **if the extension supports ffprobe**.

## Required test and clear stop condition

1. Import *⚡ Speed Video Smart v5.3* without overwriting old shortcuts; test a short camera video. Confirm only one foreground a-Shell.
2. Test the previously working Instagram xHE-AAC video; confirm just one foreground a-Shell.
3. If the shortcut stops at ffprobe with `command not found`, a failed action, or exceeds the extension's allowed time, **do not infer FFmpeg/codec failure**. Fall back to v5.2 and do not tamper with the stable releases.

Signed builds are not on-device validation.

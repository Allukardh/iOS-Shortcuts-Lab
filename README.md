# iOS Shortcuts Lab

A small gallery of **real-device-tested Shortcuts for iOS 17.3.1**, built from the user's original exports. All releases rely on **a-Shell mini** and FFmpeg. The GitHub Actions workflow uses the public Shortcuty signing API (no Apple account or paid API key).

## ✅ Three validated releases

| Shortcut | iOS 17.3.1 acceptance | Main function |
|---|---|---|
| [🎙️ Voice → Status](./shortcuts/%F0%9F%8E%99%EF%B8%8F%20Voice%20%E2%86%92%20Status.shortcut) | **User tested** | Makes a WhatsApp-ready vertical MP4 with waveform from audio. |
| [⚡ Speed Video](./shortcuts/%E2%9A%A1%20Speed%20Video.shortcut) | **User tested** | Fast video packet-copy acceleration at 1.1×–1.5× for regular compatible source audio. |
| [⚡ Speed Video Universal v4](./shortcuts/%E2%9A%A1%20Speed%20Video%20Universal%20v4.shortcut) | **User tested** | Uses iOS native audio extraction to avoid a-Shell's xHE-AAC/USAC decoder bug and preserves original video packets. |

The matching three verified signed files are the *only three shortcuts* in the user's Google Drive `iOS-Shortcuts-Lab` release folder. Earlier failing files, diagnostic folders and donor duplicates were removed from Drive after their source code and donor exports were preserved here in Git history.

## 🧪 Smart Speed — tested v5.2 and one-foreground experimental v5.3

[⚡ Speed Video Smart v5.2](./shortcuts/experimental/%E2%9A%A1%20Speed%20Video%20Smart%20v5.2.shortcut) **successfully ran on physical iOS 17.3.1** with conventional AAC and the problematic xHE-AAC/USAC source. It identifies the source audio's profile with `ffprobe` and uses iOS native **If** to choose the fast direct pipeline or native iOS → AIFF → Universal v4 pipeline. The user reported a drawback: **two visible a-Shell appearances**, one for probing and one for FFmpeg.

[⚡ Speed Video Smart v5.3](./shortcuts/experimental/%E2%9A%A1%20Speed%20Video%20Smart%20v5.3.shortcut) moves **ffprobe** into the **nonforeground a-Shell mini Intent Extension** (`openWindow=close`), and then runs the profile selection in the same Shortcuts invocation. The only intended foreground app opening is the final FFmpeg job. Native iOS conversion takes the **original Share Sheet input** rather than retrieving a large movie from the a-Shell storage.

This architecture comes directly from the upstream a-Shell mini [ExecuteCommandIntentHandler.swift](https://github.com/holzschu/a-shell/blob/master/a-Shell-Intents/ExecuteCommandIntentHandler.swift), whose forced close mode executes via `ios_system` inside the app group's extension; the developer advises <5s lightweight tasks.

**Status: v5.3 signed and structure-verified, NOT yet tested on the phone.** A forced extension `ffprobe` may still fail if required libraries are unavailable in the extension or execution exceeds the time limit. Its `WFMedia` native audio input matches the user's real iOS 17.3.1 export. The v5.2 beta and three proven releases remain unchanged until real-device acceptance. [v5.3 design and test plan](./docs/speed-video-smart-v5-3.md) · [Issue #2](../../issues/2).

## Proven implementation

- Video: `-c:v copy` plus `setts` timestamps; avoids transcoding and generational video loss.
- Audio: `atempo`, AAC-LC final encode; Universal v4 uses native iOS Encode Media → AIFF first.
- Accurate iOS 17 native `Encode Media` input needs the **`WFMedia`** field, verified against an on-device-exported original.
- Speed options: 1.1× / 1.2× / 1.3× / 1.4× / 1.5×.
- Successful builds save to Photos and delete temporary files via the name-based `FINALIZAR` callback. Failures may leave residue to aid debugging; a later successful run cleans it.
- **Not fully universal:** video AV1 and silent videos are not yet validated; some container compatibility varies. AIFF extraction adds temporary disk space and preprocessing time.

## Reproducible build and signing

GitHub Actions processes: **signed donor → macOS AEA1 extraction → binary plist action construction → Shortcuty public signing API → AEA1 integrity check → signed .shortcut**.

[Universal v4 accepted build](../../actions/runs/38506099255) · [Smart v5.3 experimental workflow](../../actions/workflows/build-speed-smart-v5-3.yml) · [xHE-AAC investigation (closed)](../../issues/1).

Sources and old references stay in `scripts/`, `donors/`, Git history and `docs/`; failed signed binaries are no longer promoted as gallery releases.

**Security:** never publish Apple IDs, passwords, keychain data or personal files inside Shortcuts. A third-party signing server can inspect workflow contents. A successful signature/content-diff is *not* equivalent to a successful iPhone runtime test.

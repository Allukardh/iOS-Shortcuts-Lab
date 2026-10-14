# iOS Shortcuts Lab

A small gallery of **real-device-tested Shortcuts for iOS 17.3.1**, built from the user's original exports. All releases rely on **a-Shell mini** and FFmpeg. The GitHub Actions workflow uses the public Shortcuty signing API (no Apple account or paid API key).

## ✅ Three validated releases

| Shortcut | iOS 17.3.1 acceptance | Main function |
|---|---|---|
| [🎙️ Voice → Status](./shortcuts/%F0%9F%8E%99%EF%B8%8F%20Voice%20%E2%86%92%20Status.shortcut) | **User tested** | Makes a WhatsApp-ready vertical MP4 with waveform from audio. |
| [⚡ Speed Video](./shortcuts/%E2%9A%A1%20Speed%20Video.shortcut) | **User tested** | Fast video packet-copy acceleration at 1.1×–1.5× for regular compatible source audio. |
| [⚡ Speed Video Universal v4](./shortcuts/%E2%9A%A1%20Speed%20Video%20Universal%20v4.shortcut) | **User tested** | Uses iOS native audio extraction to avoid a-Shell's xHE-AAC/USAC decoder bug and preserves original video packets. |

The matching three verified signed files are the *only three shortcuts* in the user's Google Drive `iOS-Shortcuts-Lab` release folder. Earlier failing files, diagnostic folders and donor duplicates were removed from Drive after their source code and donor exports were preserved here in Git history.

## 🧪 Smart Speed v5.2 — experimental (NOT a replacement yet)

[⚡ Speed Video Smart v5.2](./shortcuts/experimental/%E2%9A%A1%20Speed%20Video%20Smart%20v5.2.shortcut) is the only active beta. It tests a codec-preflight workflow using iOS 17's native **If** action, **not** unreliable conditional expressions in a-Shell's non-POSIX `sh`.

1. A short `ffprobe` invocation records the audio profile and calls back to the Shortcut (`PROBE_<speed>`).
2. Native Shortcuts **Get File → Get Text → If** examines the codec report.
3. AAC-LC goes through the original fast FFmpeg command; other audio formats use Apple's native audio-to-AIFF preparation and the accepted Universal v4 command.
4. Only the validated `&& open FINALIZAR` callback performs save/cleanup.

The user's **v5** failed with `if: command not found`. Their **v5.1** did not process video because an attempted nested `sh` / `||` structure was unsupported in practice. Those test shortcuts were removed from the active gallery. [Investigation and remaining test requirements](../../issues/2).

**Important:** v5.2 has passed signature and static action graph validation, **not actual iOS 17.3.1 runtime verification**. The initial `ffprobe` callback, native Get Text/If decision, and original-video retrieval still require one ordinary and one USAC test on the phone. Keep the three validated releases unchanged.

## Proven implementation

- Video: `-c:v copy` plus `setts` timestamps; avoids transcoding and generational video loss.
- Audio: `atempo`, AAC-LC final encode; Universal v4 uses native iOS Encode Media → AIFF first.
- Accurate iOS 17 native `Encode Media` input needs the **`WFMedia`** field, verified against an on-device-exported original.
- Speed options: 1.1× / 1.2× / 1.3× / 1.4× / 1.5×.
- Successful builds save to Photos and delete temporary files via the name-based `FINALIZAR` callback. Failures may leave residue to aid debugging; a later successful run cleans it.
- **Not fully universal:** video AV1 and silent videos are not yet validated; some container compatibility varies. AIFF extraction adds temporary disk space and preprocessing time.

## Reproducible build and signing

GitHub Actions processes: **signed donor → macOS AEA1 extraction → binary plist action construction → Shortcuty public signing API → AEA1 integrity check → signed .shortcut**.

[Universal v4 accepted build](../../actions/runs/38506099255) · [Smart v5 experimental workflow](../../actions/workflows/build-speed-smart-v5.yml) · [xHE-AAC investigation (closed)](../../issues/1).

Sources and old references stay in `scripts/`, `donors/`, Git history and `docs/`; failed signed binaries are no longer promoted as gallery releases.

**Security:** never publish Apple IDs, passwords, keychain data or personal files inside Shortcuts. A third-party signing server can inspect workflow contents. A successful signature/content-diff is *not* equivalent to a successful iPhone runtime test.

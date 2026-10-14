# iOS Shortcuts Lab

A small gallery of **real-device-tested Shortcuts for iOS 17.3.1**, built from the user's original exports. All releases rely on **a-Shell mini** and FFmpeg. The GitHub Actions workflow uses the public Shortcuty signing API (no Apple account or paid API key).

## ✅ Three validated releases

| Shortcut | iOS 17.3.1 acceptance | Main function |
|---|---|---|
| [🎙️ Voice → Status](./shortcuts/%F0%9F%8E%99%EF%B8%8F%20Voice%20%E2%86%92%20Status.shortcut) | **User tested** | Makes a WhatsApp-ready vertical MP4 with waveform from audio. |
| [⚡ Speed Video](./shortcuts/%E2%9A%A1%20Speed%20Video.shortcut) | **User tested** | Fast video packet-copy acceleration at 1.1×–1.5× for regular compatible source audio. |
| [⚡ Speed Video Universal v4](./shortcuts/%E2%9A%A1%20Speed%20Video%20Universal%20v4.shortcut) | **User tested** | Uses iOS native audio extraction to avoid a-Shell's xHE-AAC/USAC decoder bug and preserves original video packets. |

The matching three verified signed files are the *only three shortcuts* in the user's Google Drive `iOS-Shortcuts-Lab` release folder. Earlier failing files, diagnostic folders and donor duplicates were removed from Drive after their source code and donor exports were preserved here in Git history.

## 🧪 Experimental, not a replacement

[⚡ Speed Video Smart Test — v5 prototype](./shortcuts/experimental/%E2%9A%A1%20Speed%20Video%20Smart%20Test.shortcut) lives under `shortcuts/experimental/` **only**, not in the three-file release folder. It attempts the traditional FFmpeg-only fast path, then automatically calls itself with `FALLBACK_<speed>` and uses native iOS audio decoding to retry through v4 if the direct FFmpeg process fails.

This includes the original codec handling and all five speed choices but **needs a physical iOS 17.3.1 test before promotion**, specifically to prove an a-Shell FFmpeg assertion allows the fallback callback and that Shortcuts' Get File → Encode Media pipeline recognizes the retrieved movie. If the test passes, the Smart version can replace traditional **⚡ Speed Video**, keeping three release files overall. See [v5 test plan](./docs/speed-video-smart-v5.md).

**Keep current validated releases installed and unchanged until v5 is proven.** Importing another Shortcut with the same name can add a number (`1`) and break the `FINALIZAR` name-based callback. The beta uses a unique internal name so it can run alongside them.

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

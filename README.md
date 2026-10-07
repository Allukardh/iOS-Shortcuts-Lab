# iOS Shortcuts Lab

Apple Shortcuts built from **real iOS 17.3.1 exports**, not guessed action schemas.

## Shortcuts (v2 work in progress)

| Shortcut | What it does |
| --- | --- |
| **🎙️ Voice → Status** | Takes shared audio, creates a 720 × 1280 portrait video with a cyan animated waveform and AAC audio, saves it to Photos and cleans temporary files. |
| **⚡ Speed Video** | Speeds a shared H.264/HEVC video to exactly **1.1× / 1.2× / 1.3× / 1.4× / 1.5×**, retaining the original video bitstream and re-timing its audio. |

The donor actions use **a-Shell mini** on iOS. The stock `ffmpeg` executable inside a-Shell mini must support VideoToolbox, `showwaves`, `setts`, and AAC.

## Proven pipeline

1. `donors/`: original, Apple-signed `AEA1` .shortcut exports from iOS 17.3.1.
2. `scripts/extract_signed.py`: on macOS, unpack AEA1 → Apple Archive → `Shortcut.wflow` using the donor’s embedded signing certificate public key. **No Apple ID credentials needed to extract.**
3. `scripts/build_shortcuts.py`: edit the underlying workflow using only original iOS 17.3.1 action IDs; preserve silent a-Shell callback pattern. Emit editable XML `.plist` and unsigned `.wflow` files.
4. GitHub Actions builds and uploads source workflows as artifacts.

### Signing — HubSign optional CI integration

The first real [macOS runner signing attempt](../../actions) successfully extracted the 15-action Speed Video donor, then **Apple’s** `shortcuts sign --mode anyone` failed with **“In order to do this, you must be signed into iCloud.”**

A hosted macOS Actions runner is ephemeral and not logged into the owner’s Apple ID. **Do not put Apple ID passwords, two-factor codes, or session cookies into GitHub Actions secrets or into this repository.**

The build now includes an optional **official RoutineHub HubSign** signing step. To activate it, obtain an eligible RoutineHub membership and a dedicated **HubSign** API key. Add this key **only** to GitHub → Repository Settings → Secrets and variables → Actions → New repository secret with name `HUBSIGN_API_KEY`. Never share passwords or tokens in source code or chat. The next `workflow_dispatch` build will use the key privately to sign both shortcuts. The API returns an AEA1 signed file; CI also tries to extract it before publishing the artifacts.

Alternative: sign on a trusted persistent Mac with iCloud configured.

When no HubSign secret is configured, the CI produces **editable developer workflows only**. After signing succeeds, the build additionally publishes signed `.shortcut` files. **On-device iOS 17.3.1 import/run tests are still required**.

## Testing
Locally verified FFmpeg `showwaves` output with H.264/AAC video and `setts` / `atempo` speed changes for **both H.264 and HEVC**. iPhone / a-Shell mini execution still requires final testing after signing.

## Safety
Before sharing a new Shortcut publicly, review the workflow for tokens, secrets, personally identifiable paths or sensitive data.

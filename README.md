# iOS Shortcuts Lab

An open, reproducible Apple Shortcuts gallery targeting **iOS 17.3.1**.

## Shortcuts

| Name | Purpose |
| ---- | ------- |
| 🎙️ **Voice → Status** | Convert shared audio to an optimized vertical MP4 with an animated waveform, AAC audio, automatic cleanup and a-Shell mini callback. |
| ⚡ **Speed Video** | Speed up H.264/HEVC clips at **1.1× / 1.2× / 1.3× / 1.4× / 1.5×** with packet timestamp adjustment and audio tempo correction. |

Both are generated using action types harvested from the author's existing **iOS 17.3.1** exports. No speculative new iOS 18+ Shortcut actions are used. They use `a-Shell mini` and its bundled FFmpeg.

## Install-ready gallery (device acceptance pending)

Latest signed `.shortcut` files are published automatically into [`shortcuts/`](./shortcuts) whenever the build passes all checks. Both are generated from genuine iOS 17.3.1 originals and re-signed via Shortcuty, without paid accounts.

- [🎙️ Voice → Status](./shortcuts/%F0%9F%8E%99%EF%B8%8F%20Voice%20%E2%86%92%20Status.shortcut) — audio as portrait video with animated waveform.
- [⚡ Speed Video](./shortcuts/%E2%9A%A1%20Speed%20Video.shortcut) — finely adjusted speed presets.

**Install:** open a file from the `shortcuts/` directory, choose **Download raw file** if GitHub previews it, transfer to the iPhone (Files/AirDrop), and open with Apple Shortcuts. Keep the two existing working shortcuts installed until the new versions pass real iOS 17.3.1 runtime testing.

## Automatic reproducible build and signing

**Donors → extract AEA1 → modify bplist → Shortcuty signing API → verify AEA1 → GitHub Actions artifact**.

Our build workflow uses an Apple-hosted compatible macOS runner to *extract* the donor originals; it calls [Shortcuty's **public official signing API**](https://github.com/Shortcuty/Signing-Server-API-Documentation) to sign the newly generated shortcuts. The API is documented as requiring **no API key** and no RoutineHub subscription:

`POST https://sign.shortcuty.app/api/v1/sign`, `multipart/form-data` with a field named `file`.

The signed output is checked by Apple's `aea` unpacking utility, and the resulting workflow actions are compared with the exact ones we submitted, including the minimum client version. **This confirms content integrity, not on-device feature/codec compatibility**.

To get the latest files, open [GitHub Actions](../../actions/workflows/sign-smoke-test.yml), choose the successful `Build and sign iOS 17 Shortcuts (Shortcuty)` run, and download the signed ZIP artifact. Extract it, move the two `.shortcut` files to the iPhone, open them in Apple Shortcuts, and test on **iOS 17.3.1**.

## Important boundaries

- The source donor exports are signed and are kept unchanged for reference.
- Never publish Apple account credentials, keychain dumps, application passwords, tokens, or private shortcuts.
- A public signing provider can read a submitted shortcut. Audit any workflow before sending it to a third party.
- The current signing API is public but its uptime and rate limits are controlled by Shortcuty.
- Final iOS 17.3.1 import and a-Shell mini execution tests must be done on the user's physical phone. Successful signing alone does not prove the callback/audio/video workflow on-device.

## Previous findings

RoutineHub's **membership-only HubSign API** requires a dedicated key and plan. An older public HubSign endpoint no longer produced usable signed files in our October 2026 test. Gluebyte's older `shortcuts.gluebyte.workers.dev` signing endpoint explicitly says it is offline and points to an updated Shortcut Source Helper (version 3.0, released 2026-09-15) that uses Shortcuty.

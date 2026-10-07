# iOS Shortcuts Lab

Versioned, production-ready Apple Shortcuts.

## Compatibility
Primary target: **iOS 17.3.1**.

## Shortcuts
- **Voice → Status** — shared audio → vertical MP4 with animated waveform.
- **Speed Video** — fine-grained playback presets: 1.1×, 1.2×, 1.3×, 1.4×, 1.5×.

## Build & signing
Editable shortcut payloads live in `src/`. A macOS GitHub Actions runner signs distributable builds using Apple's official `shortcuts sign --mode anyone`.

Original AEA1-signed shortcuts are compatibility donors/reference. Modifying an AEA1 package in place invalidates its Apple signature.

## Status
Initial build/signing proof-of-concept.

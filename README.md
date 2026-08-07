# 🎨 FontCraft Assets Library

> Central Asset Repository for the FontCraft Module
> Your dynamic font and emoji library for seamless WebUI integration.

<div align="center">

[![Last Commit](https://img.shields.io/github/last-commit/RipperHybrid/FontLib)](https://github.com/RipperHybrid/FontLib/commits/main) [![Build Status](https://github.com/RipperHybrid/FontLib/actions/workflows/reconfigure.yml/badge.svg)](https://github.com/RipperHybrid/FontLib/actions/workflows/reconfigure.yml)

<br>

**[ 📖 View Visual Catalog ](Preview.md)** &nbsp;&nbsp;•&nbsp;&nbsp; **[ ⚡ Main FontCraft Module ](https://github.com/RipperHybrid/FontCraft.git)**

</div>

---

This repository is the remote asset database for FontCraft. By decoupling the assets from the core module logic, you can push new fonts and emojis instantly without needing to trigger unnecessary commits or releases on the main module.

## 📊 Generated Files

| File | Purpose | Format |
|------|---------|---------|
| [fonts.json](fonts.json) | Module / WebUI API endpoint | Structured JSON |
| [Preview.md](Preview.md) | Visual catalog of all assets | Markdown with images |
| [patched.json](patched.json) | Tracks glyph patching states to prevent redundant builds | JSON |

## 🚀 Core Features

* **Zero-Release Updates:** Adding a single font no longer requires pushing to the main module. Just drop the `.ttf` file in its respective folder, and the WebUI pulls it dynamically.
* **Automated Previews:** The CI/CD pipeline generates the high-quality preview PNGs automatically on every push. No manual image editing is required.
* **Automated Glyph Patching:** The pipeline detects fonts missing critical UI glyphs and silently patches them using a structural donor. This ensures system stability without altering the font's original name, metadata, or core design identity.
* **Lightweight Core:** Keeps the main FontCraft installation zip small, efficient, and focused strictly on system logic.

## 📁 Repository Structure

```text
FontLib/
├── Emoji/                     # Emoji Packs & Icon Fonts
│   └── [Emoji Pack Name]/
│       └── font.ttf           # Drop font file here (PNG auto-generates)
│
├── Fonts/                     # System & Display Fonts
│   └── [Font Family Name]/
│       └── font.ttf           # Drop font file here (PNG auto-generates)
│
├── fonts.json                 # Module & WebUI API Metadata
├── patched.json               # Patching State Tracker
├── Preview.md                 # Visual Catalog
└── .github/workflows/         # Automation Scripts
```

> [!note]
> All fonts and emojis belong to their respective creators. This repository acts as a distribution engine for legally shareable assets. The automated patching process does not claim ownership or alter the original font's identity. If you are a copyright holder and wish to request a removal, or if you have any other concerns, feel free to contact me anytime on Telegram.
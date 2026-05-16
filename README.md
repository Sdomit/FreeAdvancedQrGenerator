# Free Advanced QR Generator

A feature-rich desktop QR code generator built with Python + PyQt6. Generate, style, and export QR codes for any use case — completely free and open source.

![Dark modern UI with QR preview](screenshot.png)

---

## Features

- **8 content types** — Plain Text, URL, Phone, Email, SMS, Contact (vCard), Multi URL, PDF
- **Live preview** — QR updates automatically as you type
- **Custom colors** — Foreground, background, and finder/eye colors with swatch buttons
- **Transparent background** support
- **Gradient overlays** — Apply linear gradients to the QR or background
- **Logo / watermark** — Embed any image at the center with optional elliptical border
- **Multiple module styles** — Square, dots (PIL), and all styles available in segno
- **Error correction levels** — L / M / Q / H
- **Version control** — Manual version selection (1–40), auto-bumps when data is too large
- **Output sizes** — 128 × 128 up to 4096 × 4096 px
- **Export** — Save as PNG, copy to clipboard, or export as SVG
- **Dark modern UI** — Clean landscape layout with grouped controls

---

## Requirements

- Python 3.11+
- [PyQt6](https://pypi.org/project/PyQt6/)
- [segno](https://pypi.org/project/segno/)
- [Pillow](https://pypi.org/project/Pillow/)

---

## Installation

```bash
git clone https://github.com/Sdomit/free-advanced-qr-generator.git
cd free-advanced-qr-generator
pip install -r requirements.txt
python main.py
```

---

## Usage

1. Select a **content type** from the dropdown
2. Enter your data in the input field(s)
3. Adjust appearance settings (colors, style, gradient, logo, margins)
4. The QR code updates automatically — click the preview to enlarge it
5. Use **Save PNG**, **Copy to Clipboard**, or **Export SVG** to get your QR

---

## License

MIT — free to use, modify, and distribute.

---

Developed by [Sarmad Domit](https://linktr.ee/SarmadDomit)

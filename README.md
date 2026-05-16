# Free Advanced QR Generator

> A feature-rich, free and open-source desktop QR code generator — built with Python & PyQt6.

[![Latest Release](https://img.shields.io/github/v/release/Sdomit/free-advanced-qr-generator?label=Download&style=for-the-badge&logo=windows&color=bd93f9)](https://github.com/Sdomit/free-advanced-qr-generator/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

---

## ⚡ Quick Start (Windows)

### Option A — Run the EXE (no Python needed)
1. Go to the [**Releases**](https://github.com/Sdomit/free-advanced-qr-generator/releases/latest) page
2. Download **`Free Advanced QR Generator.exe`**
3. Double-click to run — no installation required

### Option B — Run from source
```bash
git clone https://github.com/Sdomit/free-advanced-qr-generator.git
cd free-advanced-qr-generator
pip install -r requirements.txt
python main.py
```
Or simply double-click **`Run QR Generator.bat`** (requires Python 3.11+ in PATH).

---

## ✨ Features

| Feature | Details |
|--------|---------|
| **8 content types** | Plain Text, URL, Phone, Email, SMS, Contact (vCard), Multi URL, PDF |
| **Live preview** | QR updates automatically as you type |
| **Custom colors** | QR color, background color, finder/eye color — all with live swatches |
| **Transparent background** | Generate QR codes with no background |
| **Gradient overlays** | Apply linear gradients to the QR modules or background |
| **Logo / watermark** | Embed any image at the center with optional elliptical border |
| **Module styles** | Square (crisp) or Dot (rounded PIL rendering) |
| **Error correction** | L / M / Q / H levels |
| **Version control** | Manual selection (1–40), auto-bumps when data is too large |
| **Output sizes** | 128 × 128 up to 4096 × 4096 px |
| **Export** | Save as PNG · Copy to clipboard · Export as SVG |
| **Dark modern UI** | Clean landscape layout with grouped controls |

---

## 🖥️ Requirements (source only)

- Python 3.11+
- PyQt6 ≥ 6.4
- segno ≥ 1.6
- Pillow ≥ 10.0

```bash
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
free-advanced-qr-generator/
├── main.py                  # Entry point
├── qr_generator.py          # UI + generation logic
├── qr_logo_utils.py         # Logo overlay with border
├── qr_gradient_utils.py     # Linear gradient rendering
├── Run QR Generator.bat     # One-click launcher (Windows)
├── requirements.txt
└── README.md
```

---

## 📄 License

MIT — free to use, modify, and distribute.

---

Developed by [Sarmad Domit](https://linktr.ee/SarmadDomit)

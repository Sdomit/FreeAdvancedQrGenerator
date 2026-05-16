import sys
from io import BytesIO

import segno
from PIL import Image, ImageDraw, ImageColor

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QFileDialog, QComboBox, QSlider, QCheckBox,
    QScrollArea, QSizePolicy, QGroupBox, QTextEdit, QDialog, QMenu,
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QSize

from qr_logo_utils import add_logo_with_border
from qr_gradient_utils import apply_linear_gradient

# ---------------------------------------------------------------------------
# Dark-modern stylesheet
# ---------------------------------------------------------------------------
STYLESHEET = """
QWidget {
    background-color: #1e1e2e;
    color: #f8f8f2;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QScrollArea, QScrollArea > QWidget > QWidget {
    background-color: #1e1e2e;
}
QGroupBox {
    border: 1px solid #44475a;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
    color: #bd93f9;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #2a2a3e;
    border: 1px solid #44475a;
    border-radius: 4px;
    padding: 4px 6px;
    color: #f8f8f2;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #bd93f9;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #2a2a3e;
    selection-background-color: #44475a;
    color: #f8f8f2;
}
QPushButton {
    background-color: #44475a;
    color: #f8f8f2;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #6272a4; }
QPushButton:pressed { background-color: #bd93f9; color: #1e1e2e; }
QPushButton#generate_btn {
    background-color: #bd93f9;
    color: #1e1e2e;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 16px;
}
QPushButton#generate_btn:hover { background-color: #cfa9ff; }
QSlider::groove:horizontal {
    height: 4px;
    background: #44475a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #bd93f9;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #bd93f9; border-radius: 2px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #44475a;
    border-radius: 3px;
    background: #2a2a3e;
}
QCheckBox::indicator:checked { background: #bd93f9; border-color: #bd93f9; }
QLabel#status_label { color: #ff5555; font-size: 12px; }
QLabel#preview_placeholder { color: #6272a4; font-size: 13px; }
"""


def _make_checkerboard(size: QSize, tile: int = 12) -> QPixmap:
    pm = QPixmap(size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    c1, c2 = QColor("#2a2a3e"), QColor("#3a3a5e")
    cols = (size.width() + tile - 1) // tile
    rows = (size.height() + tile - 1) // tile
    for r in range(rows):
        for c in range(cols):
            color = c1 if (r + c) % 2 == 0 else c2
            p.fillRect(c * tile, r * tile, tile, tile, QBrush(color))
    p.end()
    return pm


def _swatch_style(color: str) -> str:
    r, g, b = ImageColor.getrgb(color)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    text = "#1e1e2e" if luma > 128 else "#f8f8f2"
    return f"background-color: {color}; color: {text}; border: 1px solid #44475a; border-radius: 4px; padding: 6px 12px;"


def _slider_row(label_text: str, slider: QSlider, value_label: QLabel) -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label_text)
    lbl.setMinimumWidth(130)
    row.addWidget(lbl)
    row.addWidget(slider, 1)
    value_label.setMinimumWidth(28)
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    row.addWidget(value_label)
    return row


class QRGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Free Advanced QR Generator — by Sarmad Domit")
        self.setMinimumSize(1100, 700)

        # State
        self.fg_color = "#000000"
        self.bg_color = "#ffffff"
        self.finder_color = None
        self.logo_img = None
        self.logo_border_color = "#ffffff"
        self.gradient_color1 = "#000000"
        self.gradient_color2 = "#0000ff"
        self.qr_img = None
        self.qr_img_bytes = None

        # Discover real segno module drawers
        self._segno_styles = self._discover_styles()

        # Build UI
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left scrollable panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(480)
        scroll.setMaximumWidth(560)
        scroll.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        left_layout.addWidget(self._build_content_section())
        left_layout.addWidget(self._build_appearance_section())
        left_layout.addWidget(self._build_logo_section())
        left_layout.addWidget(self._build_options_section())

        self.generate_btn = QPushButton("Generate QR Code")
        self.generate_btn.setObjectName("generate_btn")
        self.generate_btn.clicked.connect(self.generate_qr)
        left_layout.addWidget(self.generate_btn)

        credit = QLabel('<a href="https://linktr.ee/SarmadDomit" style="color:#bd93f9;">Developed by Sarmad Domit</a>')
        credit.setOpenExternalLinks(True)
        credit.setAlignment(Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(credit)
        left_layout.addStretch(1)

        scroll.setWidget(left_widget)
        main_layout.addWidget(scroll)

        # Right preview panel
        right_panel = self._build_preview_panel()
        main_layout.addWidget(right_panel, 1)

        # Wire signals that trigger auto-generation
        self._connect_auto_generate()

        # Show the correct input widget for the default type
        self.on_type_changed(0)

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_content_section(self) -> QGroupBox:
        box = QGroupBox("Content")
        layout = QVBoxLayout(box)
        layout.setSpacing(6)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Plain Text", "URL", "Phone", "Email", "SMS",
            "Contact (vCard)", "Multi URL", "PDF",
        ])
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        layout.addWidget(QLabel("QR Content Type:"))
        layout.addWidget(self.type_combo)

        # All input widgets — only one visible at a time
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter plain text…")
        self.text_edit.setMaximumHeight(80)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+1 555 000 0000")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")

        self.sms_widget = QWidget()
        sms_row = QHBoxLayout(self.sms_widget)
        sms_row.setContentsMargins(0, 0, 0, 0)
        self.sms_phone = QLineEdit()
        self.sms_phone.setPlaceholderText("Phone number")
        self.sms_msg = QLineEdit()
        self.sms_msg.setPlaceholderText("Message (optional)")
        sms_row.addWidget(self.sms_phone)
        sms_row.addWidget(self.sms_msg)

        self.vcard_widget = QWidget()
        vcard_col = QVBoxLayout(self.vcard_widget)
        vcard_col.setContentsMargins(0, 0, 0, 0)
        self.vcard_name = QLineEdit(); self.vcard_name.setPlaceholderText("Full Name")
        self.vcard_phone = QLineEdit(); self.vcard_phone.setPlaceholderText("Phone")
        self.vcard_email = QLineEdit(); self.vcard_email.setPlaceholderText("Email")
        self.vcard_org = QLineEdit(); self.vcard_org.setPlaceholderText("Organization (optional)")
        self.vcard_url = QLineEdit(); self.vcard_url.setPlaceholderText("Website URL (optional)")
        for w in (self.vcard_name, self.vcard_phone, self.vcard_email, self.vcard_org, self.vcard_url):
            vcard_col.addWidget(w)

        self.multiurl_input = QTextEdit()
        self.multiurl_input.setPlaceholderText("One URL per line…")
        self.multiurl_input.setMaximumHeight(80)

        self.pdf_widget = QWidget()
        pdf_row = QHBoxLayout(self.pdf_widget)
        pdf_row.setContentsMargins(0, 0, 0, 0)
        self.pdf_path = QLineEdit()
        self.pdf_path.setPlaceholderText("PDF file path or URL")
        pdf_browse = QPushButton("Browse")
        pdf_browse.clicked.connect(self._browse_pdf)
        pdf_row.addWidget(self.pdf_path)
        pdf_row.addWidget(pdf_browse)

        # Container that swaps widgets
        self.input_container = QVBoxLayout()
        layout.addLayout(self.input_container)

        for w in (self.text_edit, self.url_input, self.phone_input,
                  self.email_input, self.sms_widget, self.vcard_widget,
                  self.multiurl_input, self.pdf_widget):
            w.hide()

        # Load from file
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self._load_file)
        layout.addWidget(load_btn)

        return box

    def _build_appearance_section(self) -> QGroupBox:
        box = QGroupBox("Appearance")
        layout = QVBoxLayout(box)
        layout.setSpacing(6)

        # Colors row 1
        color_row = QHBoxLayout()
        self.fg_btn = QPushButton("QR Color")
        self.fg_btn.clicked.connect(self._pick_fg)
        self.fg_btn.setStyleSheet(_swatch_style(self.fg_color))
        self.bg_btn = QPushButton("BG Color")
        self.bg_btn.clicked.connect(self._pick_bg)
        self.bg_btn.setStyleSheet(_swatch_style(self.bg_color))
        color_row.addWidget(self.fg_btn)
        color_row.addWidget(self.bg_btn)
        layout.addLayout(color_row)

        # Transparent BG
        self.transparent_cb = QCheckBox("Transparent background")
        self.transparent_cb.setChecked(False)
        self.transparent_cb.stateChanged.connect(self.generate_qr)
        layout.addWidget(self.transparent_cb)

        # Finder / eye color
        finder_row = QHBoxLayout()
        self.finder_btn = QPushButton("Finder / Eye Color")
        self.finder_btn.clicked.connect(self._pick_finder)
        self.finder_btn.setStyleSheet(_swatch_style("#000000"))
        self.finder_clear_btn = QPushButton("Reset")
        self.finder_clear_btn.clicked.connect(self._clear_finder)
        finder_row.addWidget(self.finder_btn)
        finder_row.addWidget(self.finder_clear_btn)
        layout.addLayout(finder_row)

        # Style
        layout.addWidget(QLabel("Module style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(self._segno_styles)
        self.style_combo.currentIndexChanged.connect(self.generate_qr)
        layout.addWidget(self.style_combo)

        # Gradient
        grad_row = QHBoxLayout()
        self.grad_fg_cb = QCheckBox("Gradient on QR")
        self.grad_bg_cb = QCheckBox("Gradient on BG")
        self.grad_fg_cb.stateChanged.connect(self.generate_qr)
        self.grad_bg_cb.stateChanged.connect(self.generate_qr)
        grad_row.addWidget(self.grad_fg_cb)
        grad_row.addWidget(self.grad_bg_cb)
        layout.addLayout(grad_row)

        grad_colors = QHBoxLayout()
        self.gc1_btn = QPushButton("From")
        self.gc1_btn.clicked.connect(self._pick_gc1)
        self.gc1_btn.setStyleSheet(_swatch_style(self.gradient_color1))
        self.gc2_btn = QPushButton("To")
        self.gc2_btn.clicked.connect(self._pick_gc2)
        self.gc2_btn.setStyleSheet(_swatch_style(self.gradient_color2))
        grad_colors.addWidget(self.gc1_btn)
        grad_colors.addWidget(self.gc2_btn)
        layout.addLayout(grad_colors)

        # Margin slider
        self.margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.margin_slider.setRange(0, 20)
        self.margin_slider.setValue(4)
        self.margin_val = QLabel("4")
        self.margin_slider.valueChanged.connect(lambda v: (self.margin_val.setText(str(v)), self.generate_qr()))
        layout.addLayout(_slider_row("Margin (modules):", self.margin_slider, self.margin_val))

        return box

    def _build_logo_section(self) -> QGroupBox:
        box = QGroupBox("Logo / Watermark")
        layout = QVBoxLayout(box)
        layout.setSpacing(6)

        logo_row = QHBoxLayout()
        add_logo_btn = QPushButton("Add Logo")
        add_logo_btn.clicked.connect(self._load_logo)
        self.logo_name_label = QLabel("No logo")
        self.logo_name_label.setStyleSheet("color: #6272a4; font-size: 11px;")
        clear_logo_btn = QPushButton("Clear")
        clear_logo_btn.clicked.connect(self._clear_logo)
        logo_row.addWidget(add_logo_btn)
        logo_row.addWidget(self.logo_name_label, 1)
        logo_row.addWidget(clear_logo_btn)
        layout.addLayout(logo_row)

        # Logo size slider
        self.logo_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_size_slider.setRange(5, 40)
        self.logo_size_slider.setValue(20)
        self.logo_size_val = QLabel("20%")
        self.logo_size_slider.valueChanged.connect(
            lambda v: (self.logo_size_val.setText(f"{v}%"), self.generate_qr()))
        layout.addLayout(_slider_row("Logo size:", self.logo_size_slider, self.logo_size_val))

        # Border
        border_row = QHBoxLayout()
        self.logo_border_cb = QCheckBox("Add border")
        self.logo_border_cb.stateChanged.connect(self.generate_qr)
        self.logo_border_color_btn = QPushButton("Border Color")
        self.logo_border_color_btn.clicked.connect(self._pick_logo_border_color)
        self.logo_border_color_btn.setStyleSheet(_swatch_style(self.logo_border_color))
        border_row.addWidget(self.logo_border_cb)
        border_row.addWidget(self.logo_border_color_btn)
        layout.addLayout(border_row)

        self.logo_border_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_border_slider.setRange(1, 20)
        self.logo_border_slider.setValue(4)
        self.logo_border_val = QLabel("4")
        self.logo_border_slider.valueChanged.connect(
            lambda v: (self.logo_border_val.setText(str(v)), self.generate_qr()))
        layout.addLayout(_slider_row("Border thickness:", self.logo_border_slider, self.logo_border_val))

        return box

    def _build_options_section(self) -> QGroupBox:
        box = QGroupBox("QR Options")
        layout = QVBoxLayout(box)
        layout.setSpacing(6)

        layout.addWidget(QLabel("Error correction:"))
        self.ec_combo = QComboBox()
        self.ec_combo.addItems(["L — Low (7%)", "M — Medium (15%)", "Q — Quartile (25%)", "H — High (30%)"])
        self.ec_combo.setCurrentIndex(1)
        self.ec_combo.currentIndexChanged.connect(self.generate_qr)
        layout.addWidget(self.ec_combo)

        self.version_slider = QSlider(Qt.Orientation.Horizontal)
        self.version_slider.setRange(1, 40)
        self.version_slider.setValue(1)
        self.version_val = QLabel("1")
        self.version_slider.valueChanged.connect(
            lambda v: (self.version_val.setText(str(v)), self.generate_qr()))
        layout.addLayout(_slider_row("Version (1–40):", self.version_slider, self.version_val))

        layout.addWidget(QLabel("Output size:"))
        self.size_combo = QComboBox()
        self.size_presets = [
            ("128 × 128", 128), ("256 × 256", 256), ("300 × 300", 300),
            ("512 × 512", 512), ("1024 × 1024", 1024),
            ("2048 × 2048", 2048), ("4096 × 4096", 4096),
        ]
        for label, _ in self.size_presets:
            self.size_combo.addItem(label)
        self.size_combo.setCurrentIndex(3)  # 512×512 default
        self.size_combo.currentIndexChanged.connect(self.generate_qr)
        layout.addWidget(self.size_combo)

        return box

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: #16162a;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Preview label
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumSize(450, 450)
        self.qr_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.qr_label.setObjectName("preview_placeholder")
        self.qr_label.setText("QR preview will appear here")
        self.qr_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.qr_label.customContextMenuRequested.connect(self._show_context_menu)
        self.qr_label.mousePressEvent = self._preview_click
        layout.addWidget(self.qr_label, 1)

        # Action buttons
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save PNG")
        self.save_btn.clicked.connect(self.save_qr)
        self.save_btn.setEnabled(False)
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_qr_to_clipboard)
        self.copy_btn.setEnabled(False)
        self.svg_btn = QPushButton("Export SVG")
        self.svg_btn.clicked.connect(self.export_svg)
        self.svg_btn.setEnabled(False)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.svg_btn)
        layout.addLayout(btn_row)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        return panel

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_auto_generate(self):
        for w in (self.url_input, self.phone_input, self.email_input,
                  self.sms_phone, self.sms_msg, self.vcard_name,
                  self.vcard_phone, self.vcard_email, self.vcard_org,
                  self.vcard_url, self.pdf_path):
            w.textChanged.connect(self.generate_qr)
        self.text_edit.textChanged.connect(self.generate_qr)
        self.multiurl_input.textChanged.connect(self.generate_qr)

    # ------------------------------------------------------------------
    # Style discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _discover_styles() -> list[str]:
        return ["Square (default)", "Dot (PIL)"]

    # ------------------------------------------------------------------
    # Type switching
    # ------------------------------------------------------------------

    def on_type_changed(self, _idx: int):
        all_widgets = [
            self.text_edit, self.url_input, self.phone_input, self.email_input,
            self.sms_widget, self.vcard_widget, self.multiurl_input, self.pdf_widget,
        ]
        for w in all_widgets:
            w.hide()
            self.input_container.removeWidget(w)

        mapping = {
            "Plain Text": self.text_edit,
            "URL": self.url_input,
            "Phone": self.phone_input,
            "Email": self.email_input,
            "SMS": self.sms_widget,
            "Contact (vCard)": self.vcard_widget,
            "Multi URL": self.multiurl_input,
            "PDF": self.pdf_widget,
        }
        widget = mapping.get(self.type_combo.currentText(), self.url_input)
        self.input_container.addWidget(widget)
        widget.show()
        self.generate_qr()

    # ------------------------------------------------------------------
    # Input extraction
    # ------------------------------------------------------------------

    def _get_raw_input(self) -> str:
        t = self.type_combo.currentText()
        if t == "Plain Text":
            return self.text_edit.toPlainText()
        if t == "URL":
            return self.url_input.text()
        if t == "Phone":
            return self.phone_input.text()
        if t == "Email":
            return self.email_input.text()
        if t == "SMS":
            return f"{self.sms_phone.text()}|{self.sms_msg.text()}"
        if t == "Contact (vCard)":
            return "|".join([
                self.vcard_name.text(), self.vcard_phone.text(),
                self.vcard_email.text(), self.vcard_org.text(), self.vcard_url.text(),
            ])
        if t == "Multi URL":
            return self.multiurl_input.toPlainText()
        if t == "PDF":
            return self.pdf_path.text()
        return ""

    def _format_qr_data(self, qr_type: str, raw: str) -> str:
        if qr_type == "Plain Text":
            return raw
        if qr_type == "URL":
            return raw if raw.startswith(("http://", "https://", "ftp://")) else f"https://{raw}"
        if qr_type == "Phone":
            return f"tel:{raw}"
        if qr_type == "Email":
            return f"mailto:{raw}"
        if qr_type == "SMS":
            phone, _, msg = raw.partition("|")
            return f"sms:{phone}?body={msg}" if msg else f"sms:{phone}"
        if qr_type == "Contact (vCard)":
            parts = (raw + "||||").split("|")
            name, phone, email, org, url = parts[0], parts[1], parts[2], parts[3], parts[4]
            lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{name}"]
            if phone:
                lines.append(f"TEL:{phone}")
            if email:
                lines.append(f"EMAIL:{email}")
            if org:
                lines.append(f"ORG:{org}")
            if url:
                lines.append(f"URL:{url}")
            lines.append("END:VCARD")
            return "\n".join(lines)
        if qr_type == "Multi URL":
            return "\n".join(u.strip() for u in raw.splitlines() if u.strip())
        if qr_type == "PDF":
            return raw if raw.startswith(("http", "ftp")) else f"file://{raw}"
        return raw

    # ------------------------------------------------------------------
    # QR generation
    # ------------------------------------------------------------------

    def generate_qr(self):
        raw = self._get_raw_input()
        if not raw or not raw.strip():
            self._set_status("Enter content above to generate a QR code.", error=False)
            self._disable_export()
            return

        qr_type = self.type_combo.currentText()
        qr_data = self._format_qr_data(qr_type, raw)

        ec_letters = ["L", "M", "Q", "H"]
        ec_level = ec_letters[self.ec_combo.currentIndex()]
        version = self.version_slider.value()
        output_dim = self.size_presets[self.size_combo.currentIndex()][1]
        style = self.style_combo.currentText()
        transparent = self.transparent_cb.isChecked()
        margin = self.margin_slider.value()

        img = self._try_generate(qr_data, ec_level, version, output_dim, style, transparent, margin)
        if img is None:
            return

        # Logo overlay
        if self.logo_img:
            img = add_logo_with_border(
                img, self.logo_img,
                logo_size_pct=self.logo_size_slider.value(),
                border=self.logo_border_cb.isChecked(),
                border_color=self.logo_border_color,
                border_thickness=self.logo_border_slider.value(),
            )

        # Store full-res image
        buf = BytesIO()
        img.save(buf, format="PNG")
        self.qr_img_bytes = buf.getvalue()
        self.qr_img = img

        self._update_preview()
        self._enable_export()
        self._set_status("", error=False)

    def _try_generate(self, qr_data, ec_level, version, output_dim, style, transparent, margin, _depth=0):
        if _depth > 38:
            self._set_status("Data too large to encode into a QR code.")
            self._disable_export()
            return None
        try:
            qr = segno.make(qr_data, error=ec_level, version=version, micro=False)
            symbol_w = qr.symbol_size(1)[0]
            scale = max(1, output_dim // symbol_w)

            buf = BytesIO()

            if style == "Dot (PIL)":
                qr.save(buf, kind="png", scale=scale, dark=self.fg_color, light="white", border=margin)
                buf.seek(0)
                img = Image.open(buf).convert("RGBA")
                module_px = qr.symbol_size(scale)[0] // qr.symbol_size(1)[0]
                img = self._render_dots(img, module_px)
            else:
                # Square (default segno renderer)
                save_kw: dict = dict(kind="png", scale=scale, dark=self.fg_color, border=margin)
                if transparent:
                    save_kw["light"] = None
                else:
                    save_kw["light"] = self.bg_color
                if self.finder_color:
                    save_kw["finder_dark"] = self.finder_color
                qr.save(buf, **save_kw)
                buf.seek(0)
                img = Image.open(buf).convert("RGBA")

            if transparent:
                data = img.getdata()
                img.putdata([
                    (r, g, b, 0) if (r > 240 and g > 240 and b > 240) else (r, g, b, a)
                    for r, g, b, a in data
                ])

            if img.size[0] != output_dim:
                img = img.resize((output_dim, output_dim), Image.LANCZOS)

            # Gradient overlays
            use_fg_grad = self.grad_fg_cb.isChecked()
            use_bg_grad = self.grad_bg_cb.isChecked()
            c1, c2 = self.gradient_color1, self.gradient_color2

            if use_fg_grad:
                bg_rgba = ImageColor.getrgb(self.bg_color) + (255,) if not transparent else (0, 0, 0, 0)
                bg_layer = Image.new("RGBA", img.size, bg_rgba)
                fg_grad = apply_linear_gradient(img, c1, c2)
                mask = img.split()[3]
                img = Image.composite(fg_grad, bg_layer, mask)
            elif use_bg_grad:
                bg_grad = Image.new("RGBA", img.size, (0, 0, 0, 0))
                bg_grad = apply_linear_gradient(bg_grad, c1, c2)
                img = Image.alpha_composite(bg_grad, img)

            return img

        except Exception as e:
            msg = str(e)
            if "does not fit into version" in msg and version < 40:
                self.version_slider.blockSignals(True)
                self.version_slider.setValue(version + 1)
                self.version_val.setText(str(version + 1))
                self.version_slider.blockSignals(False)
                return self._try_generate(qr_data, ec_level, version + 1, output_dim, style, transparent, margin, _depth + 1)
            self._set_status(f"Error: {msg}")
            self._disable_export()
            return None

    def _render_dots(self, img: Image.Image, module_px: int) -> Image.Image:
        dot_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(dot_img)
        px = img.load()
        w, h = img.size
        m = max(module_px, 1)
        r = max(int(m * 0.42), 1)
        for y in range(0, h, m):
            for x in range(0, w, m):
                pixel = px[x, y]
                if pixel[3] > 0 and pixel[:3] != (255, 255, 255):
                    cx, cy = x + m // 2, y + m // 2
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pixel)
        return dot_img

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self):
        box = self.qr_label.size()
        checker = _make_checkerboard(box)
        qimg = QImage.fromData(self.qr_img_bytes)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(box, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        painter = QPainter(checker)
        x = (box.width() - scaled.width()) // 2
        y = (box.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        self.qr_label.setPixmap(checker)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.qr_img_bytes:
            self._update_preview()

    # ------------------------------------------------------------------
    # Export actions
    # ------------------------------------------------------------------

    def save_qr(self):
        if not self.qr_img:
            return
        ver = self.version_slider.value()
        default = f"QR_V{ver:02d}.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save QR Code", default, "PNG Files (*.png)")
        if path:
            self.qr_img.save(path)

    def copy_qr_to_clipboard(self):
        if self.qr_img_bytes:
            QApplication.instance().clipboard().setImage(QImage.fromData(self.qr_img_bytes))

    def export_svg(self):
        raw = self._get_raw_input()
        if not raw:
            return
        qr_data = self._format_qr_data(self.type_combo.currentText(), raw)
        ec_letters = ["L", "M", "Q", "H"]
        ec_level = ec_letters[self.ec_combo.currentIndex()]
        version = self.version_slider.value()
        output_dim = self.size_presets[self.size_combo.currentIndex()][1]

        ver = self.version_slider.value()
        default = f"QR_V{ver:02d}.svg"
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", default, "SVG Files (*.svg)")
        if not path:
            return
        try:
            qr = segno.make(qr_data, error=ec_level, version=version, micro=False)
            scale = max(1, output_dim // qr.symbol_size(1)[0])
            qr.save(path, scale=scale, dark=self.fg_color, light=self.bg_color)
        except Exception as e:
            self._set_status(f"SVG export error: {e}")

    # ------------------------------------------------------------------
    # Full-preview dialog
    # ------------------------------------------------------------------

    def _preview_click(self, event):
        if not self.qr_img_bytes:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("QR Preview")
        dialog.setStyleSheet("background-color: #1e1e2e;")
        vbox = QVBoxLayout(dialog)
        label = QLabel()
        qimg = QImage.fromData(self.qr_img_bytes)
        pixmap = QPixmap.fromImage(qimg)
        screen = QApplication.primaryScreen().availableGeometry()
        max_w = min(screen.width() - 80, 1200)
        max_h = min(screen.height() - 120, 1200)
        if pixmap.width() > max_w or pixmap.height() > max_h:
            pixmap = pixmap.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(label)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        vbox.addWidget(close_btn)
        dialog.resize(pixmap.width() + 40, pixmap.height() + 80)
        dialog.exec()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        copy_act = menu.addAction("Copy QR to Clipboard")
        save_act = menu.addAction("Save PNG…")
        act = menu.exec(self.qr_label.mapToGlobal(pos))
        if act == copy_act:
            self.copy_qr_to_clipboard()
        elif act == save_act:
            self.save_qr()

    # ------------------------------------------------------------------
    # Color pickers
    # ------------------------------------------------------------------

    def _pick_color(self, current: str) -> str | None:
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(current), self)
        return color.name() if color.isValid() else None

    def _pick_fg(self):
        c = self._pick_color(self.fg_color)
        if c:
            self.fg_color = c
            self.fg_btn.setStyleSheet(_swatch_style(c))
            self.generate_qr()

    def _pick_bg(self):
        c = self._pick_color(self.bg_color)
        if c:
            self.bg_color = c
            self.bg_btn.setStyleSheet(_swatch_style(c))
            self.generate_qr()

    def _pick_finder(self):
        c = self._pick_color(self.finder_color or "#000000")
        if c:
            self.finder_color = c
            self.finder_btn.setStyleSheet(_swatch_style(c))
            self.generate_qr()

    def _clear_finder(self):
        self.finder_color = None
        self.finder_btn.setStyleSheet(_swatch_style("#000000"))
        self.generate_qr()

    def _pick_gc1(self):
        c = self._pick_color(self.gradient_color1)
        if c:
            self.gradient_color1 = c
            self.gc1_btn.setStyleSheet(_swatch_style(c))
            self.generate_qr()

    def _pick_gc2(self):
        c = self._pick_color(self.gradient_color2)
        if c:
            self.gradient_color2 = c
            self.gc2_btn.setStyleSheet(_swatch_style(c))
            self.generate_qr()

    def _pick_logo_border_color(self):
        c = self._pick_color(self.logo_border_color)
        if c:
            self.logo_border_color = c
            self.logo_border_color_btn.setStyleSheet(_swatch_style(c))
            self.generate_qr()

    # ------------------------------------------------------------------
    # File / logo loaders
    # ------------------------------------------------------------------

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            t = self.type_combo.currentText()
            if t == "Plain Text":
                self.text_edit.setPlainText(content)
            else:
                self.url_input.setText(content)
        except Exception as e:
            self._set_status(f"File error: {e}")

    def _browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf);;All Files (*)")
        if path:
            self.pdf_path.setText(path)

    def _load_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Logo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)")
        if path:
            self.logo_img = Image.open(path)
            self.logo_name_label.setText(path.split("/")[-1].split("\\")[-1])
            self.logo_name_label.setStyleSheet("color: #f8f8f2; font-size: 11px;")
            self.generate_qr()

    def _clear_logo(self):
        self.logo_img = None
        self.logo_name_label.setText("No logo")
        self.logo_name_label.setStyleSheet("color: #6272a4; font-size: 11px;")
        self.generate_qr()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg: str, error: bool = True):
        self.status_label.setStyleSheet("color: #ff5555;" if error else "color: #6272a4;")
        self.status_label.setText(msg)

    def _enable_export(self):
        for btn in (self.save_btn, self.copy_btn, self.svg_btn):
            btn.setEnabled(True)

    def _disable_export(self):
        for btn in (self.save_btn, self.copy_btn, self.svg_btn):
            btn.setEnabled(False)

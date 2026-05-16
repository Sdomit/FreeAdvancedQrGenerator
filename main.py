import sys
from PyQt6.QtWidgets import QApplication
from qr_generator import QRGenerator, STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = QRGenerator()
    window.setMinimumSize(1100, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

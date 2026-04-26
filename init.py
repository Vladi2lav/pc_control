"""init.py — Точка входа приложения Control."""

import sys
from pathlib import Path

# Добавляем корень в путь
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from components.UI import GlassWindow
from modules.db_explorer import DBExplorerModule


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GlassWindow("Control")
    window._mount(DBExplorerModule, icon="🗄️", name="DB")
    window.show()

    sys.exit(app.exec())
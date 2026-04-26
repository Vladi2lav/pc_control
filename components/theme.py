"""
Theme helpers for Control.
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


def build_stylesheet(theme: str = "dark") -> str:
    if theme == "light":
        return """
        * {
            font-family: "Segoe UI";
            color: #2f3a4a;
            background: transparent;
        }
        QWidget[glass="true"] {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(117, 129, 148, 0.24);
            border-radius: 16px;
        }
        QLabel {
            color: #2f3a4a;
            font-size: 12px;
        }
        QLabel[style_="title"] {
            color: #1f2633;
            font-weight: 600;
            font-size: 14px;
        }
        QLabel[style_="muted"] {
            color: #6f7a8e;
        }
        QLabel[style_="accent"] {
            color: #245ea8;
        }
        QPushButton, QToolButton {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(117, 129, 148, 0.36);
            border-radius: 8px;
            min-height: 24px;
            padding: 4px 10px;
        }
        QPushButton:hover, QToolButton:hover {
            background: rgba(245, 249, 255, 0.98);
            border-color: rgba(36, 94, 168, 0.52);
        }
        QPushButton:checked {
            background: rgba(36, 94, 168, 0.18);
            border-color: rgba(36, 94, 168, 0.64);
        }
        QPushButton[style_="accent"], QToolButton[style_="accent"] {
            background: rgba(36, 94, 168, 0.16);
            border-color: rgba(36, 94, 168, 0.44);
            color: #245ea8;
        }
        QLineEdit, QTextEdit, QListWidget, QTreeWidget, QComboBox, QPlainTextEdit, QTabWidget::pane {
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(117, 129, 148, 0.34);
            border-radius: 8px;
            color: #2f3a4a;
            padding: 4px 8px;
        }
        QTabBar::tab {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(117, 129, 148, 0.30);
            border-bottom: none;
            padding: 5px 10px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: rgba(245, 249, 255, 1.0);
            color: #1f2633;
        }
        QListWidget::item:selected, QTreeWidget::item:selected {
            background: rgba(36, 94, 168, 0.20);
            color: #1f2633;
        }
        """

    return """
    * {
        font-family: "Segoe UI";
        color: #dbe7ff;
        background: transparent;
    }
    QWidget[glass="true"] {
        background: rgba(16, 22, 34, 0.90);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
    }
    QLabel {
        color: #dbe7ff;
        font-size: 12px;
    }
    QLabel[style_="title"] {
        color: #ffffff;
        font-weight: 600;
        font-size: 14px;
    }
    QLabel[style_="muted"] {
        color: #93a4c5;
    }
    QLabel[style_="accent"] {
        color: #8ec5ff;
    }
    QPushButton, QToolButton {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.20);
        border-radius: 8px;
        min-height: 24px;
        padding: 4px 10px;
    }
    QPushButton:hover, QToolButton:hover {
        background: rgba(255, 255, 255, 0.14);
        border-color: rgba(142, 197, 255, 0.52);
    }
    QPushButton:checked {
        background: rgba(142, 197, 255, 0.22);
        border-color: rgba(142, 197, 255, 0.72);
    }
    QPushButton[style_="accent"], QToolButton[style_="accent"] {
        background: rgba(142, 197, 255, 0.18);
        border-color: rgba(142, 197, 255, 0.42);
        color: #a8d4ff;
    }
    QLineEdit, QTextEdit, QListWidget, QTreeWidget, QComboBox, QPlainTextEdit, QTabWidget::pane {
        background: rgba(9, 14, 24, 0.94);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 8px;
        color: #dbe7ff;
        padding: 4px 8px;
    }
    QTabBar::tab {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-bottom: none;
        padding: 5px 10px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: rgba(142, 197, 255, 0.18);
        color: #ffffff;
    }
    QListWidget::item:selected, QTreeWidget::item:selected {
        background: rgba(142, 197, 255, 0.20);
        color: #ffffff;
    }
    """


def apply_theme(app: QApplication, theme: str) -> str:
    app.setStyleSheet(build_stylesheet(theme))
    return theme

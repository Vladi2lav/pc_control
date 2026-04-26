"""UIBase.py — XML-to-PySide6 движок. Документация: docs/UIBase.md"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QSpacerItem, QSizePolicy, QFrame,
    QScrollArea, QCheckBox, QProgressBar, QStackedWidget,
    QLayout,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont, QColor, QPalette


# ─── Палитра и стили Dark Glass ───────────────────────────────────────────────

GLASS_STYLESHEET = """
/* ═══════════════════════════════════════════════
   Dark Glass — UIBase stylesheet
   ═══════════════════════════════════════════════ */

* {
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    color: #E8EAF0;
    selection-background-color: rgba(100, 160, 255, 0.35);
}

/* ── Базовый фон панели ─────────────────────── */
QWidget[glass="true"] {
    background: rgba(18, 20, 30, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

/* ── Метки ──────────────────────────────────── */
QLabel {
    background: transparent;
    color: #D0D4E8;
    font-size: 13px;
}
QLabel[style_="title"] {
    font-size: 16px;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: 0.5px;
}
QLabel[style_="muted"] {
    color: rgba(180, 185, 210, 0.55);
    font-size: 12px;
}
QLabel[style_="accent"] {
    color: #7EB8F7;
    font-size: 13px;
}
QLabel[style_="danger"] {
    color: #F78080;
}

/* ── Кнопки ─────────────────────────────────── */
QPushButton {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    color: #D0D4E8;
    font-size: 13px;
    padding: 7px 18px;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 0.13);
    border-color: rgba(255, 255, 255, 0.20);
    color: #FFFFFF;
}
QPushButton:pressed {
    background: rgba(255, 255, 255, 0.05);
}
QPushButton[style_="accent"] {
    background: rgba(100, 160, 255, 0.18);
    border-color: rgba(100, 160, 255, 0.35);
    color: #7EB8F7;
}
QPushButton[style_="accent"]:hover {
    background: rgba(100, 160, 255, 0.30);
    color: #C2DCFF;
}
QPushButton[style_="danger"] {
    background: rgba(220, 60, 60, 0.15);
    border-color: rgba(220, 60, 60, 0.30);
    color: #F78080;
}
QPushButton[style_="danger"]:hover {
    background: rgba(220, 60, 60, 0.28);
    color: #FFAAAA;
}
QPushButton[style_="close"] {
    background: transparent;
    border: none;
    color: rgba(180, 185, 210, 0.55);
    font-size: 15px;
    padding: 4px 8px;
    border-radius: 8px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
QPushButton[style_="close"]:hover {
    background: rgba(220, 60, 60, 0.22);
    color: #FF8080;
}

/* ── Поля ввода ─────────────────────────────── */
QLineEdit, QTextEdit {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 8px;
    color: #D0D4E8;
    font-size: 13px;
    padding: 6px 10px;
    selection-background-color: rgba(100, 160, 255, 0.30);
}
QLineEdit:focus, QTextEdit:focus {
    border-color: rgba(100, 160, 255, 0.45);
    background: rgba(100, 160, 255, 0.06);
}
QLineEdit::placeholder {
    color: rgba(180, 185, 210, 0.35);
}

/* ── Чекбокс ────────────────────────────────── */
QCheckBox {
    spacing: 8px;
    color: #D0D4E8;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 5px;
    background: rgba(255,255,255,0.05);
}
QCheckBox::indicator:checked {
    background: rgba(100, 160, 255, 0.55);
    border-color: rgba(100, 160, 255, 0.70);
}

/* ── Прогресс-бар ───────────────────────────── */
QProgressBar {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #4A90D9, stop:1 #7EB8F7
    );
    border-radius: 6px;
}

/* ── Разделитель ────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    background: rgba(255,255,255,0.07);
    border: none;
    max-height: 1px;
}

/* ── Прокрутка ──────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.18);
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
}
QScrollBar::handle:horizontal {
    background: rgba(255,255,255,0.18);
    border-radius: 3px;
}
"""


# ─── Компоненты ───────────────────────────────────────────────────────────────

def _apply_style(widget: QWidget, style: Optional[str]) -> None:
    """Устанавливает кастомный style_ property для CSS селектора."""
    if style:
        widget.setProperty("style_", style)
        widget.style().unpolish(widget)
        widget.style().polish(widget)


def _int(attrs: dict, key: str, default: int = 0) -> int:
    return int(attrs.get(key, default))


def _bool_attr(attrs: dict, key: str, default: bool = False) -> bool:
    v = attrs.get(key, "")
    return v.lower() in ("true", "1", "yes") if v else default


class GlassLabel(QLabel):
    """Метка с поддержкой glass-стилей."""
    def __init__(self, text: str = "", style: Optional[str] = None, **kwargs):
        super().__init__(text, **kwargs)
        _apply_style(self, style)


class GlassButton(QPushButton):
    """Кнопка с glass-стилем и анимацией нажатия."""
    def __init__(self, text: str = "", style: Optional[str] = None, **kwargs):
        super().__init__(text, **kwargs)
        _apply_style(self, style)


class GlassInput(QLineEdit):
    """Поле ввода с glass-стилем."""
    def __init__(self, placeholder: str = "", style: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.setPlaceholderText(placeholder)
        _apply_style(self, style)


class GlassTextArea(QTextEdit):
    """Многострочное поле с glass-стилем."""
    def __init__(self, style: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        _apply_style(self, style)


class GlassCheckBox(QCheckBox):
    """Чекбокс с glass-стилем."""
    def __init__(self, text: str = "", style: Optional[str] = None, **kwargs):
        super().__init__(text, **kwargs)
        _apply_style(self, style)


class GlassProgressBar(QProgressBar):
    """Прогресс-бар с glass-стилем."""
    def __init__(self, value: int = 0, minimum: int = 0, maximum: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.setRange(minimum, maximum)
        self.setValue(value)


class GlassSeparator(QFrame):
    """Горизонтальный разделитель."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class GlassPanel(QWidget):
    """Контейнер-панель с glass-эффектом."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setProperty("glass", "true")


# ─── Рендерер XML → Виджеты ──────────────────────────────────────────────────

class UIRenderer:
    """
    Парсит XML и создаёт иерархию PySide6 виджетов.

    Поддерживаемые теги:
        Window, VBox, HBox, Label, Button, Input,
        TextArea, CheckBox, ProgressBar, Spacer, Separator, Panel, Stack
    """

    def __init__(self) -> None:
        self._refs: Dict[str, QWidget] = {}

    # ── Публичный API ─────────────────────────────────────────────────────────

    def load_file(
        self, xml_path: str
    ) -> Tuple[QWidget, Dict[str, QWidget]]:
        """Загружает XML из файла и рендерит виджет."""
        tree = ET.parse(xml_path)
        return self._render_root(tree.getroot())

    def load_string(
        self, xml_string: str
    ) -> Tuple[QWidget, Dict[str, QWidget]]:
        """Загружает XML из строки и рендерит виджет."""
        root = ET.fromstring(xml_string)
        return self._render_root(root)

    # ── Приватные методы ──────────────────────────────────────────────────────

    def _render_root(
        self, root: ET.Element
    ) -> Tuple[QWidget, Dict[str, QWidget]]:
        self._refs = {}
        widget = self._build(root)
        # Применяем общий стилишит
        widget.setStyleSheet(GLASS_STYLESHEET)
        return widget, self._refs

    def _build(self, elem: ET.Element, parent: Optional[QWidget] = None) -> QWidget:
        tag = elem.tag.strip()
        attrs = {k: v for k, v in elem.attrib.items()}
        widget = self._create_widget(tag, attrs, parent)

        # Регистрируем ref
        if "id" in attrs:
            self._refs[attrs["id"]] = widget

        # Рекурсивно строим дочерние
        layout = widget.layout() if isinstance(widget, QWidget) else None
        for child_elem in elem:
            child = self._build(child_elem, widget)
            if layout is not None:
                self._add_to_layout(layout, child, child_elem.attrib)

        return widget

    def _create_widget(
        self, tag: str, attrs: dict, parent: Optional[QWidget]
    ) -> QWidget:
        style   = attrs.get("style")
        text    = attrs.get("text", "")
        tooltip = attrs.get("tooltip")

        w: QWidget

        if tag in ("Window", "VBox", "Panel"):
            w = GlassPanel(parent=parent)
            layout = QVBoxLayout(w)
            layout.setSpacing(_int(attrs, "spacing", 8))
            layout.setContentsMargins(*self._parse_padding(attrs.get("padding", "12")))
            if tag == "Window":
                w.setWindowTitle(attrs.get("title", ""))
                if "width" in attrs or "height" in attrs:
                    w.resize(_int(attrs, "width", 400), _int(attrs, "height", 300))

        elif tag == "HBox":
            w = GlassPanel(parent=parent)
            layout = QHBoxLayout(w)
            layout.setSpacing(_int(attrs, "spacing", 8))
            layout.setContentsMargins(*self._parse_padding(attrs.get("padding", "0")))

        elif tag == "Label":
            w = GlassLabel(text=text, style=style, parent=parent)
            if "align" in attrs:
                w.setAlignment(self._parse_align(attrs["align"]))  # type: ignore[attr-defined]

        elif tag == "Button":
            w = GlassButton(text=text, style=style, parent=parent)

        elif tag == "Input":
            w = GlassInput(
                placeholder=attrs.get("placeholder", ""),
                style=style,
                parent=parent,
            )
            if text:
                w.setText(text)

        elif tag == "TextArea":
            w = GlassTextArea(style=style, parent=parent)
            if text:
                w.setPlainText(text)

        elif tag == "CheckBox":
            w = GlassCheckBox(text=text, style=style, parent=parent)
            if _bool_attr(attrs, "checked"):
                w.setChecked(True)

        elif tag == "ProgressBar":
            w = GlassProgressBar(
                value=_int(attrs, "value", 0),
                minimum=_int(attrs, "min", 0),
                maximum=_int(attrs, "max", 100),
                parent=parent,
            )

        elif tag == "Separator":
            w = GlassSeparator(parent=parent)

        elif tag == "Spacer":
            # Spacer реализуем через пустой виджет
            w = QWidget(parent=parent)
            w.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

        elif tag == "Stack":
            w = QStackedWidget(parent=parent)

        elif tag == "Scroll":
            scroll = QScrollArea(parent=parent)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            inner = GlassPanel()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setSpacing(_int(attrs, "spacing", 8))
            inner_layout.setContentsMargins(
                *self._parse_padding(attrs.get("padding", "8"))
            )
            scroll.setWidget(inner)
            # Дочерние будем добавлять в inner_layout
            scroll._inner_layout = inner_layout  # type: ignore[attr-defined]
            w = scroll  # type: ignore[assignment]

        else:
            # Неизвестный тег — пустая панель-заглушка
            w = QWidget(parent=parent)

        # Общие атрибуты
        if tooltip:
            w.setToolTip(tooltip)
        if "min_width" in attrs:
            w.setMinimumWidth(_int(attrs, "min_width"))
        if "max_width" in attrs:
            w.setMaximumWidth(_int(attrs, "max_width"))
        if "min_height" in attrs:
            w.setMinimumHeight(_int(attrs, "min_height"))
        if "max_height" in attrs:
            w.setMaximumHeight(_int(attrs, "max_height"))
        if _bool_attr(attrs, "hidden"):
            w.hide()
        if _bool_attr(attrs, "disabled"):
            w.setEnabled(False)

        return w

    def _add_to_layout(
        self, layout: QLayout, child: QWidget, attrs: dict
    ) -> None:
        if isinstance(layout, (QVBoxLayout, QHBoxLayout)):
            stretch = _int(attrs, "stretch", 0)
            align_str = attrs.get("align")
            if align_str:
                align = self._parse_align(align_str)
                layout.addWidget(child, stretch, align)
            else:
                layout.addWidget(child, stretch)
        else:
            layout.addWidget(child)

    @staticmethod
    def _parse_padding(value: str) -> Tuple[int, int, int, int]:
        """'12' → (12,12,12,12), '8,16' → (8,16,8,16), '8,16,8,16' → (8,16,8,16)"""
        parts = [int(x.strip()) for x in value.split(",")]
        if len(parts) == 1:
            return (parts[0],) * 4
        if len(parts) == 2:
            return (parts[0], parts[1], parts[0], parts[1])
        if len(parts) == 4:
            return tuple(parts)  # type: ignore[return-value]
        return (0, 0, 0, 0)

    @staticmethod
    def _parse_align(align: str) -> Qt.AlignmentFlag:
        mapping = {
            "left":   Qt.AlignmentFlag.AlignLeft,
            "right":  Qt.AlignmentFlag.AlignRight,
            "center": Qt.AlignmentFlag.AlignCenter,
            "top":    Qt.AlignmentFlag.AlignTop,
            "bottom": Qt.AlignmentFlag.AlignBottom,
        }
        return mapping.get(align.lower(), Qt.AlignmentFlag.AlignLeft)
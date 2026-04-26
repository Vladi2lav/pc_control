"""
Main application window.
"""

from __future__ import annotations

import logging
from enum import Enum

from PySide6.QtCore import QEvent, QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from components.CORE import core


logger = logging.getLogger("ui")

SNAP_THRESHOLD = 40
RESIZE_MARGIN = 8


class MenuMode(Enum):
    STANDARD = 1
    COMPACT = 2
    SIDE_THIN = 3
    SIDE_OPEN = 4


class TitleBar(QWidget):
    def __init__(self, title: str, on_close, on_minimize, on_mode, on_configure, on_drag_start, on_drag_move, on_drag_end, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._on_drag_start = on_drag_start
        self._on_drag_move = on_drag_move
        self._on_drag_end = on_drag_end
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        badge = QLabel("Control")
        badge.setProperty("style_", "title")
        layout.addWidget(badge)

        subtitle = QLabel(title)
        subtitle.setProperty("style_", "muted")
        self.subtitle = subtitle
        layout.addWidget(subtitle)
        layout.addStretch(1)

        self.config_button = self._make_button("CFG", on_configure, accent=False)
        self.mode_button = self._make_button("MODE", on_mode, accent=False)
        self.min_button = self._make_button("_", on_minimize, accent=False)
        self.close_button = self._make_button("X", on_close, accent=False)

        layout.addWidget(self.config_button)
        layout.addWidget(self.mode_button)
        layout.addWidget(self.min_button)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_drag_start(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._on_drag_move(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_drag_end(event.globalPosition().toPoint())

    def _make_button(self, text: str, slot, accent: bool) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(42, 30)
        if accent:
            button.setProperty("style_", "accent")
        button.clicked.connect(slot)
        return button

    def update_mode_icon(self, mode: MenuMode) -> None:
        titles = {
            MenuMode.STANDARD: "WINDOW",
            MenuMode.COMPACT: "COMPACT",
            MenuMode.SIDE_THIN: "PIN",
            MenuMode.SIDE_OPEN: "DOCK",
        }
        self.mode_button.setText(titles.get(mode, "MODE"))


class ModuleButton(QPushButton):
    def __init__(self, icon: str, name: str, on_click, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._name = name
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(on_click)
        self.setMinimumHeight(48)
        self.set_open_mode(False)

    def set_open_mode(self, open_mode: bool) -> None:
        if open_mode:
            self.setFixedSize(QSize(120, 62))
            self.setText(f"{self._icon}\n{self._name}")
            self.setStyleSheet(
                "QPushButton { text-align: left; padding: 8px 10px; font-size: 12px; border-radius: 8px; }"
            )
        else:
            self.setFixedSize(QSize(56, 56))
            self.setText(self._icon)
            self.setStyleSheet(
                "QPushButton { text-align: center; padding: 6px; font-size: 13px; border-radius: 8px; }"
            )


class SideBar(QWidget):
    THIN_W = 18
    OPEN_W = 136

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = MenuMode.STANDARD
        self._buttons: list[ModuleButton] = []
        self.setMouseTracking(True)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(8, 14, 8, 14)
        self.layout_.setSpacing(10)
        self.layout_.addStretch(1)
        self.hide()

    def add_button(self, icon: str, name: str, on_click) -> ModuleButton:
        button = ModuleButton(icon, name, on_click, self)
        self.layout_.insertWidget(self.layout_.count() - 1, button)
        self._buttons.append(button)
        return button

    def set_mode(self, mode: MenuMode) -> None:
        self._mode = mode
        visible = mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN)
        self.setVisible(visible)
        open_mode = mode == MenuMode.SIDE_OPEN
        self.setFixedWidth(self.OPEN_W if open_mode else self.THIN_W)
        for button in self._buttons:
            button.setVisible(open_mode)
            button.set_open_mode(open_mode)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)

        if self._mode == MenuMode.SIDE_THIN:
            painter.setPen(QPen(QColor(255, 255, 255, 24), 1))
            painter.setBrush(QColor(20, 28, 42, 220))
            painter.drawRoundedRect(rect, 8, 8)
            painter.setPen(QPen(QColor(145, 200, 255, 120), 2))
            painter.drawLine(rect.center().x(), 14, rect.center().x(), rect.bottom() - 14)
            return

        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        painter.setBrush(QColor(14, 22, 36, 214))
        painter.drawRoundedRect(rect, 12, 12)


class SnapPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(125, 204, 255, 84))
        gradient.setColorAt(1.0, QColor(125, 204, 255, 18))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(150, 220, 255, 120), 1))
        painter.drawRoundedRect(rect, 10, 10)


class ModulePopup(QWidget):
    def __init__(self, module_widget: QWidget, name: str, on_close, on_configure, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(560, 420)
        self._closing = False
        self._drag_offset: QPoint | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        self.card = QWidget()
        self.card.setProperty("glass", True)
        outer.addWidget(self.card)
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self._header = QWidget(self.card)
        self._header.setFixedHeight(32)
        header = QHBoxLayout(self._header)
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel(name)
        title.setProperty("style_", "title")
        title.installEventFilter(self)
        header.addWidget(title)
        header.addStretch(1)
        configure = QPushButton("cfg")
        configure.setFixedSize(34, 26)
        configure.clicked.connect(on_configure)
        close = QPushButton("x")
        close.setFixedSize(34, 26)
        close.clicked.connect(on_close)
        header.addWidget(configure)
        header.addWidget(close)
        layout.addWidget(self._header)
        self._header.installEventFilter(self)

        module_widget.setParent(self.card)
        module_widget.show()
        layout.addWidget(module_widget, 1)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.card.setGraphicsEffect(shadow)

    def eventFilter(self, watched, event):
        if watched in (self._header,) or watched.parent() is self._header:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self._drag_offset = None
                return True
        return super().eventFilter(watched, event)

    def show_with_animation(self) -> None:
        self.setWindowOpacity(0.0)
        super().show()
        opacity = QPropertyAnimation(self, b"windowOpacity", self)
        opacity.setDuration(170)
        opacity.setStartValue(0.0)
        opacity.setEndValue(1.0)
        opacity.setEasingCurve(QEasingCurve.Type.OutCubic)
        opacity.start()
        self._opacity_animation = opacity

        start_rect = QRect(self.x() + 24, self.y() + 16, max(480, self.width() - 40), max(360, self.height() - 30))
        end_rect = self.geometry()
        geometry = QPropertyAnimation(self, b"geometry", self)
        geometry.setDuration(190)
        geometry.setStartValue(start_rect)
        geometry.setEndValue(end_rect)
        geometry.setEasingCurve(QEasingCurve.Type.OutCubic)
        geometry.start()
        self._geometry_animation = geometry

    def close_with_animation(self, callback) -> None:
        if self._closing:
            return
        self._closing = True
        opacity = QPropertyAnimation(self, b"windowOpacity", self)
        opacity.setDuration(120)
        opacity.setStartValue(self.windowOpacity())
        opacity.setEndValue(0.0)
        opacity.setEasingCurve(QEasingCurve.Type.InCubic)
        opacity.finished.connect(callback)
        opacity.start()
        self._opacity_animation = opacity


class GlassWindow(QWidget):
    _MODE_SIZES = {
        MenuMode.STANDARD: (980, 720),
        MenuMode.COMPACT: (420, 220),
        MenuMode.SIDE_THIN: (SideBar.THIN_W, 420),
        MenuMode.SIDE_OPEN: (SideBar.OPEN_W, 420),
    }

    def __init__(self, title: str = "Control") -> None:
        super().__init__()
        self._title = title
        self._modules: list[dict] = []
        self._mode = MenuMode.STANDARD
        self._snapped: str | None = None
        self._drag_pos: QPoint | None = None
        self._closing = False
        self._resizing = False
        self._resize_edges: set[str] = set()
        self._start_geometry = QRect()
        self._start_pos = QPoint()
        self._current_preview_side = None
        self._preview_window: SnapPreview | None = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(720, 520)
        self.resize(*self._MODE_SIZES[MenuMode.STANDARD])

        self._build_ui()
        self._fade_in()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(0)

        self._glass = QWidget()
        self._glass.setProperty("glass", True)
        root.addWidget(self._glass)

        glass_layout = QVBoxLayout(self._glass)
        glass_layout.setContentsMargins(0, 0, 0, 0)
        glass_layout.setSpacing(0)

        self._titlebar = TitleBar(
            self._title,
            on_close=self._request_close,
            on_minimize=self.showMinimized,
            on_mode=self._cycle_mode,
            on_configure=lambda: core.call_api("app.open_configurator", context="app"),
            on_drag_start=self._start_window_drag,
            on_drag_move=self._move_window_drag,
            on_drag_end=self._end_window_drag,
            parent=self._glass,
        )
        glass_layout.addWidget(self._titlebar)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        glass_layout.addWidget(body, 1)

        self._sidebar = SideBar(body)
        body_layout.addWidget(self._sidebar)

        self._content = QWidget(body)
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(10, 0, 10, 10)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget(self._content)
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self._stack, 1)
        self._content_lay = content_layout
        body_layout.addWidget(self._content, 1)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self._glass.setGraphicsEffect(shadow)

    def _cycle_mode(self) -> None:
        order = [MenuMode.STANDARD, MenuMode.COMPACT, MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN]
        index = order.index(self._mode)
        self._apply_mode(order[(index + 1) % len(order)])

    def _apply_mode(self, mode: MenuMode) -> None:
        self._mode = mode
        self._titlebar.update_mode_icon(mode)
        width, height = self._MODE_SIZES[mode]
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else QRect(0, 0, width, height)

        if mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            self.setMinimumSize(width, 320)
            self._sidebar.set_mode(mode)
            self._content.setVisible(False)
            self._titlebar.setVisible(False)
            self._snap_to_side(self._snapped or "left", geometry, width)
            self.resize(width, geometry.height())
        else:
            self.setMinimumSize(720 if mode == MenuMode.STANDARD else 380, 520 if mode == MenuMode.STANDARD else 220)
            self._sidebar.set_mode(mode)
            self._content.setVisible(True)
            self._titlebar.setVisible(True)
            self._snapped = None
            new_width = width if mode == MenuMode.COMPACT else max(self.width(), width)
            new_height = height if mode == MenuMode.COMPACT else max(self.height(), height)
            self.resize(new_width, new_height)
            self.center()
            self._close_all_popups()

    def _snap_to_side(self, side: str, screen_geometry: QRect, width: int) -> None:
        self._snapped = side
        if side == "right":
            self.setGeometry(screen_geometry.right() - width + 1, screen_geometry.top(), width, screen_geometry.height())
        else:
            self.setGeometry(screen_geometry.left(), screen_geometry.top(), width, screen_geometry.height())

    def _mount(self, ModuleClass, icon: str = "[]", name: str = "Module", **kwargs):
        index = len(self._modules)
        instance = ModuleClass(core=core, parent=self._content, **kwargs)
        entry = {
            "instance": instance,
            "name": name,
            "icon": icon,
            "popup": None,
            "button": None,
        }
        button = self._sidebar.add_button(icon, name, lambda checked=False, i=index: self._toggle_module(i))
        entry["button"] = button
        self._modules.append(entry)
        self._stack.addWidget(instance.widget)
        if index == 0:
            self._stack.setCurrentIndex(0)
            button.setChecked(True)
        return instance

    def _toggle_module(self, index: int) -> None:
        if self._mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            entry = self._modules[index]
            if entry["popup"] is None:
                self._open_popup(index)
            else:
                self._close_popup(index)
            return

        self._stack.setCurrentIndex(index)
        for pos, entry in enumerate(self._modules):
            entry["button"].setChecked(pos == index)

    def _open_popup(self, index: int) -> None:
        self._close_all_popups()
        entry = self._modules[index]
        popup = ModulePopup(
            entry["instance"].widget,
            entry["name"],
            on_close=lambda i=index: self._close_popup(i),
            on_configure=entry["instance"].open_configurator,
        )
        popup.resize(760, 620)
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        screen_rect = screen.availableGeometry() if screen else QRect(0, 0, 1280, 720)
        if self._snapped == "right":
            x = max(screen_rect.left() + 30, self.x() - popup.width() - 12)
        else:
            x = min(screen_rect.right() - popup.width() - 30, self.x() + self.width() + 12)
        y = max(screen_rect.top() + 40, min(self.y() + 40, screen_rect.bottom() - popup.height() - 30))
        popup.move(x, y)
        popup.show_with_animation()
        entry["popup"] = popup
        entry["button"].setChecked(True)

    def _close_popup(self, index: int) -> None:
        entry = self._modules[index]
        popup = entry["popup"]
        if popup is None:
            return
        entry["instance"].widget.setParent(self._content)
        self._stack.insertWidget(index, entry["instance"].widget)
        def finish():
            popup.close()
            entry["popup"] = None
            entry["button"].setChecked(False)
        popup.close_with_animation(finish)

    def _close_all_popups(self) -> None:
        for index in range(len(self._modules)):
            self._close_popup(index)

    def _show_preview(self, rect: QRect) -> None:
        if self._preview_window is None:
            self._preview_window = SnapPreview()
        self._preview_window.setGeometry(rect)
        self._preview_window.show()

    def _hide_preview(self) -> None:
        if self._preview_window is not None:
            self._preview_window.hide()

    def _request_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._close_all_popups()
        for entry in self._modules:
            instance = entry["instance"]
            if hasattr(instance, "safe_close"):
                instance.safe_close()
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(160)
        animation.setStartValue(self.windowOpacity())
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(QApplication.instance().quit)
        animation.start()
        self._fade_animation = animation

    def _fade_in(self) -> None:
        self.setWindowOpacity(0.0)
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._fade_animation = animation

    def closeEvent(self, event) -> None:
        if self._closing:
            event.accept()
            return
        event.ignore()
        self._request_close()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._glass.geometry().adjusted(0, 0, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 22, 22)
        painter.setPen(QPen(QColor(255, 255, 255, 35), 1.2))
        painter.fillPath(path, QColor(18, 24, 36, 38))
        shine = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        shine.setColorAt(0.0, QColor(255, 255, 255, 26))
        shine.setColorAt(0.35, QColor(130, 210, 255, 10))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillPath(path, shine)
        painter.drawPath(path)

    def center(self) -> None:
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        if screen is None:
            return
        rect = screen.availableGeometry()
        self.move(rect.center() - QPoint(self.width() // 2, self.height() // 2))

    def _hit_test_edges(self, pos: QPoint) -> set[str]:
        rect = self.rect()
        edges: set[str] = set()
        if pos.x() <= RESIZE_MARGIN:
            edges.add("left")
        if pos.x() >= rect.width() - RESIZE_MARGIN:
            edges.add("right")
        if pos.y() <= RESIZE_MARGIN:
            edges.add("top")
        if pos.y() >= rect.height() - RESIZE_MARGIN:
            edges.add("bottom")
        return edges

    def _update_cursor(self, edges: set[str]) -> None:
        if {"left", "top"} == edges or {"right", "bottom"} == edges:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif {"right", "top"} == edges or {"left", "bottom"} == edges:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif "left" in edges or "right" in edges:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif "top" in edges or "bottom" in edges:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _start_window_drag(self, global_pos: QPoint) -> None:
        if self._mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            return
        self._drag_pos = global_pos - self.frameGeometry().topLeft()

    def _move_window_drag(self, global_pos: QPoint) -> None:
        if self._drag_pos is None:
            return
        self.move(global_pos - self._drag_pos)
        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            preview_width = int(screen_rect.width() * 0.1)
            if global_pos.x() <= screen_rect.left() + SNAP_THRESHOLD:
                self._show_preview(QRect(screen_rect.left(), screen_rect.top(), preview_width, screen_rect.height()))
                self._current_preview_side = "left"
            elif global_pos.x() >= screen_rect.right() - SNAP_THRESHOLD:
                self._show_preview(QRect(screen_rect.right() - preview_width, screen_rect.top(), preview_width, screen_rect.height()))
                self._current_preview_side = "right"
            else:
                self._hide_preview()
                self._current_preview_side = None

    def _end_window_drag(self, global_pos: QPoint) -> None:
        if self._drag_pos is None:
            return
        self._drag_pos = None
        if self._current_preview_side:
            screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
            if screen:
                self._apply_mode(MenuMode.SIDE_THIN)
                self._snap_to_side(self._current_preview_side, screen.availableGeometry(), self._MODE_SIZES[MenuMode.SIDE_THIN][0])
            self._current_preview_side = None
        self._hide_preview()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        global_pos = event.globalPosition().toPoint()
        edges = self._hit_test_edges(event.position().toPoint())
        if self._mode not in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN) and edges:
            self._resizing = True
            self._resize_edges = edges
            self._start_geometry = self.geometry()
            self._start_pos = global_pos
            return
        if event.position().y() <= 56:
            self._start_window_drag(global_pos)

    def mouseMoveEvent(self, event) -> None:
        global_pos = event.globalPosition().toPoint()
        if self._resizing:
            delta = global_pos - self._start_pos
            geometry = QRect(self._start_geometry)
            min_width = self.minimumWidth()
            min_height = self.minimumHeight()
            if "left" in self._resize_edges:
                new_left = min(geometry.right() - min_width, geometry.left() + delta.x())
                geometry.setLeft(new_left)
            if "right" in self._resize_edges:
                geometry.setRight(max(geometry.left() + min_width, geometry.right() + delta.x()))
            if "top" in self._resize_edges:
                new_top = min(geometry.bottom() - min_height, geometry.top() + delta.y())
                geometry.setTop(new_top)
            if "bottom" in self._resize_edges:
                geometry.setBottom(max(geometry.top() + min_height, geometry.bottom() + delta.y()))
            self.setGeometry(geometry)
            return

        if self._drag_pos is not None:
            self._move_window_drag(global_pos)
            return

        if self._mode == MenuMode.SIDE_THIN:
            local = self.mapFromGlobal(QCursor.pos())
            if local.x() <= int(self._sidebar.width() * 1.2):
                self._apply_mode(MenuMode.SIDE_OPEN)
        elif self._mode == MenuMode.SIDE_OPEN:
            local = self.mapFromGlobal(QCursor.pos())
            if local.x() > self._sidebar.width() + 24 and self._snapped:
                QTimer.singleShot(120, self._collapse_if_mouse_left)

        if self._mode not in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            self._update_cursor(self._hit_test_edges(event.position().toPoint()))

    def _collapse_if_mouse_left(self) -> None:
        if self._mode != MenuMode.SIDE_OPEN or not self._snapped:
            return
        local = self.mapFromGlobal(QCursor.pos())
        if local.x() > int(self._sidebar.width() * 1.2):
            self._apply_mode(MenuMode.SIDE_THIN)

    def mouseReleaseEvent(self, event) -> None:
        if self._resizing:
            self._resizing = False
            self._resize_edges = set()
            return
        if self._drag_pos is None:
            return
        self._end_window_drag(event.globalPosition().toPoint())

"""
UI.py — Главное окно. Документация: docs/UI.md
"""
import sys, logging
from enum import Enum
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGraphicsDropShadowEffect,
    QSizePolicy, QFrame, QScrollArea
)
from PySide6.QtCore import (
    Qt, QPoint, QPropertyAnimation, QEasingCurve,
    QRect, QTimer, QSize, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QPainterPath
)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from components.CORE import core
from components.UIBase import GLASS_STYLESHEET

logger = logging.getLogger("UI")
logging.basicConfig(level=logging.INFO)

SNAP_THRESHOLD = 40   # px от края — расстояние для магнита


class MenuMode(Enum):
    STANDARD   = 1   # обычный по центру
    COMPACT    = 2   # компактный по центру
    SIDE_THIN  = 3   # сбоку, закрытый (только иконки)
    SIDE_OPEN  = 4   # сбоку, открытый (иконки + названия)


# ── стили titlebar/sidebar ────────────────────────────────────────────────────

_BTN_BASE = """
QPushButton {{
    background: {bg};
    border: {border};
    border-radius: {r}px;
    color: {color};
    font-size: {fs}px;
    {extra}
}}
QPushButton:hover {{ background: {hbg}; color: {hcolor}; }}
QPushButton:pressed {{ background: rgba(255,255,255,0.04); }}
"""

def _wbtn(bg="transparent", border="none", r=8, color="rgba(200,210,235,0.6)",
          fs=13, extra="", hbg="rgba(255,255,255,0.09)", hcolor="#fff"):
    return _BTN_BASE.format(bg=bg, border=border, r=r, color=color,
                             fs=fs, extra=extra, hbg=hbg, hcolor=hcolor)


# ── Кастомный titlebar ────────────────────────────────────────────────────────

class _TitleBar(QWidget):
    """Перетаскиваемый заголовок: лого · title · режим · свернуть · закрыть."""

    def __init__(self, title: str, on_close, on_minimize, on_mode, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background: rgba(10,12,22,0.0);
                border: none;
            }
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 8, 0)
        lay.setSpacing(6)

        # decorative dots
        dots = QLabel("⬤  ⬤  ⬤")
        dots.setStyleSheet("color: rgba(255,255,255,0.15); font-size: 8px; background:transparent;")
        lay.addWidget(dots)

        lay.addSpacing(6)

        # title
        self._lbl = QLabel(title)
        self._lbl.setStyleSheet(
            "color: rgba(215,225,245,0.85); font-size: 13px; "
            "font-weight:600; letter-spacing:0.4px; background:transparent;"
        )
        lay.addWidget(self._lbl)
        lay.addStretch()

        # mode toggle button
        self._mode_btn = QPushButton("⊞")
        self._mode_btn.setFixedSize(28, 28)
        self._mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mode_btn.setToolTip("Сменить режим меню")
        self._mode_btn.setStyleSheet(_wbtn(fs=14))
        self._mode_btn.clicked.connect(on_mode)
        lay.addWidget(self._mode_btn)

        # minimize
        btn_min = QPushButton("—")
        btn_min.setFixedSize(28, 28)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setToolTip("Свернуть")
        btn_min.setStyleSheet(_wbtn(fs=14))
        btn_min.clicked.connect(on_minimize)
        lay.addWidget(btn_min)

        # close
        btn_cls = QPushButton("✕")
        btn_cls.setFixedSize(28, 28)
        btn_cls.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cls.setToolTip("Закрыть")
        btn_cls.setStyleSheet(_wbtn(
            hbg="rgba(220,60,60,0.30)", hcolor="#FF9090", fs=14
        ))
        btn_cls.clicked.connect(on_close)
        lay.addWidget(btn_cls)

    def update_mode_icon(self, mode: MenuMode):
        icons = {
            MenuMode.STANDARD:  "⊞",
            MenuMode.COMPACT:   "⊡",
            MenuMode.SIDE_THIN: "◧",
            MenuMode.SIDE_OPEN: "▣",
        }
        self._mode_btn.setText(icons.get(mode, "⊞"))


# ── Кнопка модуля в сайдбаре ─────────────────────────────────────────────────

class _ModuleButton(QPushButton):
    """Квадратная кнопка модуля — иконка + имя (в SIDE_OPEN)."""

    _IDLE = """
        QPushButton {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 10px;
            color: rgba(190,200,230,0.7);
            font-size: 20px;
            text-align: center;
        }
        QPushButton:hover {
            background: rgba(100,160,255,0.18);
            border-color: rgba(100,160,255,0.40);
            color: #C2DCFF;
        }
        QPushButton:pressed { background: rgba(100,160,255,0.10); }
        QPushButton:checked {
            background: rgba(100,160,255,0.22);
            border-color: rgba(100,160,255,0.55);
            color: #7EB8F7;
        }
    """

    def __init__(self, icon: str, name: str, on_click, parent=None):
        super().__init__(icon, parent)
        self._icon = icon
        self._name = name
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(name)
        self.setFixedSize(48, 48)
        self.setStyleSheet(self._IDLE)
        self.clicked.connect(on_click)

    def set_open_mode(self, open_: bool):
        """В SIDE_OPEN режиме показываем иконку + мини-текст."""
        if open_:
            self.setFixedSize(64, 64)
            self.setText(f"{self._icon}\n{self._name[:6]}")
            self.setStyleSheet(self._IDLE + """
                QPushButton { font-size: 16px; padding: 4px; }
            """)
        else:
            self.setFixedSize(48, 48)
            self.setText(self._icon)
            self.setStyleSheet(self._IDLE)


# ── Сайдбар ───────────────────────────────────────────────────────────────────

class _SideBar(QWidget):
    """Вертикальная панель с кнопками модулей."""

    THIN_W = 14
    OPEN_W = 80

    def __init__(self, on_hover_enter, on_hover_leave, parent=None):
        super().__init__(parent)
        self._on_hover_enter = on_hover_enter
        self._on_hover_leave = on_hover_leave
        self._btns: list[_ModuleButton] = []
        self._mode = MenuMode.STANDARD
        self._snapped = None
        
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(6, 8, 6, 8)
        self._lay.setSpacing(6)
        self._lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.setFixedWidth(self.THIN_W)
        self.hide()

    def add_button(self, icon: str, name: str, on_click) -> _ModuleButton:
        btn = _ModuleButton(icon, name, on_click, self)
        self._btns.append(btn)
        self._lay.addWidget(btn)
        return btn

    def set_mode(self, mode: MenuMode, snapped: str | None = None, window_w: int = 0):
        self._mode = mode
        self._snapped = snapped
        visible = mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN)
        self.setVisible(visible)
        open_ = mode == MenuMode.SIDE_OPEN
        thin_ = mode == MenuMode.SIDE_THIN

        if thin_:
            self.setFixedWidth(self.THIN_W)
            for btn in self._btns:
                btn.hide()
        else:
            self.setFixedWidth(self.OPEN_W if open_ else self.THIN_W)
            for btn in self._btns:
                btn.show()
                btn.set_open_mode(open_)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self._mode == MenuMode.SIDE_THIN:
            # Collapsed pill against the wall
            radius = 6
            bg = QColor(20, 22, 32, 200)
            painter.setBrush(bg)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, w, h, radius, radius)

            # Edge glow
            edge_grad = QLinearGradient(0, 0, w, 0) if self._snapped == 'right' else QLinearGradient(w, 0, 0, 0)
            edge_grad.setColorAt(0.0, QColor(80, 140, 255, 0))
            edge_grad.setColorAt(1.0, QColor(80, 140, 255, 60))
            painter.setBrush(QBrush(edge_grad))
            painter.drawRoundedRect(0, 0, w, h, radius, radius)
            
            # Drag handle
            cx, cy = w // 2, h // 2
            alpha = 180
            for offset in (-7, 7):
                y = cy + offset
                grad = QLinearGradient(0, y, w, y)
                grad.setColorAt(0.0, QColor(255, 255, 255, 0))
                grad.setColorAt(0.3, QColor(160, 200, 255, alpha))
                grad.setColorAt(0.5, QColor(200, 220, 255, min(255, alpha + 40)))
                grad.setColorAt(0.7, QColor(160, 200, 255, alpha))
                grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                pen = QPen(QBrush(grad), 1.5)
                painter.setPen(pen)
                painter.drawLine(4, y, w - 4, y)

        elif self._mode == MenuMode.SIDE_OPEN:
            # Full glass panel
            from PySide6.QtCore import QRectF
            radius = 14
            bg_grad = QLinearGradient(0, 0, w, h)
            bg_grad.setColorAt(0.0, QColor(20, 22, 35, 210))
            bg_grad.setColorAt(1.0, QColor(12, 14, 24, 190))
            painter.setBrush(QBrush(bg_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(1, 1, w - 2, h - 2, radius, radius)

            shimmer = QLinearGradient(0, 0, w, 0)
            shimmer.setColorAt(0.0, QColor(255, 255, 255, 0))
            shimmer.setColorAt(0.3, QColor(255, 255, 255, 22))
            shimmer.setColorAt(0.7, QColor(255, 255, 255, 14))
            shimmer.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(shimmer))
            painter.drawRoundedRect(1, 1, w - 2, 40, radius, radius)

            border_grad = QLinearGradient(0, 0, 0, h)
            border_grad.setColorAt(0.0, QColor(255, 255, 255, 70))
            border_grad.setColorAt(0.5, QColor(255, 255, 255, 20))
            border_grad.setColorAt(1.0, QColor(255, 255, 255, 10))
            pen = QPen(QBrush(border_grad), 1.0)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), float(radius), float(radius))

            from PySide6.QtGui import QRadialGradient
            inner_glow = QRadialGradient(0, h // 2, h * 0.6)
            inner_glow.setColorAt(0.0, QColor(60, 120, 255, 18))
            inner_glow.setColorAt(1.0, QColor(60, 120, 255, 0))
            painter.setBrush(QBrush(inner_glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(1, 1, w - 2, h - 2, radius, radius)
        else:
            # Standard background
            painter.fillRect(self.rect(), QColor(8, 10, 20, 140))
            painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
            painter.drawLine(w - 1, 0, w - 1, h)

        painter.end()

    def uncheck_all(self):
        for b in self._btns:
            b.setChecked(False)


# ── Попап модуля ──────────────────────────────────────────────────────────────

class _ModulePopup(QWidget):
    """Всплывающее окно модуля рядом с сайдбаром (в SIDE режимах)."""

    def __init__(self, module_widget: QWidget, name: str, on_close, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(name)
        self.setMinimumSize(320, 200)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background: rgba(14,16,26,0.97);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.10);
            }
        """)
        outer.addWidget(card)

        vl = QVBoxLayout(card)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # mini titlebar
        tb = QWidget()
        tb.setFixedHeight(36)
        tb.setStyleSheet("background:transparent; border:none;")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(12, 0, 8, 0)
        lbl = QLabel(name)
        lbl.setStyleSheet("color:rgba(210,220,245,0.85); font-size:12px; font-weight:600; background:transparent;")
        tbl.addWidget(lbl)
        tbl.addStretch()
        cls = QPushButton("✕")
        cls.setFixedSize(24, 24)
        cls.setCursor(Qt.CursorShape.PointingHandCursor)
        cls.setStyleSheet(_wbtn(hbg="rgba(220,60,60,0.28)", hcolor="#FF9090", r=7, fs=12))
        cls.clicked.connect(on_close)
        tbl.addWidget(cls)
        vl.addWidget(tb)

        sep = QWidget(); sep.setFixedHeight(1)
        sep.setStyleSheet("background:rgba(255,255,255,0.07); border:none;")
        vl.addWidget(sep)

        module_widget.setParent(card)
        vl.addWidget(module_widget)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 140))
        card.setGraphicsEffect(shadow)


class _SnapPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, QColor(80, 140, 255, 60))
        grad.setColorAt(1.0, QColor(80, 140, 255, 10))
        painter.setBrush(QBrush(grad))
        painter.setPen(QColor(100, 160, 255, 100))
        painter.drawRoundedRect(1, 1, w - 2, h - 2, 8, 8)
        painter.end()


# ── GlassWindow ───────────────────────────────────────────────────────────────

class GlassWindow(QWidget):
    """
    Главное окно. Документация: docs/UI.md
    Модули: self._mount(ModuleClass, icon='🗄', name='DB Explorer')
    """

    # Геометрии по режимам (w, h)
    _MODE_SIZES = {
        MenuMode.STANDARD:  (560, 380),
        MenuMode.COMPACT:   (140, 100),
        MenuMode.SIDE_THIN: (14, 390),
        MenuMode.SIDE_OPEN: (130, 390),
    }

    def get_anim_width(self) -> int:
        return self.width()

    def set_anim_width(self, val: int):
        self.setFixedWidth(val)
        if self._snapped:
            screen = QApplication.screenAt(self.geometry().center()) or self.screen() or QApplication.primaryScreen()
            if screen:
                sr = screen.geometry()
                if self._snapped == 'right':
                    self.move(sr.right() - val + 1, self.y())
                elif self._snapped == 'left':
                    self.move(sr.left(), self.y())

    anim_width = Property(int, get_anim_width, set_anim_width)

    def __init__(self, title: str = "Control Panel") -> None:
        super().__init__()
        self._title   = title
        self._modules: list[dict] = []   # {instance, btn, popup, name}
        self._drag_pos: QPoint | None = None
        self._mode    = MenuMode.STANDARD
        self._snapped : str | None = None  # "left" | "right" | None
        self._preview_window = None
        self._current_preview_side = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet(GLASS_STYLESHEET)

        self._anim_width = QPropertyAnimation(self, b"anim_width")
        self._anim_width.setDuration(240)
        self._anim_width.setEasingCurve(QEasingCurve.Type.OutCubic)

        # outer (margins for shadow)
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(16, 16, 16, 16)
        self._outer_layout.setSpacing(0)

        # glass card
        self._glass = QWidget()
        self._glass.setObjectName("glass_root")
        self._outer_layout.addWidget(self._glass)

        gl = QVBoxLayout(self._glass)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(0)

        # titlebar
        self._titlebar = _TitleBar(
            title,
            on_close    = self._request_close,
            on_minimize = self.showMinimized,
            on_mode     = self._cycle_mode,
            parent      = self._glass
        )
        gl.addWidget(self._titlebar)

        sep = QWidget(); sep.setFixedHeight(1)
        sep.setStyleSheet("background:rgba(255,255,255,0.07); border:none;")
        self._titlebar_sep = sep
        gl.addWidget(self._titlebar_sep)

        # body row: sidebar + content
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)

        self._sidebar = _SideBar(
            on_hover_enter=self._on_sidebar_enter,
            on_hover_leave=self._on_sidebar_leave,
            parent=body
        )
        bl.addWidget(self._sidebar)

        self._content = QWidget()
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        self._content_lay.setSpacing(0)
        bl.addWidget(self._content)

        gl.addWidget(body)

        # shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40); shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self._glass.setGraphicsEffect(shadow)

        core.start()
        self.setWindowOpacity(0.0)
        self._fade_in()

    # ── Режимы меню ───────────────────────────────────────────────────────────

    def _cycle_mode(self):
        """Циклически переключает режимы: 1→2→3→4→1."""
        order = [MenuMode.STANDARD, MenuMode.COMPACT,
                 MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN]
        idx = order.index(self._mode)
        self._apply_mode(order[(idx + 1) % len(order)])

    def _on_sidebar_enter(self):
        if self._mode == MenuMode.SIDE_THIN:
            self._apply_mode(MenuMode.SIDE_OPEN)

    def _on_sidebar_leave(self):
        if self._mode == MenuMode.SIDE_OPEN:
            # Check if mouse is actually outside sidebar area (to avoid flickering)
            # Or just wait a bit? Let's switch back to thin if we were snapped
            if self._snapped:
                 self._apply_mode(MenuMode.SIDE_THIN)

    def enterEvent(self, event):
        if self._mode == MenuMode.SIDE_THIN:
            self._apply_mode(MenuMode.SIDE_OPEN)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._mode == MenuMode.SIDE_OPEN:
            if self._snapped:
                self._apply_mode(MenuMode.SIDE_THIN)
        super().leaveEvent(event)

    def _animate_width(self, target: int):
        if self.width() == target:
            return
        self._anim_width.stop()
        self._anim_width.setStartValue(self.width())
        self._anim_width.setEndValue(target)
        self._anim_width.start()

    def _apply_mode(self, mode: MenuMode):
        old_mode = self._mode
        self._mode = mode
        self._titlebar.update_mode_icon(mode)

        w, h = self._MODE_SIZES[mode]
        screen = QApplication.screenAt(self.geometry().center()) or self.screen() or QApplication.primaryScreen()
        sg = screen.geometry() if screen else None

        if mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            self._outer_layout.setContentsMargins(0, 0, 0, 0)
            self._content.hide()
            self._titlebar.hide()
            self._titlebar_sep.hide()
            self._glass.setStyleSheet("background: transparent; border: none;")
            
            target_h = sg.height() if sg else h
            
            # Start width for animation
            start_w = self.width()
            if old_mode not in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
                # When coming from floating, start animation from 80px
                start_w = self._MODE_SIZES[MenuMode.SIDE_OPEN][0]
            
            self._sidebar.set_mode(mode, self._snapped, w)
            
            if sg:
                if self._snapped == "right":
                    self.setGeometry(sg.right() - start_w + 1, sg.top(), start_w, target_h)
                else:
                    self.setGeometry(sg.left(), sg.top(), start_w, target_h)
            
            self._animate_width(w)

        else:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self._outer_layout.setContentsMargins(16, 16, 16, 16)
            self._content.show()
            self._titlebar.show()
            self._titlebar_sep.show()
            self._glass.setStyleSheet(GLASS_STYLESHEET)
            
            gl = self._glass.layout()
            gl.setAlignment(self._titlebar, Qt.AlignmentFlag(0))
            gl.setAlignment(self._titlebar_sep, Qt.AlignmentFlag(0))
            self._titlebar.setMinimumWidth(0)
            self._titlebar.setMaximumWidth(16777215)
            self._titlebar_sep.setMinimumWidth(0)
            self._titlebar_sep.setMaximumWidth(16777215)
            
            self._sidebar.set_mode(mode, self._snapped, w)
            
            cx = self.x() + self.width() // 2
            cy = self.y() + self.height() // 2
            new_x = cx - w // 2
            new_y = cy - h // 2
            if sg:
                new_x = max(sg.left(), min(new_x, sg.right() - w))
                new_y = max(sg.top(), min(new_y, sg.bottom() - h))
            self.setGeometry(new_x, new_y, w, h)
            self._snapped = None

        if mode not in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            self._close_all_popups()

    # ── Монтирование модулей ──────────────────────────────────────────────────

    def _mount(self, ModuleClass, icon: str = "⬡", name: str = "Module", **kwargs):
        """Регистрирует модуль в сайдбаре и content area."""
        idx = len(self._modules)

        entry = {"instance": None, "btn": None, "popup": None, "name": name, "icon": icon}
        self._modules.append(entry)

        btn = self._sidebar.add_button(icon, name, lambda checked, i=idx: self._toggle_module(i))
        entry["btn"] = btn

        # создаём экземпляр модуля
        instance = ModuleClass(core=core, parent=self._content, **kwargs)
        entry["instance"] = instance

        # в STANDARD/COMPACT — просто монтируем в content
        self._content_lay.addWidget(instance.widget)
        instance.widget.setVisible(idx == 0)  # первый виден

        return instance

    def _toggle_module(self, idx: int):
        entry = self._modules[idx]
        btn = entry["btn"]

        if self._mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
            # попап рядом с панелью
            if entry["popup"] is not None:
                self._close_popup(idx)
                return
            self._open_popup(idx)
        else:
            # в обычных режимах переключаем видимость в content
            for i, e in enumerate(self._modules):
                e["instance"].widget.setVisible(i == idx)
                if e["btn"]:
                    e["btn"].setChecked(i == idx)

    def _open_popup(self, idx: int):
        self._close_all_popups()
        entry = self._modules[idx]
        widget = entry["instance"].widget

        popup = _ModulePopup(widget, entry["name"],
                             on_close=lambda i=idx: self._close_popup(i))
        popup.resize(420, 500)

        # позиция рядом с панелью
        sg = self.screen().geometry()
        sb_right = self.x() + self._sidebar.width() + 16
        if self._snapped == "right":
            sb_right = self.x() - 440
        py = max(sg.top() + 60, self.y() + 40)
        popup.move(sb_right, py)
        popup.show()

        entry["popup"] = popup
        entry["btn"].setChecked(True)

    def _close_popup(self, idx: int):
        entry = self._modules[idx]
        if entry["popup"]:
            # виджет модуля возвращаем обратно
            entry["instance"].widget.setParent(self._content)
            entry["popup"].close()
            entry["popup"] = None
        if entry["btn"]:
            entry["btn"].setChecked(False)

    def _close_all_popups(self):
        for i in range(len(self._modules)):
            self._close_popup(i)

    # ── Рисование стекла ──────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._glass.geometry()
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()
        rad = 16.0

        path = QPainterPath()
        path.addRoundedRect(rx, ry, rw, rh, rad, rad)
        p.fillPath(path, QColor(14, 16, 26, 200))

        hi = QLinearGradient(rx, ry, rx, ry + 56)
        hi.setColorAt(0.0, QColor(255, 255, 255, 16))
        hi.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillPath(path, QBrush(hi))

        pen = QPen(QColor(255, 255, 255, 18)); pen.setWidthF(1.0)
        p.setPen(pen)
        p.drawRoundedRect(rx+.5, ry+.5, rw-1, rh-1, rad, rad)
        p.end()

    # ── Drag (только за titlebar) ─────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            tb_geo = QRect(
                self._titlebar.mapToGlobal(self._titlebar.rect().topLeft()),
                self._titlebar.size()
            )
            if tb_geo.contains(event.globalPosition().toPoint()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _show_preview(self, rect: QRect):
        if not self._preview_window:
            self._preview_window = _SnapPreview()
        self._preview_window.setGeometry(rect)
        self._preview_window.show()

    def _hide_preview(self):
        if getattr(self, '_preview_window', None):
            self._preview_window.hide()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            self.move(global_pos - self._drag_pos)

            screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
            if screen:
                sg = screen.geometry()
                pw = int(sg.width() * 0.1)
                ph = sg.height()

                if global_pos.x() <= sg.left() + SNAP_THRESHOLD:
                    preview_rect = QRect(sg.left(), sg.top(), pw, ph)
                    self._show_preview(preview_rect)
                    self._current_preview_side = 'left'
                elif global_pos.x() >= sg.right() - SNAP_THRESHOLD:
                    preview_rect = QRect(sg.right() - pw, sg.top(), pw, ph)
                    self._show_preview(preview_rect)
                    self._current_preview_side = 'right'
                else:
                    self._hide_preview()
                    self._current_preview_side = None

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_pos:
            self._drag_pos = None
            if getattr(self, '_current_preview_side', None):
                self._hide_preview()
                self._snapped = self._current_preview_side
                mode = self._mode if self._mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN) else MenuMode.SIDE_THIN
                # Before applying mode, move center to the screen we snapped to ensure it picks the right screen
                screen = QApplication.screenAt(event.globalPosition().toPoint()) or QApplication.primaryScreen()
                if screen:
                    sg = screen.geometry()
                    self.move(sg.center() - QPoint(self.width() // 2, self.height() // 2))
                self._apply_mode(mode)
                self._current_preview_side = None
            else:
                self._hide_preview()
                if self._snapped:
                    self._snapped = None
                    if self._mode in (MenuMode.SIDE_THIN, MenuMode.SIDE_OPEN):
                        self._apply_mode(MenuMode.STANDARD)

    # ── Snap к краям ─────────────────────────────────────────────────────────

    def _try_snap(self):
        # Kept for backward compatibility if needed, but logic moved to mouseReleaseEvent
        pass

    # ── Анимации ─────────────────────────────────────────────────────────────

    def _fade_in(self) -> None:
        a = QPropertyAnimation(self, b"windowOpacity", self)
        a.setDuration(280); a.setStartValue(0.0); a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.start(); self._anim = a

    def _fade_out(self, callback=None) -> None:
        a = QPropertyAnimation(self, b"windowOpacity", self)
        a.setDuration(180); a.setStartValue(1.0); a.setEndValue(0.0)
        a.setEasingCurve(QEasingCurve.Type.InCubic)
        if callback: a.finished.connect(callback)
        a.start(); self._anim = a

    # ── Закрытие ─────────────────────────────────────────────────────────────

    def _request_close(self) -> None:
        for mod in self._modules:
            inst = mod.get("instance")
            if inst and hasattr(inst, "safe_close"):
                inst.safe_close()

        def _finish():
            try: core.stop()
            except Exception: pass
            QApplication.instance().quit()

        self._fade_out(callback=_finish)

    def closeEvent(self, event) -> None:
        event.ignore()
        self._request_close()

    def center(self) -> None:
        screen = self.screen()
        if screen:
            g = screen.geometry()
            self.move(g.x() + (g.width()  - self.width())  // 2,
                      g.y() + (g.height() - self.height()) // 2)

"""
UI.py — Главное окно и всплывающие окна модулей.
"""
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QHBoxLayout, 
    QLabel, QPushButton, QGridLayout, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve, Property, Signal, QRectF, QTimer
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QBrush, QPen, QRadialGradient, QCursor, QMouseEvent
)
from components.CORE import core

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SNAP_THRESHOLD = 35
HEIGHT = 420

# ---------------------------------------------------------------------------
# Shared Styles
# ---------------------------------------------------------------------------
GLASS_FRAME_STYLE = """
    QFrame#SidebarFrame {
        background: transparent;
        border: none;
    }
"""

# ---------------------------------------------------------------------------
# Snap preview ghost window
# ---------------------------------------------------------------------------
class SnapPreview(QWidget):
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
        painter.setPen(QPen(QColor(100, 160, 255, 100)))
        painter.drawRoundedRect(1, 1, w - 2, h - 2, 8, 8)
        painter.end()


# ---------------------------------------------------------------------------
# Header (visible always, has drag handle and close)
# ---------------------------------------------------------------------------
class SidebarHeader(QWidget):
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        
        # Transparent button for closing
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setStyleSheet("""
            QPushButton { background: transparent; color: #aaa; border: none; font-size: 14px; font-weight: bold; }
            QPushButton:hover { color: #f55; }
        """)
        self.btn_close.clicked.connect(self.close_clicked)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.addStretch()
        layout.addWidget(self.btn_close)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Draw the 2 horizontal lines in the middle
        cy = h // 2
        painter.setPen(QPen(QColor(255, 255, 255, 50), 2))
        painter.drawLine(w // 2 - 15, cy - 3, w // 2 + 15, cy - 3)
        painter.drawLine(w // 2 - 15, cy + 3, w // 2 + 15, cy + 3)
        painter.end()

# ---------------------------------------------------------------------------
# Sidebar Frame (The actual drawing of the glass)
# ---------------------------------------------------------------------------
class SidebarFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarFrame")
        self.setStyleSheet(GLASS_FRAME_STYLE)
        self._opacity = 1.0

    def get_anim_opacity(self):
        return self._opacity

    def set_anim_opacity(self, val):
        self._opacity = val
        self.update()

    anim_opacity = Property(float, get_anim_opacity, set_anim_opacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        parent_win = self.window()
        snapped = getattr(parent_win, '_snapped_side', None)
        expanded = getattr(parent_win, '_is_expanded', True)

        if snapped and not expanded:
            # Collapsed pill
            radius = 6
            bg = QColor(20, 22, 32, int(200 * self._opacity))
            painter.setBrush(bg)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, w, h, radius, radius)

            edge_grad = QLinearGradient(0, 0, w, 0) if snapped == 'right' else QLinearGradient(w, 0, 0, 0)
            edge_grad.setColorAt(0.0, QColor(80, 140, 255, 0))
            edge_grad.setColorAt(1.0, QColor(80, 140, 255, 60))
            painter.setBrush(QBrush(edge_grad))
            painter.drawRoundedRect(0, 0, w, h, radius, radius)
        else:
            # Full glass panel
            radius = 14
            bg_grad = QLinearGradient(0, 0, w, h)
            bg_grad.setColorAt(0.0, QColor(20, 22, 35, int(210 * self._opacity)))
            bg_grad.setColorAt(1.0, QColor(12, 14, 24, int(190 * self._opacity)))
            painter.setBrush(QBrush(bg_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(1, 1, w - 2, h - 2, radius, radius)

            shimmer = QLinearGradient(0, 0, w, 0)
            shimmer.setColorAt(0.0, QColor(255, 255, 255, 0))
            shimmer.setColorAt(0.3, QColor(255, 255, 255, int(22 * self._opacity)))
            shimmer.setColorAt(0.7, QColor(255, 255, 255, int(14 * self._opacity)))
            shimmer.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(shimmer))
            painter.drawRoundedRect(1, 1, w - 2, 40, radius, radius)

            border_grad = QLinearGradient(0, 0, 0, h)
            border_grad.setColorAt(0.0, QColor(255, 255, 255, int(70 * self._opacity)))
            border_grad.setColorAt(0.5, QColor(255, 255, 255, int(20 * self._opacity)))
            border_grad.setColorAt(1.0, QColor(255, 255, 255, int(10 * self._opacity)))
            painter.setPen(QPen(QBrush(border_grad), 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), radius, radius)

            inner_glow = QRadialGradient(0, h // 2, h * 0.6)
            inner_glow.setColorAt(0.0, QColor(60, 120, 255, int(18 * self._opacity)))
            inner_glow.setColorAt(1.0, QColor(60, 120, 255, 0))
            painter.setBrush(QBrush(inner_glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(1, 1, w - 2, h - 2, radius, radius)
        painter.end()


# ---------------------------------------------------------------------------
# Module Window (Separate floating window for each module)
# ---------------------------------------------------------------------------
class ModuleWindow(QWidget):
    def __init__(self, module_class, name, parent=None, module_id=None):
        super().__init__(parent)
        self.name = name
        self.module_id = module_id if module_id else name
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(800, 600)
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        # Titlebar
        self.titlebar = QWidget()
        self.titlebar.setFixedHeight(30)
        tb_layout = QHBoxLayout(self.titlebar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        self.lbl_title = QLabel(name)
        self.lbl_title.setStyleSheet("color: #fff; font-weight: bold; font-family: 'Segoe UI';")
        tb_layout.addWidget(self.lbl_title)
        
        # Settings button
        btn_settings = QPushButton("⚙")
        btn_settings.setFixedSize(24, 24)
        btn_settings.setStyleSheet("background: transparent; border: none; color: #aaa;")
        btn_settings.clicked.connect(self._open_configurator)
        tb_layout.addStretch()
        tb_layout.addWidget(btn_settings)
        
        # Close button
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet("background: transparent; border: none; color: #aaa;")
        btn_close.clicked.connect(self.close)
        tb_layout.addWidget(btn_close)
        
        layout.addWidget(self.titlebar)
        
        # Module Content
        self.mod = module_class(core, self)
        mod_widget = self.mod.widget if hasattr(self.mod, 'widget') else self.mod
        layout.addWidget(mod_widget, 1)
        
        # State
        self._drag_pos = None
        self._resizing = False
        self._resize_edge = ""

    def _open_configurator(self):
        try:
            from components.configurator import ConfiguratorWindow
            self.conf = ConfiguratorWindow(core)
            self.conf.open_context(self.module_id)
        except Exception as e:
            print("Configurator error:", e)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 15, 20, 220))
        painter.setPen(QColor(100, 160, 255, 80))
        painter.drawRoundedRect(self.rect().adjusted(0,0,-1,-1), 10, 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._mouse_press_pos = event.globalPosition().toPoint()
                self._mouse_press_rect = self.geometry()
            elif event.pos().y() <= self.titlebar.height():
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if not self._resizing and not self._drag_pos:
            edge = self._get_resize_edge(pos)
            if edge in ('left', 'right'): self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge in ('top', 'bottom'): self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif edge in ('topleft', 'bottomright'): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge in ('topright', 'bottomleft'): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if self._resizing:
            delta = event.globalPosition().toPoint() - self._mouse_press_pos
            r = QRect(self._mouse_press_rect)
            if 'left' in self._resize_edge: r.setLeft(r.left() + delta.x())
            if 'right' in self._resize_edge: r.setRight(r.right() + delta.x())
            if 'top' in self._resize_edge: r.setTop(r.top() + delta.y())
            if 'bottom' in self._resize_edge: r.setBottom(r.bottom() + delta.y())
            self.setGeometry(r)
        elif self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _get_resize_edge(self, pos):
        margin = 8
        r = self.rect()
        edge = ""
        if pos.y() <= margin: edge += "top"
        elif pos.y() >= r.height() - margin: edge += "bottom"
        if pos.x() <= margin: edge += "left"
        elif pos.x() >= r.width() - margin: edge += "right"
        return edge


# ---------------------------------------------------------------------------
# Main App Window (The responsive side menu)
# ---------------------------------------------------------------------------
class GlassWindow(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._expanded_width = 130
        self._collapsed_width = 30
        self._floating_width = 160
        
        self.resize(self._floating_width, HEIGHT)

        self._snapped_side = None
        self._is_hovered = False
        self._is_expanded = True
        
        self._drag_offset = None
        self._current_preview_side = None
        self._preview_window = None
        
        self._open_windows = []
        self._module_count = 0
        
        self._resizing_sidebar = False
        self._mouse_press_pos = None
        self._mouse_press_rect = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar = SidebarFrame(self)
        layout.addWidget(self.sidebar)

        self.sidebar.outer_layout = QVBoxLayout(self.sidebar)
        self.sidebar.outer_layout.setContentsMargins(0,0,0,0)
        self.sidebar.outer_layout.setSpacing(0)
        
        # Use Header as drag handle ALWAYS
        self.header = SidebarHeader(self.sidebar)
        self.header.close_clicked.connect(self._close_app)
        self.sidebar.outer_layout.addWidget(self.header)
        
        self.content_container = QWidget(self.sidebar)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(12, 0, 12, 14)
        
        # Grid for modules
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0,0,0,0)
        self.grid_layout.setSpacing(4)
        self.content_layout.addWidget(self.grid_widget)
        
        self.content_layout.addStretch()
        
        self.sidebar.outer_layout.addWidget(self.content_container)

        self._anim_width = QPropertyAnimation(self, b"anim_width")
        self._anim_width.setDuration(240)
        self._anim_width.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._anim_opacity = QPropertyAnimation(self.sidebar, b"anim_opacity")
        self._anim_opacity.setDuration(220)
        
        # 1-second hide delay
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(1000)
        self._hide_timer.timeout.connect(self._apply_hide)
        
        self.setMouseTracking(True)
        self._render()

    def _close_app(self):
        core.stop()
        QApplication.quit()

    def _mount(self, module_class, icon=None, name=None, module_id=None):
        btn = QPushButton(icon or "📦")
        btn.setFixedSize(32, 32)
        btn.setToolTip(name)
        btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; font-size: 16px; color: white; }
            QPushButton:hover { background: rgba(100,160,255,0.4); }
        """)
        context_name = module_id if module_id else name
        btn.clicked.connect(lambda _, mc=module_class, mn=name, mid=context_name: self._spawn_module_window(mc, mn, mid))
        row = self._module_count // 3
        col = self._module_count % 3
        self.grid_layout.addWidget(btn, row, col)
        self._module_count += 1

    def _spawn_module_window(self, module_class, name, module_id=None):
        win = ModuleWindow(module_class, name, module_id=module_id)
        win.show()
        self._open_windows.append(win)

    def get_anim_width(self): return self.width()
    def set_anim_width(self, val):
        self.setFixedWidth(val)
        if self._snapped_side == 'right' and hasattr(self, '_anchor_x'):
            self.move(self._anchor_x - val, self.y())
        elif self._snapped_side == 'left' and hasattr(self, '_anchor_x'):
            self.move(self._anchor_x, self.y())
    anim_width = Property(int, get_anim_width, set_anim_width)

    def _animate_width(self, target):
        if self.width() == target: return
        self._anim_width.stop()
        self._anim_width.setStartValue(self.width())
        self._anim_width.setEndValue(target)
        self._anim_width.start()

    def _show_preview(self, rect):
        if not self._preview_window: self._preview_window = SnapPreview()
        self._preview_window.setGeometry(rect)
        self._preview_window.show()

    def _hide_preview(self):
        if self._preview_window: self._preview_window.hide()

    def enterEvent(self, event):
        self._hide_timer.stop()
        self._is_hovered = True
        self._render()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        if self._snapped_side:
            self._hide_timer.start()
        else:
            self._render()
        super().leaveEvent(event)

    def _apply_hide(self):
        if not self._is_hovered:
            self._render()

    def _render(self):
        should_expand = (not self._snapped_side) or (self._snapped_side and self._is_hovered)
        
        if not self._snapped_side:
            target_width = self._floating_width
        elif self._snapped_side and not should_expand:
            target_width = self._collapsed_width
        else:
            target_width = self._expanded_width
            
        self._animate_width(target_width)

        if should_expand and not self._is_expanded:
            self._is_expanded = True
            self.content_container.show()
            self._anim_opacity.setStartValue(0.3)
            self._anim_opacity.setEndValue(1.0)
            self._anim_opacity.start()
            self.header.btn_close.show()
        elif not should_expand and self._is_expanded:
            self._is_expanded = False
            self.content_container.hide()
            self._anim_opacity.setStartValue(1.0)
            self._anim_opacity.setEndValue(0.85)
            self._anim_opacity.start()
            self.header.btn_close.hide() # hide close button when collapsed
            
        self.sidebar.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton: return
        
        # Check resizing logic first
        pos = event.pos()
        margin = 8
        r = self.rect()
        edge = None
        
        # Determine valid resize edges based on snap state
        if not self._snapped_side:
            if pos.x() >= r.width() - margin: edge = "right"
            elif pos.x() <= margin: edge = "left"
        elif self._snapped_side == 'left' and pos.x() >= r.width() - margin:
            edge = "right"
        elif self._snapped_side == 'right' and pos.x() <= margin:
            edge = "left"
            
        if edge:
            self._resizing_sidebar = True
            self._mouse_press_pos = event.globalPosition().toPoint()
            self._mouse_press_rect = self.geometry()
            self._anim_width.stop()  # Stop any running animation
            event.accept()
            return
            
        # If not resizing, handle dragging from the header area
        local = event.pos()
        if local.y() <= self.header.height():
            self._drag_offset = local
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        global_pos = event.globalPosition().toPoint()
        
        # Resize cursor handling
        if not self._resizing_sidebar and not self._drag_offset:
            margin = 8
            r = self.rect()
            if not self._snapped_side:
                if pos.x() >= r.width() - margin or pos.x() <= margin:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            elif self._snapped_side == 'left' and pos.x() >= r.width() - margin:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif self._snapped_side == 'right' and pos.x() <= margin:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if self._resizing_sidebar:
            delta = global_pos - self._mouse_press_pos
            r = QRect(self._mouse_press_rect)
            
            if self._snapped_side == 'left':
                new_width = max(100, r.width() + delta.x())
                self._expanded_width = new_width
                self.set_anim_width(new_width)
            elif self._snapped_side == 'right':
                new_width = max(100, r.width() - delta.x())
                self._expanded_width = new_width
                self.set_anim_width(new_width)
            else:
                # Unsnapped resize
                if pos.x() > self.width() // 2:
                    new_width = max(100, r.width() + delta.x())
                    r.setWidth(new_width)
                    self._expanded_width = new_width
                    self.setGeometry(r)
                else:
                    new_width = max(100, r.width() - delta.x())
                    r.setLeft(r.right() - new_width + 1)
                    self._expanded_width = new_width
                    self.setGeometry(r)
            event.accept()
            return

        if self._drag_offset is None: return

        # Dragging Logic
        if self._snapped_side:
            if (pos - self._drag_offset).manhattanLength() > 12:
                # Detach
                self._snapped_side = None
                self._is_hovered = False
                self._render()
                self._drag_offset = QPoint(self.width() // 2, self._drag_offset.y())
            return

        self.move(global_pos - self._drag_offset)

        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        if screen:
            sr = screen.availableGeometry()
            yc = global_pos.y()
            if global_pos.x() <= sr.left() + SNAP_THRESHOLD:
                self._show_preview(QRect(sr.left(), yc - HEIGHT // 2, self._collapsed_width, HEIGHT))
                self._current_preview_side = 'left'
            elif global_pos.x() >= sr.right() - SNAP_THRESHOLD:
                self._show_preview(QRect(sr.right() - self._collapsed_width, yc - HEIGHT // 2, self._collapsed_width, HEIGHT))
                self._current_preview_side = 'right'
            else:
                self._hide_preview()
                self._current_preview_side = None
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton: return
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        if self._resizing_sidebar:
            self._resizing_sidebar = False
            event.accept()
            return

        if self._current_preview_side:
            self._hide_preview()
            screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
            if screen:
                sr = screen.availableGeometry()
                y = max(sr.top(), min(self.y(), sr.bottom() - HEIGHT))
                side = self._current_preview_side
                if side == 'left':
                    self.move(sr.left(), y)
                    self._anchor_x = sr.left()
                else:
                    self.move(sr.right() - self._expanded_width + 1, y)
                    self._anchor_x = sr.right() + 1
                self._snapped_side = side
                self._is_hovered = False
                self._render()
            self._current_preview_side = None

        self._drag_offset = None
        event.accept()

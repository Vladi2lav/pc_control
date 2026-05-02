from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFrame
from PySide6.QtGui import QCursor
from PySide6.QtCore import QPoint, Qt
import sys
import signal
import os

basedir = os.path.dirname(__file__)

class PhantomWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.main_container = QFrame(self)
        self.layout.addWidget(self.main_container)
        
        self.main_container.setStyleSheet("""
            background-color: rgba(0, 120, 215, 80); 
            border: 2px solid rgba(0, 120, 215, 180);
            border-radius: 8px;
        """)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput 
        )
        
        # Делаем базовый холст прозрачным
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setStyleSheet("""
            background-color: rgba(0, 120, 215, 80); 
            border: 2px solid rgba(0, 120, 215, 180);
            border-radius: 8px;
        """)

class CustomWindow(QMainWindow):
    statesize = {
        1: (240, 500, 0, 0), # wh(px) xy(%)
        2: (240, 500, 0, 0), # wh(px) xy(%)
        3: (20, 100, 5, 50), # wh(px) xy(%)
        4: (100, 300, 5, 50), # wh(px) xy(%)
    }

    def __init__(self):
        super().__init__()
        self.native_style = QApplication.instance().style().objectName()
        
        # --- НАСТРОЙКИ АРХИТЕКТУРЫ ДЛЯ ШЕЙДЕРОВ ---
        self.WOBBLY_MARGIN = 30  # Размер невидимой буферной зоны для "желе"
        self.RESIZE_MARGIN = 10  # Толщина невидимой рамки для захвата мышью
        
        self.setWindowFlags( Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Физический размер теперь включает отступы
        self.resize(500 + self.WOBBLY_MARGIN * 2, 400 + self.WOBBLY_MARGIN * 2)
        self.setMinimumSize(150 + self.WOBBLY_MARGIN * 2, 100 + self.WOBBLY_MARGIN * 2)
        
        # Центральный виджет - прозрачная основа
        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)

        # Layout, который создает буферную зону
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(
            self.WOBBLY_MARGIN, self.WOBBLY_MARGIN, 
            self.WOBBLY_MARGIN, self.WOBBLY_MARGIN
        )

        # Сам видимый интерфейс
        self.main_container = QFrame(self.central_widget)
        self.main_layout.addWidget(self.main_container)

        self.phantom = PhantomWindow()
        self.on_edge = False
        self.setMouseTracking(True)
        self.main_container.setMouseTracking(True)
        self.central_widget.setMouseTracking(True)
        
        self.state = 1
        self.setstate(self.state)

    def setstate(self, state):
        self.state = state
        
        if state == 1:
            QApplication.instance().setStyle("Fusion")
            # Включаем буферную зону
            self.main_layout.setContentsMargins(
                self.WOBBLY_MARGIN, self.WOBBLY_MARGIN, 
                self.WOBBLY_MARGIN, self.WOBBLY_MARGIN
            )
            self.main_container.setStyleSheet("""
                QFrame {
                    background-color: #212121;
                    border-radius: 8px;
                }
            """)
        elif state == 2:
            QApplication.setStyle("Fusion")
            # Отключаем буферную зону, окно прилипает к краю жестко
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border-radius: 0px; 
                }
            """)
            # ВОЗВРАЩЕНО ИЗ ТВОЕГО КОДА: жесткая геометрия из словаря
            self.setGeometry(
                self.statesize[2][2], 
                self.statesize[2][3], 
                self.statesize[2][0], 
                self.statesize[2][1]
            )

    def _get_resize_edge(self, pos: QPoint):
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        
        # Рассчитываем видимые края (с учетом текущих отступов)
        margins = self.main_layout.contentsMargins()
        v_left = margins.left()
        v_right = w - margins.right()
        v_top = margins.top()
        v_bottom = h - margins.bottom()
        
        # Если клик совсем за пределами видимого окна (в пустом желе) - игнорируем
        if x < v_left - 5 or x > v_right + 5 or y < v_top - 5 or y > v_bottom + 5:
            return None
            
        # Проверяем близость к видимым краям
        is_left = abs(x - v_left) <= self.RESIZE_MARGIN
        is_right = abs(x - v_right) <= self.RESIZE_MARGIN
        is_top = abs(y - v_top) <= self.RESIZE_MARGIN
        is_bottom = abs(y - v_bottom) <= self.RESIZE_MARGIN
        
        if is_top and is_left: return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        if is_top and is_right: return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        if is_bottom and is_left: return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        if is_bottom and is_right: return Qt.Edge.BottomEdge | Qt.Edge.RightEdge
        
        if is_top: return Qt.Edge.TopEdge
        if is_bottom: return Qt.Edge.BottomEdge
        if is_left: return Qt.Edge.LeftEdge
        if is_right: return Qt.Edge.RightEdge
        
        return None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.position())
            
            # Логика отлипания (возврат в состояние 1)
            if self.state == 2:
                self.setstate(1)
                
                # ВОЗВРАЩЕНО ИЗ ТВОЕГО КОДА: берем старые габариты из словаря
                old_w, old_h, x_pct, y_pct = self.statesize[1]
                
                # Центрируем окно под курсором
                new_x = int(event.globalPosition().x() - (old_w / 2))
                new_y = int(event.globalPosition().y() - (old_h / 2)) 
                
                self.setGeometry(new_x, new_y, old_w, old_h)
                self.windowHandle().startSystemMove()
                
            elif self.state == 1:
                if edge is not None:
                    self.windowHandle().startSystemResize(edge)
                else:
                    margins = self.main_layout.contentsMargins()
                    if (event.position().x() >= margins.left() and event.position().x() <= self.width() - margins.right() and
                        event.position().y() >= margins.top() and event.position().y() <= self.height() - margins.bottom()):
                        self.windowHandle().startSystemMove()
            
        elif event.button() == Qt.MouseButton.RightButton:
            current_screen = self.screen()
            if current_screen:
                screen_geometry = current_screen.geometry()
                self.move(screen_geometry.topLeft())
            
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.close()

    def mouseMoveEvent(self, event):
        if self.state == 1:
            edge = self._get_resize_edge(event.position())
            
            if edge == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or edge == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge == (Qt.Edge.TopEdge | Qt.Edge.RightEdge) or edge == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif edge in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge in (Qt.Edge.TopEdge, Qt.Edge.BottomEdge):
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            
    def moveEvent(self, event):
        super().moveEvent(event)
        
        mouse_x = QCursor.pos().x()
        screen_geom = self.screen().geometry()
        
        screen_left = screen_geom.left()
        screen_right = screen_geom.right()
        screen_width = screen_geom.width()
        screen_height = screen_geom.height()
        screen_top = screen_geom.top()

        if mouse_x <= screen_left + 50:
            if not self.on_edge:
                self.on_edge = True
                self.phantom.setGeometry(
                    screen_left, screen_top, 
                    screen_width // 4, screen_height
                )
                self.phantom.show()
                
        elif mouse_x >= screen_right - 50:
            if not self.on_edge:
                self.on_edge = True
                self.phantom.setGeometry(
                    screen_right - (screen_width // 4), screen_top, 
                    screen_width // 4, screen_height
                )
                self.phantom.show()
                
        else:
            if self.on_edge:
                self.on_edge = False
                self.phantom.hide() 
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Магнитимся к краю
            if self.on_edge and self.state == 1:
                
                # ВОЗВРАЩЕНО ИЗ ТВОЕГО КОДА: сохраняем текущий размер в словарь
                w = self.width()
                h = self.height()
                self.statesize[1] = (w, h, 0, 0)

                # Меняем состояние (отступы уберутся, применится statesize[2])
                self.setstate(2)
                
                self.phantom.hide()
                self.on_edge = False
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CustomWindow()
    window.show() 

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
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
        # 1. НАСТРОЙКИ ГЛАВНОГО ОКНА (Окно-призрак)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(500, 400)
        self.setMinimumSize(150, 100)
        
        

        
        self.main_container = QFrame(self)
        self.setCentralWidget(self.main_container)

        
        self.phantom = PhantomWindow()
        self.on_edge = False
        self.setMouseTracking(True)
        self.MARGIN = 15
        self.main_container.setMouseTracking(True)
        self.state = 1
        self.setstate(self.state)

    def setstate(self, state):
        self.state = state
        
        if state == 1:
            QApplication.instance().setStyle(self.native_style)
            self.main_container.setStyleSheet("""
                QFrame {
                    background-color: #212121;
                    border-radius: 8px;
                }
            """)
        elif state == 2:
            QApplication.setStyle("Fusion")
            self.main_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border-radius: 0px; 
                }
            """)
            self.setGeometry((self.phantom.geometry()))


    def _get_resize_edge(self, pos: QPoint):
        rect = self.rect()
        x, y = pos.x(), pos.y()
        
        is_top = y <= self.MARGIN
        is_bottom = y >= rect.height() - self.MARGIN
        is_left = x <= self.MARGIN
        is_right = x >= rect.width() - self.MARGIN
        
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
                
                # Достаем старые габариты
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
                    self.windowHandle().startSystemMove()
            
        elif event.button() == Qt.MouseButton.RightButton:
            current_screen = self.screen()
            if current_screen:
                screen_geometry = current_screen.geometry()
                self.move(screen_geometry.topLeft())
            
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.close()

    def mouseMoveEvent(self, event):
        if self.state == 2:
            None
        elif self.state == 1:
            
            
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
                    screen_left, 
                    screen_top, 
                    screen_width // 4, 
                    screen_height
                )
                self.phantom.show()
                
        elif mouse_x >= screen_right - 50:
            if not self.on_edge:
                self.on_edge = True
                self.phantom.setGeometry(
                    screen_right - (screen_width // 4), 
                    screen_top, 
                    screen_width // 4, 
                    screen_height
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
                
                # Запоминаем текущий размер
                w = self.width()
                h = self.height()
                self.statesize[1] = (w, h, 0, 0)

                # Меняем состояние (цвета и углы) и размер
                self.setstate(2)
                
                
                self.phantom.hide()
                self.on_edge = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CustomWindow()
    window.show() 

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
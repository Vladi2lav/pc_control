

from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QMainWindow, QProgressBar, QSlider, QTabWidget, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout, QGridLayout, QPushButton, QLineEdit, QTextEdit, QFrame, QGraphicsDropShadowEffect
from PySide6.QtGui import QGuiApplication, QPixmap, QLinearGradient, QColor, QPalette, QBrush, QPainter
from PySide6.QtCore import QPoint, QTimer, Qt
import sys
import signal
import os

basedir = os.path.dirname(__file__)
if __name__ == '__main__':

    class CustomWindow(QMainWindow):
        state = 1
        statesize = {
            1:(240,500,50,50),# wh(px) xy(%)
            2:(240,500,50,50),# wh(px) xy(%)
            3:(20,100,5,50),# wh(px) xy(%)
            4:(100,300,5,50),# wh(px) xy(%)
        }
        def __init__(self):
            super().__init__()
            self.resize(500, 400)
            self.setMinimumSize(150, 100)
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

            self.setStyleSheet("background-color: #212121;")

            self.setMouseTracking(True)
            self.MARGIN = 15

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
                if edge is not None:
                    self.windowHandle().startSystemResize(edge)
                else:
                    self.windowHandle().startSystemMove()
            
            elif event.button() == Qt.MouseButton.RightButton:
                # Получаем текущий экран, на котором находится окно в данный момент
                current_screen = self.screen()
                
                if current_screen:
                    # Получаем координаты и размеры текущего экрана
                    screen_geometry = current_screen.geometry()
                    
                    # Перемещаем окно в левый верхний угол ТЕКУЩЕГО экрана
                    # screen_geometry.topLeft() возвращает QPoint(x, y) начала этого монитора
                    self.move(screen_geometry.topLeft())
                
            elif event.button() == Qt.MouseButton.MiddleButton:
                self.close()
                
            # if event.button() == Qt.MouseButton.RightButton:
            #     self.close()
            # if event.button() == Qt.MouseButton.MiddleButton:
            #     self.showMinimized()



        def mouseMoveEvent(self, event):
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

    app = QApplication(sys.argv)
    window = CustomWindow()
    window.show() 

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())

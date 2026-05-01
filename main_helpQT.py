
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QMainWindow, QProgressBar, QSlider, QTabWidget, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout, QGridLayout, QPushButton, QLineEdit, QTextEdit, QFrame, QGraphicsDropShadowEffect
from PySide6.QtGui import QPixmap, QLinearGradient, QColor, QPalette, QBrush, QPainter
from PySide6.QtCore import QPoint, QTimer, Qt
import sys
import signal
import os

basedir = os.path.dirname(__file__)
if __name__ == '__main__':
    class AdvancedShowcaseWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Mega UI Sandbox")
            self.resize(900, 700)

            # --- ФОНОВОЕ ИЗОБРАЖЕНИЕ ---
            basedir = os.path.dirname(__file__)
            self.bg_pixmap = QPixmap(os.path.join(basedir, "vivereedit.png"))

            # Центральный виджет и основной лояут
            self.main_container = QWidget()
            self.setCentralWidget(self.main_container)
            self.main_layout = QVBoxLayout(self.main_container)
            self.main_layout.setContentsMargins(20, 20, 20, 20)

            self.init_header()
            self.init_tabs()

        def init_header(self):
            # --- ГРАДИЕНТНАЯ ПАНЕЛЬ С ТЕНЬЮ ---
            header_panel = QFrame()
            header_panel.setObjectName("headerPanel")
            header_panel.setStyleSheet("""
                #headerPanel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                stop:0 #ff0844, stop:1 #ffb199);
                    border-radius: 12px;
                }
            """)
            header_panel.setFixedHeight(60)
            
            # Тень
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 100))
            header_panel.setGraphicsEffect(shadow)

            layout = QVBoxLayout(header_panel)
            title = QLabel("Продвинутая панель элементов UI")
            title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent;")
            layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
            
            self.main_layout.addWidget(header_panel)

        def init_tabs(self):
            # --- ВКЛАДКИ (QTabWidget) ---
            self.tabs = QTabWidget()
            self.tabs.setStyleSheet("""
                QTabWidget::pane { border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 5px; background: rgba(30, 30, 30, 0.6); }
                QTabBar::tab { background: #333; color: white; padding: 10px 20px; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px; }
                QTabBar::tab:selected { background: #ffb199; color: black; font-weight: bold; }
            """)

            # Создаем страницы для вкладок
            self.tab1 = QWidget()
            self.tab2 = QWidget()
            
            self.tabs.addTab(self.tab1, "Базовые элементы")
            self.tabs.addTab(self.tab2, "Интерактив")
            
            self.setup_tab1()
            self.setup_tab2()
            
            self.main_layout.addWidget(self.tabs)

        def setup_tab1(self):
            # --- КОМПОНОВКА 1 ВКЛАДКИ ---
            layout = QVBoxLayout(self.tab1)
            
            # Сетка кнопок
            grid = QGridLayout()
            btn_style = """
                QPushButton { background-color: rgba(255, 255, 255, 0.1); color: white; border: 1px solid #aaa; border-radius: 5px; padding: 8px; }
                QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); border-color: #ffb199; }
            """
            for i in range(4):
                btn = QPushButton(f"Сетка {i+1}")
                btn.setStyleSheet(btn_style)
                grid.addWidget(btn, i // 2, i % 2) # Распределение 2x2
            layout.addLayout(grid)

            # Поле ввода
            self.line_edit = QLineEdit()
            self.line_edit.setPlaceholderText("Однострочное поле ввода...")
            self.line_edit.setStyleSheet("background: rgba(0,0,0,0.5); color: white; padding: 8px; border-radius: 4px; border: 1px solid #555;")
            layout.addWidget(self.line_edit)

            # Текстовое поле
            self.text_edit = QTextEdit()
            self.text_edit.setPlaceholderText("Многострочное поле...\nПоддерживает HTML!")
            self.text_edit.setStyleSheet("background: rgba(0,0,0,0.5); color: #00ffcc; padding: 8px; border-radius: 4px; border: 1px solid #555;")
            layout.addWidget(self.text_edit)

        def setup_tab2(self):
            # --- КОМПОНОВКА 2 ВКЛАДКИ ---
            layout = QVBoxLayout(self.tab2)
            layout.setSpacing(20)

            # Выпадающий список (ComboBox)
            h_layout1 = QHBoxLayout()
            h_layout1.addWidget(QLabel("<font color='white'>Выберите опцию:</font>"))
            self.combo = QComboBox()
            self.combo.addItems(["Опция 1", "Опция 2", "Опция 3"])
            self.combo.setStyleSheet("background: #444; color: white; padding: 5px; border-radius: 3px;")
            h_layout1.addWidget(self.combo)
            h_layout1.addStretch() # Пружина, чтобы прижать элементы влево
            layout.addLayout(h_layout1)

            # Чекбоксы
            h_layout2 = QHBoxLayout()
            self.check1 = QCheckBox("Включить тени")
            self.check1.setChecked(True)
            self.check2 = QCheckBox("Темная тема")
            for cb in [self.check1, self.check2]:
                cb.setStyleSheet("color: white; spacing: 5px;")
                h_layout2.addWidget(cb)
            h_layout2.addStretch()
            layout.addLayout(h_layout2)

            # Ползунок (QSlider) и Прогресс-бар (QProgressBar)
            self.slider = QSlider(Qt.Orientation.Horizontal)
            self.slider.setRange(0, 100)
            self.slider.setValue(50)
            
            self.progress = QProgressBar()
            self.progress.setRange(0, 100)
            self.progress.setValue(50)
            self.progress.setStyleSheet("""
                QProgressBar { border: 1px solid #aaa; border-radius: 5px; text-align: center; color: white; background: rgba(0,0,0,0.5); }
                QProgressBar::chunk { background-color: #ff0844; width: 10px; margin: 1px; }
            """)

            # Связываем ползунок с прогресс-баром (Сигналы и Слоты)
            self.slider.valueChanged.connect(self.progress.setValue)

            layout.addWidget(QLabel("<font color='white'>Ползунок и Прогресс:</font>"))
            layout.addWidget(self.slider)
            layout.addWidget(self.progress)
            layout.addStretch()

        def paintEvent(self, event):
            # Отрисовка фона
            painter = QPainter(self)
            if not self.bg_pixmap.isNull():
                painter.drawPixmap(self.rect(), self.bg_pixmap)
            else:
                painter.fillRect(self.rect(), QColor("#1e1e2e"))
                
    class CustomWindow(QMainWindow):
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


    class FastWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Fast Window")
            screen = QApplication.primaryScreen()
        
            screen_rect = screen.availableGeometry()
            self.resize(screen_rect.width()//2, screen_rect.height()//2)
            
            self.central_widget = QWidget()
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint #| 
#               Qt.WindowType.FramelessWindowHint
            )
            self.move(0,0)
            self.layout = QVBoxLayout(self.central_widget)
            self.setCentralWidget(self.central_widget)
            self.status_label = QLabel("Загрузка интерфейса...")
            self.layout.addWidget(self.status_label)
            QTimer.singleShot(100, self.load_heavy_elements)
        def load_heavy_elements(self):

            self.status_label.deleteLater()
            image_label = QLabel()
            image_path = os.path.join(basedir, "vivereedit.png")
            pixmap = QPixmap(image_path) 
            image_label.setPixmap(pixmap.scaled(200,400, Qt.AspectRatioMode.KeepAspectRatio)) 
            self.layout.addWidget(image_label)

            table = QTableWidget(3, 2)
            table.setHorizontalHeaderLabels(["Имя", "Роль"])
            table.setItem(0, 0, QTableWidgetItem("Python"))
            table.setItem(0, 1, QTableWidgetItem("Логика"))
            self.layout.addWidget(table)

    app = QApplication(sys.argv)
    
    window = CustomWindow()
    window2 = FastWindow()
    w = AdvancedShowcaseWindow()
    
    window.show() 
    window2.show() 
    w.show()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
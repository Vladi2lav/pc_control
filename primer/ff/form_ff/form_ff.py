import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton

class MainForm:
    def run(self):
        app = QApplication.instance()
        created_app = False
        if not app:
            app = QApplication(sys.argv)
            created_app = True
            
        window = QMainWindow()
        window.setWindowTitle("Форма модуля ff")
        window.resize(400, 300)
        
        central = QWidget()
        layout = QVBoxLayout(central)
        
        label = QLabel("Запущена главная форма модуля ff")
        label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 20px;")
        layout.addWidget(label)
        
        btn = QPushButton("Закрыть")
        btn.clicked.connect(window.close)
        layout.addWidget(btn)
        
        window.setCentralWidget(central)
        window.show()
        
        if created_app:
            sys.exit(app.exec())

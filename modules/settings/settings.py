from components.module_system import BaseModule
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QCheckBox

class SettingsModule(BaseModule):
    def __init__(self, core, parent=None, **kwargs):
        super().__init__(core=core, parent=parent, **kwargs)
        self.widget = QWidget(parent)
        layout = QVBoxLayout(self.widget)
        
        title = QLabel("System Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        subtitle = QLabel("Independent settings module (1C-style config).")
        subtitle.setStyleSheet("color: #aaa; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Example settings
        cb_dark = QCheckBox("Dark Theme")
        cb_dark.setChecked(True)
        cb_dark.setStyleSheet("color: white;")
        layout.addWidget(cb_dark)
        
        cb_anim = QCheckBox("Enable Animations")
        cb_anim.setChecked(True)
        cb_anim.setStyleSheet("color: white;")
        layout.addWidget(cb_anim)
        
        layout.addStretch(1)
        
        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background: rgba(100,160,255,0.8); color: white; padding: 10px; border-radius: 6px;")
        layout.addWidget(btn_save)
        
        self.widget.setStyleSheet("background: transparent;")

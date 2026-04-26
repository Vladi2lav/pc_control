"""
Built-in configurator launcher module.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from components.module_system import BaseModule


class ModuleStudioModule(BaseModule):
    def __init__(self, core, parent=None, **kwargs):
        super().__init__(core=core, parent=parent, **kwargs)
        self.widget = QWidget(parent)
        self._selected_module_id: str | None = None
        self._build_ui()
        self.register_local_api(
            {
                "list_modules": self.api_list_modules,
                "get_config": self.api_get_config,
                "save_config": self.api_save_config,
            }
        )
        self.refresh_modules()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self.widget)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Configurator")
        title.setProperty("style_", "title")
        subtitle = QLabel("Entry point for the full-screen 1C-style configurator")
        subtitle.setProperty("style_", "muted")
        title_wrap = QVBoxLayout()
        title_wrap.addWidget(title)
        title_wrap.addWidget(subtitle)
        header.addLayout(title_wrap)
        header.addStretch(1)
        self.config_button = QToolButton()
        self.config_button.setText("cfg")
        self.config_button.setFixedSize(28, 28)
        self.config_button.clicked.connect(lambda: self.core.call_api("app.open_configurator", context="app"))
        self.runtime_button = QToolButton()
        self.runtime_button.setText("run")
        self.runtime_button.setFixedSize(34, 28)
        self.runtime_button.clicked.connect(self.open_selected_runtime)
        header.addWidget(self.runtime_button)
        header.addWidget(self.config_button)
        root.addLayout(header)

        actions = QHBoxLayout()
        self.open_app_button = QPushButton("Open main configurator")
        self.open_app_button.setProperty("style_", "accent")
        self.open_selected_button = QPushButton("Open selected module")
        self.open_runtime_button = QPushButton("Open runtime")
        self.create_module_button = QPushButton("Create module")
        self.reload_button = QPushButton("Reload")
        self.theme_dark = QPushButton("Dark glass")
        self.theme_light = QPushButton("White glass")
        self.open_app_button.clicked.connect(lambda: self.core.call_api("app.open_configurator", context="app"))
        self.open_selected_button.clicked.connect(self.open_selected_module)
        self.open_runtime_button.clicked.connect(self.open_selected_runtime)
        self.create_module_button.clicked.connect(self.create_module)
        self.reload_button.clicked.connect(self.refresh_modules)
        self.theme_dark.clicked.connect(lambda: self.core.call_api("app.set_theme", theme="dark"))
        self.theme_light.clicked.connect(lambda: self.core.call_api("app.set_theme", theme="light"))
        actions.addWidget(self.open_app_button)
        actions.addWidget(self.open_selected_button)
        actions.addWidget(self.open_runtime_button)
        actions.addWidget(self.create_module_button)
        actions.addWidget(self.reload_button)
        actions.addStretch(1)
        actions.addWidget(self.theme_dark)
        actions.addWidget(self.theme_light)
        root.addLayout(actions)

        self.module_list = QListWidget()
        self.module_list.currentItemChanged.connect(self._on_module_selected)
        root.addWidget(self.module_list, 1)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setProperty("style_", "muted")
        root.addWidget(self.info)

    def refresh_modules(self) -> None:
        self.core.modules.discover()
        self.module_list.clear()
        for manifest in self.core.modules.list_manifests():
            item = QListWidgetItem(f"{manifest.name} [{manifest.module_id}]")
            item.setData(Qt.ItemDataRole.UserRole, manifest.module_id)
            item.setToolTip(manifest.description)
            self.module_list.addItem(item)
        if self.module_list.count():
            self.module_list.setCurrentRow(0)

    def _on_module_selected(self, current, previous) -> None:
        if current is None:
            self._selected_module_id = None
            self.info.setText("")
            return
        module_id = current.data(Qt.ItemDataRole.UserRole)
        self._selected_module_id = module_id
        manifest = self.core.modules.get_manifest(module_id)
        config = self.core.modules.get_module_config(module_id)
        forms = config.get("forms", [])
        pages = sum(len(form.get("pages", [])) for form in forms)
        self.info.setText(
            f"{manifest.name}\n"
            f"id: {manifest.module_id}\n"
            f"version: {manifest.version}\n"
            f"forms: {len(forms)}\n"
            f"pages: {pages}\n"
            f"requisites: {len(config.get('requisites', []))}\n"
            f"commands: {len(config.get('commands', []))}"
        )

    def open_selected_module(self) -> None:
        if self._selected_module_id:
            self.core.call_api("app.open_configurator", context=self._selected_module_id)

    def open_selected_runtime(self) -> None:
        if self._selected_module_id:
            self.core.call_api("app.open_module_runtime", module_id=self._selected_module_id)

    def create_module(self) -> None:
        module_id, ok = QInputDialog.getText(self.widget, "Create module", "Module ID (latin, underscore)")
        if not ok or not module_id.strip():
            return
        name, ok = QInputDialog.getText(self.widget, "Create module", "Module name")
        if not ok or not name.strip():
            return
        try:
            self.core.call_api("app.create_module", module_id=module_id.strip(), name=name.strip())
        except Exception as exc:
            QMessageBox.warning(self.widget, "Create module", str(exc))
            return
        self.refresh_modules()
        for row in range(self.module_list.count()):
            item = self.module_list.item(row)
            if f"[{module_id.strip().lower()}]" in item.text().lower():
                self.module_list.setCurrentRow(row)
                break

    def api_list_modules(self) -> list[dict]:
        return [manifest.to_dict() for manifest in self.core.modules.list_manifests()]

    def api_get_config(self, module_id: str) -> dict:
        return self.core.modules.get_module_config(module_id)

    def api_save_config(self, module_id: str, config: dict) -> dict:
        self.core.modules.save_module_config(module_id, config)
        return config

    def safe_close(self) -> None:
        super().safe_close()

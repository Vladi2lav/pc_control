"""
Config-driven runtime forms workspace.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QLineEdit,
    QMdiArea,
    QMdiSubWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class RuntimePageWidget(QWidget):
    def __init__(self, workspace, form_data: dict[str, Any], page_data: dict[str, Any], requisites: list[dict[str, Any]], parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.form_data = form_data
        self.page_data = page_data
        self.requisites = requisites
        self.setMinimumSize(int(form_data.get("width", 960)), int(form_data.get("height", 620)))
        self._build()

    def _build(self) -> None:
        title = QLabel(self.page_data.get("title", self.page_data.get("name", "")), self)
        title.setGeometry(14, 10, 360, 24)
        title.setProperty("style_", "title")
        title.show()

        for control in self.page_data.get("controls", []):
            widget = self._create_widget(control)
            widget.setParent(self)
            widget.setGeometry(
                int(control.get("x", 0)),
                int(control.get("y", 0)),
                max(60, int(control.get("w", 120))),
                max(24, int(control.get("h", 32))),
            )
            widget.show()

    def _create_widget(self, control: dict[str, Any]) -> QWidget:
        control_type = control.get("type", "button")
        text = control.get("text", control_type.title())
        if control_type == "label":
            widget = QLabel(text)
        elif control_type == "input":
            widget = QLineEdit()
            widget.setPlaceholderText(text)
            requisite_name = control.get("requisite", "")
            if requisite_name:
                for requisite in self.requisites:
                    if requisite.get("name") == requisite_name:
                        widget.setText(str(requisite.get("default", "")))
                        break
        elif control_type == "checkbox":
            widget = QCheckBox(text)
        else:
            widget = QPushButton(text)
            widget.clicked.connect(
                lambda checked=False, payload=deepcopy(control): self.workspace.handle_control_action(payload)
            )
        return widget


class ModuleRuntimeWorkspace(QWidget):
    def __init__(self, module_id: str, config: dict[str, Any], parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self.config = deepcopy(config)
        self.forms = {form["id"]: form for form in self.config.get("forms", [])}
        self.subwindows: dict[str, QMdiSubWindow] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.mdi = QMdiArea()
        self.mdi.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi.setTabsClosable(False)
        self.mdi.setOption(QMdiArea.AreaOption.DontMaximizeSubWindowOnActivation, True)
        root.addWidget(self.mdi)

        if self.forms:
            first_form = next(iter(self.forms.values()))
            self.open_form(first_form["id"])

    def open_form(self, form_id: str, page_id: str | None = None) -> None:
        form = self.forms.get(form_id)
        if form is None:
            return

        page = None
        for candidate in form.get("pages", []):
            if page_id is None or candidate["id"] == page_id:
                page = candidate
                break
        if page is None and form.get("pages"):
            page = form["pages"][0]
        if page is None:
            return

        key = f"{form_id}:{page['id']}"
        existing = self.subwindows.get(key)
        if existing is not None:
            self.mdi.setActiveSubWindow(existing)
            existing.showNormal()
            return

        page_widget = RuntimePageWidget(self, form, page, self.config.get("requisites", []))
        subwindow = QMdiSubWindow()
        subwindow.setWidget(page_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        subwindow.setWindowTitle(f"{form.get('title', form.get('name', form_id))} / {page.get('title', page.get('name', page['id']))}")
        subwindow.resize(int(form.get("width", 960)), int(form.get("height", 620)))
        subwindow.setStyleSheet("QMdiSubWindow { background: transparent; }")
        self.mdi.addSubWindow(subwindow)
        subwindow.show()
        self.subwindows[key] = subwindow
        self.mdi.setActiveSubWindow(subwindow)

    def handle_control_action(self, control: dict[str, Any]) -> None:
        command_name = control.get("command", "")
        target_form = control.get("target_form", "")
        target_page = control.get("target_page", "")

        if target_form:
            self.open_form(target_form, target_page or None)
            return

        if target_page:
            current_form = next(iter(self.forms.values()), None)
            if current_form is not None:
                self.open_form(current_form["id"], target_page)
            return

        if command_name:
            for command in self.config.get("commands", []):
                if command.get("name") == command_name:
                    if command.get("target_form"):
                        self.open_form(command["target_form"], command.get("target_page") or None)
                    return


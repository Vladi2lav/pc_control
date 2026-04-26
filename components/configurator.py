"""
Fullscreen configurator with visual form designer.
"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from typing import Any


from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QAction, QColor, QPainter, QPen

from PySide6.QtCore import QPoint, QRect, Qt, Signal

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMdiArea,
    QMdiSubWindow,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class DesignerCanvas(QWidget):
    controlSelected = Signal(str, str, str)
    pageChanged = Signal(str, str)

    def __init__(self, form_data: dict[str, Any], parent=None):
        super().__init__(parent)
        self.form_data = form_data
        self.current_page_index = 0
        self.widgets: dict[str, QWidget] = {}
        self.selected_control_id: str | None = None
        self._drag_control_id: str | None = None
        self._drag_offset = QPoint()
        self.setMinimumSize(
            int(form_data.get("width", 960)),
            int(form_data.get("height", 620)),
        )
        self.setMouseTracking(True)
        self.render_page()

    def current_page(self) -> dict[str, Any]:
        pages = self.form_data.setdefault("pages", [])
        if not pages:
            pages.append(
                {"id": make_id("page"), "name": "Page1", "title": "Page 1", "controls": []}
            )
        self.current_page_index = max(0, min(self.current_page_index, len(pages) - 1))
        return pages[self.current_page_index]

    def set_page(self, page_index: int) -> None:
        self.current_page_index = page_index
        page = self.current_page()
        self.render_page()
        self.pageChanged.emit(self.form_data["id"], page["id"])

    def add_control(self, control_type: str) -> None:
        page = self.current_page()
        control = {
            "id": make_id(control_type),
            "type": control_type,
            "text": control_type.title(),
            "x": 48,
            "y": 48 + len(page.get("controls", [])) * 44,
            "w": 160 if control_type != "label" else 220,
            "h": 34,
            "requisite": "",
            "command": "",
            "target_form": "",
            "target_page": "",
        }
        page.setdefault("controls", []).append(control)
        self.render_page()
        self.select_control(control["id"])

    def select_control(self, control_id: str | None) -> None:
        self.selected_control_id = control_id
        for cid, widget in self.widgets.items():
            widget.setProperty("selected", cid == control_id)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        if control_id:
            page = self.current_page()
            self.controlSelected.emit(self.form_data["id"], page["id"], control_id)

    def selected_control(self) -> dict[str, Any] | None:
        control_id = self.selected_control_id
        if not control_id:
            return None
        for control in self.current_page().get("controls", []):
            if control["id"] == control_id:
                return control
        return None

    def update_selected_control(self, changes: dict[str, Any]) -> None:
        control = self.selected_control()
        if not control:
            return
        control.update(changes)
        self.render_page()
        self.select_control(control["id"])

    def delete_selected_control(self) -> None:
        control = self.selected_control()
        if not control:
            return
        page = self.current_page()
        page["controls"] = [item for item in page.get("controls", []) if item["id"] != control["id"]]
        self.selected_control_id = None
        self.render_page()

    def render_page(self) -> None:
        for child in self.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            child.deleteLater()
        self.widgets.clear()

        page = self.current_page()
        self.setMinimumSize(
            int(self.form_data.get("width", 960)),
            int(self.form_data.get("height", 620)),
        )
        self.resize(self.minimumSize())

        for control in page.get("controls", []):
            widget = self._create_control_widget(control)
            widget.setParent(self)
            widget.setGeometry(
                int(control.get("x", 0)),
                int(control.get("y", 0)),
                max(70, int(control.get("w", 120))),
                max(28, int(control.get("h", 34))),
            )
            widget.installEventFilter(self)
            widget.show()
            self.widgets[control["id"]] = widget
        self.update()

    def _create_control_widget(self, control: dict[str, Any]) -> QWidget:
        control_type = control.get("type", "button")
        text = control.get("text", control_type.title())
        if control_type == "label":
            widget = QLabel(text)
        elif control_type == "input":
            widget = QLineEdit()
            widget.setPlaceholderText(text)
        elif control_type == "checkbox":
            from PySide6.QtWidgets import QCheckBox

            widget = QCheckBox(text)
        else:
            widget = QPushButton(text)
        widget.setObjectName(control["id"])
        widget.setProperty("glass", True)
        widget.setStyleSheet(
            "QWidget[selected='true'], QLabel[selected='true'], QPushButton[selected='true'], "
            "QLineEdit[selected='true'], QCheckBox[selected='true'] {"
            "border: 2px solid rgba(126, 184, 247, 0.95);"
            "background: rgba(126, 184, 247, 0.08);"
            "}"
        )
        return widget

    def eventFilter(self, watched, event):
        control_id = watched.objectName()
        if event.type() == QEvent.Type.MouseButtonPress:
            self.select_control(control_id)
            self._drag_control_id = control_id
            self._drag_offset = event.position().toPoint()
            return False
        if event.type() == QEvent.Type.MouseMove and self._drag_control_id == control_id and event.buttons() & Qt.MouseButton.LeftButton:
            control = self.selected_control()
            if control:
                new_pos = watched.pos() + event.position().toPoint() - self._drag_offset
                new_pos.setX(max(0, min(self.width() - watched.width(), new_pos.x())))
                new_pos.setY(max(0, min(self.height() - watched.height(), new_pos.y())))
                watched.move(new_pos)
                control["x"] = new_pos.x()
                control["y"] = new_pos.y()
            return False
        if event.type() == QEvent.Type.MouseButtonRelease and self._drag_control_id == control_id:
            self._drag_control_id = None
            return False
        return super().eventFilter(watched, event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(240, 238, 221))
        painter.setPen(QPen(QColor(205, 199, 174), 1))
        step = 24
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

        selected = self.selected_control()
        if selected:
            painter.setPen(QPen(QColor(43, 93, 171), 2))
            painter.drawRect(
                int(selected.get("x", 0)) - 1,
                int(selected.get("y", 0)) - 1,
                max(12, int(selected.get("w", 0)) + 2),
                max(12, int(selected.get("h", 0)) + 2),
            )


class FormDesignerTab(QWidget):
    selected = Signal(str, str, str)
    changed = Signal()

    def __init__(self, form_data: dict[str, Any], parent=None):
        super().__init__(parent)
        self.form_data = form_data
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        toolbar = QHBoxLayout()
        self.page_selector = QComboBox()
        self._reload_pages()
        self.page_selector.currentIndexChanged.connect(self._switch_page)
        self.add_page_button = QPushButton("Add page")
        self.add_page_button.clicked.connect(self.add_page)
        toolbar.addWidget(QLabel("Page"))
        toolbar.addWidget(self.page_selector)
        toolbar.addWidget(self.add_page_button)
        toolbar.addSpacing(14)

        for label, control_type in (
            ("Button", "button"),
            ("Label", "label"),
            ("Input", "input"),
            ("Check", "checkbox"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, kind=control_type: self._add_control(kind))
            toolbar.addWidget(button)
        toolbar.addStretch(1)

        self.delete_button = QPushButton("Delete control")
        self.delete_button.clicked.connect(self._delete_control)
        toolbar.addWidget(self.delete_button)
        root.addLayout(toolbar)

        self.canvas = DesignerCanvas(self.form_data)
        self.canvas.controlSelected.connect(self.selected.emit)
        self.canvas.pageChanged.connect(self._on_page_changed)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        canvas_host = QWidget()
        canvas_layout = QVBoxLayout(canvas_host)
        canvas_layout.setContentsMargins(12, 12, 12, 12)
        canvas_layout.addWidget(self.canvas, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        canvas_layout.addStretch(1)
        scroll.setWidget(canvas_host)
        root.addWidget(scroll, 1)

    def _reload_pages(self) -> None:
        current = self.page_selector.currentData()
        self.page_selector.blockSignals(True)
        self.page_selector.clear()
        for index, page in enumerate(self.form_data.get("pages", [])):
            self.page_selector.addItem(page.get("title", page.get("name", f"Page {index + 1}")), index)
        if self.page_selector.count():
            self.page_selector.setCurrentIndex(min(self.canvas.current_page_index if hasattr(self, "canvas") else 0, self.page_selector.count() - 1))
        self.page_selector.blockSignals(False)

    def _switch_page(self, index: int) -> None:
        if index < 0:
            return
        self.canvas.set_page(index)
        self.changed.emit()

    def _add_control(self, control_type: str) -> None:
        self.canvas.add_control(control_type)
        self.changed.emit()

    def _delete_control(self) -> None:
        self.canvas.delete_selected_control()
        self.changed.emit()

    def add_page(self) -> None:
        page = {
            "id": make_id("page"),
            "name": f"Page{len(self.form_data.get('pages', [])) + 1}",
            "title": f"Page {len(self.form_data.get('pages', [])) + 1}",
            "controls": [],
        }
        self.form_data.setdefault("pages", []).append(page)
        self._reload_pages()
        self.page_selector.setCurrentIndex(self.page_selector.count() - 1)
        self.changed.emit()

    def _on_page_changed(self, form_id: str, page_id: str) -> None:
        self.changed.emit()


class ConfiguratorWindow(QMainWindow):
    def __init__(self, core, parent=None):
        super().__init__(parent)
        self.core = core
        self._current_context = "app"
        self._config: dict[str, Any] = {}
        self._node_kind = "root"
        self._node_payload: Any = None
        self._designer_tabs: dict[str, FormDesignerTab] = {}
        self._designer_windows: dict[str, QMdiSubWindow] = {}
        self._tree_sync = False
        self.setWindowTitle("Configurator")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self._build_menu()
        self._build_ui()
        self._apply_classic_style()

    def _build_menu(self) -> None:
        for title in ("File", "Edit", "Configuration", "Debug", "Administration", "Service", "Windows", "Help"):
            self.menuBar().addMenu(title)
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        for caption in ("Save", "Reload", "Add Form", "Add Page", "Add Requisite"):
            action = QAction(caption, self)
            toolbar.addAction(action)

    def _build_ui(self) -> None:
        shell = QWidget()
        shell.setProperty("glass", True)
        self.setCentralWidget(shell)

        root = QVBoxLayout(shell)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        self.title_label = QLabel("Configurator")
        self.title_label.setProperty("style_", "title")
        self.path_label = QLabel("")
        self.path_label.setProperty("style_", "muted")
        self.add_form_button = QPushButton("Add form")
        self.create_module_button = QPushButton("Create module")
        self.add_form_button.setProperty("style_", "accent")
        self.save_button = QPushButton("Save")
        self.save_button.setProperty("style_", "accent")
        self.reload_button = QPushButton("Reload")
        self.close_button = QPushButton("Close")
        self.add_form_button.clicked.connect(self.add_form)
        self.create_module_button.clicked.connect(self.create_module_from_configurator)
        self.save_button.clicked.connect(self.save_config)
        self.reload_button.clicked.connect(self.reload_config)
        self.close_button.clicked.connect(self.close)
        header.addWidget(self.title_label)
        header.addWidget(self.path_label)
        header.addStretch(1)
        header.addWidget(self.create_module_button)
        header.addWidget(self.add_form_button)
        header.addWidget(self.reload_button)
        header.addWidget(self.save_button)
        header.addWidget(self.close_button)
        root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._on_tree_changed)
        self.tree.itemChanged.connect(self._on_tree_item_renamed)
        splitter.addWidget(self.tree)

        center_splitter = QSplitter(Qt.Orientation.Vertical)
        center_splitter.setChildrenCollapsible(False)
        splitter.addWidget(center_splitter)

        self.workspace_mdi = QMdiArea()
        self.workspace_mdi.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.workspace_mdi.setTabsClosable(False)
        self.workspace_mdi.setOption(QMdiArea.AreaOption.DontMaximizeSubWindowOnActivation, True)
        center_splitter.addWidget(self.workspace_mdi)

        self.bottom_tabs = QTabWidget()
        center_splitter.addWidget(self.bottom_tabs)
        center_splitter.setSizes([700, 260])

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        splitter.addWidget(right_panel)
        splitter.setSizes([260, 980, 320])

        prop_title = QLabel("Properties")
        prop_title.setProperty("style_", "title")
        right_layout.addWidget(prop_title)

        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)
        self.prop_name = QLineEdit()
        self.prop_type = QComboBox()
        self.prop_type.addItems(["button", "label", "input", "checkbox", "String", "Boolean", "Number"])
        self.prop_text = QLineEdit()
        self.prop_requisite = QComboBox()
        self.prop_command = QComboBox()
        self.prop_target_form = QComboBox()
        self.prop_target_page = QComboBox()
        self.prop_x = QLineEdit()
        self.prop_y = QLineEdit()
        self.prop_w = QLineEdit()
        self.prop_h = QLineEdit()
        self.prop_value = QTextEdit()
        self.prop_value.setMaximumHeight(140)
        form_layout.addRow("Name", self.prop_name)
        form_layout.addRow("Type", self.prop_type)
        form_layout.addRow("Text", self.prop_text)
        form_layout.addRow("Requisite", self.prop_requisite)
        form_layout.addRow("Command", self.prop_command)
        form_layout.addRow("Target form", self.prop_target_form)
        form_layout.addRow("Target page", self.prop_target_page)
        form_layout.addRow("X", self.prop_x)
        form_layout.addRow("Y", self.prop_y)
        form_layout.addRow("Width", self.prop_w)
        form_layout.addRow("Height", self.prop_h)
        form_layout.addRow("Value", self.prop_value)
        right_layout.addWidget(form)

        self.apply_button = QPushButton("Apply")
        self.apply_button.setProperty("style_", "accent")
        self.apply_button.clicked.connect(self.apply_properties)
        right_layout.addWidget(self.apply_button)
        right_layout.addStretch(1)

        self.prop_target_form.currentIndexChanged.connect(self._reload_target_pages)

        self._build_bottom_tabs()

    def _apply_classic_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #d9d4bd;
                color: #3e3a2d;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QTreeWidget, QListWidget, QTextEdit, QLineEdit, QComboBox, QTabWidget::pane, QMdiArea {
                background: #f2f0df;
                border: 1px solid #b2ac95;
                color: #3e3a2d;
            }
            QTreeWidget::item:selected, QListWidget::item:selected {
                background: #9fb9e6;
                color: #1f2633;
            }
            QMenuBar, QToolBar {
                background: #d7d1b7;
                border: 1px solid #b2ac95;
            }
            QPushButton, QToolButton {
                background: #e8e2ca;
                border: 1px solid #b2ac95;
                padding: 4px 8px;
                min-height: 22px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #f1ecd6;
            }
            QLabel[style_="title"] {
                font-weight: 600;
                color: #3c3a2f;
            }
            """
        )

    def _build_bottom_tabs(self) -> None:
        self.module_info = QTextEdit()
        self.module_info.setReadOnly(True)
        self.bottom_tabs.addTab(self.module_info, "Module")

        req_page = QWidget()
        req_layout = QVBoxLayout(req_page)
        req_layout.setContentsMargins(8, 8, 8, 8)
        req_layout.setSpacing(8)
        req_actions = QHBoxLayout()
        self.req_add = QPushButton("Add requisite")
        self.req_remove = QPushButton("Remove requisite")
        self.req_add.clicked.connect(self.add_requisite)
        self.req_remove.clicked.connect(self.remove_requisite)
        req_actions.addWidget(self.req_add)
        req_actions.addWidget(self.req_remove)
        req_actions.addStretch(1)
        req_layout.addLayout(req_actions)
        self.requisites_list = QListWidget()
        self.requisites_list.currentItemChanged.connect(self._on_requisite_clicked)
        req_layout.addWidget(self.requisites_list, 1)
        self.bottom_tabs.addTab(req_page, "Requisites")

        cmd_page = QWidget()
        cmd_layout = QVBoxLayout(cmd_page)
        cmd_layout.setContentsMargins(8, 8, 8, 8)
        cmd_layout.setSpacing(8)
        cmd_actions = QHBoxLayout()
        self.cmd_add = QPushButton("Add command")
        self.cmd_remove = QPushButton("Remove command")
        self.cmd_add.clicked.connect(self.add_command)
        self.cmd_remove.clicked.connect(self.remove_command)
        cmd_actions.addWidget(self.cmd_add)
        cmd_actions.addWidget(self.cmd_remove)
        cmd_actions.addStretch(1)
        cmd_layout.addLayout(cmd_actions)
        self.commands_list = QListWidget()
        self.commands_list.currentItemChanged.connect(self._on_command_clicked)
        cmd_layout.addWidget(self.commands_list, 1)
        self.bottom_tabs.addTab(cmd_page, "Commands")

        self.code_editor = QTextEdit()
        self.bottom_tabs.addTab(self.code_editor, "Code")

    def open_context(self, context: str) -> None:
        self._current_context = context or "app"
        self.reload_config()
        self.show()
        self.raise_()
        self.activateWindow()

    def reload_config(self) -> None:
        self._config = self._normalize_config(self._load_context_config(self._current_context))
        label = "Application" if self._current_context == "app" else self._current_context
        self.title_label.setText(f"Configurator: {label}")
        self.path_label.setText(self._current_context)
        self._rebuild_tree()
        self._rebuild_workspace()
        self._refresh_lists()
        self._refresh_module_info()

    def _load_context_config(self, context: str) -> dict[str, Any]:
        if context == "app":
            theme = self.core.get_setting("theme", "dark")
            return self.core.get_setting(
                "app_config",
                {
                    "module_id": "app",
                    "title": "Application",
                    "forms": [
                        {
                            "id": "menu_form",
                            "name": "MenuForm",
                            "title": "Main menu",
                            "width": 1180,
                            "height": 720,
                            "pages": [
                                {
                                    "id": "dashboard_page",
                                    "name": "DashboardPage",
                                    "title": "Dashboard",
                                    "controls": [
                                        {
                                            "id": "menu_title",
                                            "type": "label",
                                            "text": "Main menu",
                                            "x": 34,
                                            "y": 24,
                                            "w": 320,
                                            "h": 36,
                                            "requisite": "",
                                            "command": "",
                                            "target_form": "",
                                            "target_page": "",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                    "styles": {
                        "theme": theme,
                        "mode": "glass",
                        "sidebar": {"collapsed_width": 18, "open_width": 136},
                    },
                    "requisites": [
                        {"name": "Theme", "type": "String", "default": theme},
                        {"name": "Snap", "type": "Boolean", "default": True},
                    ],
                    "commands": [
                        {"name": "OpenModule", "handler": "open_module", "target_form": "", "target_page": "", "parameter": ""}
                    ],
                    "code": "def open_module(module_id):\n    return modules.call(module_id, 'open', {})\n",
                },
            )
        config = deepcopy(self.core.modules.get_module_config(context))
        if context == "sql_console":
            forms = config.get("forms", [])
            page_ids = {page.get("id") for form in forms for page in form.get("pages", [])}
            if "sql_data" not in page_ids or "sql_terminal" not in page_ids:
                config = deepcopy(self.core.modules.build_default_config("sql_console"))
        return config

    def _normalize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        data = deepcopy(config)
        data.setdefault("module_id", self._current_context)
        data.setdefault("title", self._current_context)
        forms = data.get("forms")
        legacy_form = data.pop("form", None)
        if not forms:
            if legacy_form:
                forms = [
                    {
                        "id": "main_form",
                        "name": "MainForm",
                        "title": legacy_form.get("caption", data["title"]),
                        "width": legacy_form.get("size", {}).get("width", 960),
                        "height": legacy_form.get("size", {}).get("height", 620),
                        "pages": [{"id": "main_page", "name": "MainPage", "title": "Main Page", "controls": []}],
                    }
                ]
            else:
                forms = [
                    {
                        "id": "main_form",
                        "name": "MainForm",
                        "title": data["title"],
                        "width": 960,
                        "height": 620,
                        "pages": [{"id": "main_page", "name": "MainPage", "title": "Main Page", "controls": []}],
                    }
                ]
        data["forms"] = forms
        data.setdefault("styles", {})
        data.setdefault("requisites", [])
        data.setdefault("commands", [])
        data.setdefault("code", "")
        for form in data["forms"]:
            form.setdefault("id", make_id("form"))
            form.setdefault("name", form.get("title", "Form"))
            form.setdefault("title", form.get("name", "Form"))
            form.setdefault("width", 960)
            form.setdefault("height", 620)
            pages = form.setdefault("pages", [])
            if not pages:
                pages.append({"id": make_id("page"), "name": "Page1", "title": "Page 1", "controls": []})
            for page in pages:
                page.setdefault("id", make_id("page"))
                page.setdefault("name", page.get("title", "Page"))
                page.setdefault("title", page.get("name", "Page"))
                page.setdefault("controls", [])
                for control in page["controls"]:
                    control.setdefault("id", make_id(control.get("type", "control")))
                    control.setdefault("type", "button")
                    control.setdefault("text", control["type"].title())
                    control.setdefault("x", 24)
                    control.setdefault("y", 24)
                    control.setdefault("w", 140)
                    control.setdefault("h", 34)
                    control.setdefault("requisite", "")
                    control.setdefault("command", "")
                    control.setdefault("target_form", "")
                    control.setdefault("target_page", "")
        return data

    def _rebuild_tree(self) -> None:
        self._tree_sync = True
        self.tree.clear()
        root = QTreeWidgetItem([self._config.get("title", self._current_context)])
        root.setData(0, Qt.ItemDataRole.UserRole, ("root", self._config))
        self._mark_item_editable(root)
        self.tree.addTopLevelItem(root)

        forms_root = QTreeWidgetItem(["Forms"])
        forms_root.setData(0, Qt.ItemDataRole.UserRole, ("forms", self._config["forms"]))
        self._mark_item_editable(forms_root)
        root.addChild(forms_root)
        for form in self._config["forms"]:
            form_item = QTreeWidgetItem([form["name"]])
            form_item.setData(0, Qt.ItemDataRole.UserRole, ("form", form))
            self._mark_item_editable(form_item)
            forms_root.addChild(form_item)
            for page in form["pages"]:
                page_item = QTreeWidgetItem([page["name"]])
                page_item.setData(0, Qt.ItemDataRole.UserRole, ("page", page))
                self._mark_item_editable(page_item)
                form_item.addChild(page_item)
                for control in page["controls"]:
                    control_item = QTreeWidgetItem([control.get("text") or control["id"]])
                    control_item.setData(0, Qt.ItemDataRole.UserRole, ("control", control))
                    self._mark_item_editable(control_item)
                    page_item.addChild(control_item)

        req_root = QTreeWidgetItem(["Requisites"])
        req_root.setData(0, Qt.ItemDataRole.UserRole, ("requisites", self._config["requisites"]))
        self._mark_item_editable(req_root)
        root.addChild(req_root)
        for item in self._config["requisites"]:
            node = QTreeWidgetItem([item.get("name", "Requisite")])
            node.setData(0, Qt.ItemDataRole.UserRole, ("requisite", item))
            self._mark_item_editable(node)
            req_root.addChild(node)

        cmd_root = QTreeWidgetItem(["Commands"])
        cmd_root.setData(0, Qt.ItemDataRole.UserRole, ("commands", self._config["commands"]))
        self._mark_item_editable(cmd_root)
        root.addChild(cmd_root)
        for item in self._config["commands"]:
            node = QTreeWidgetItem([item.get("name", "Command")])
            node.setData(0, Qt.ItemDataRole.UserRole, ("command", item))
            self._mark_item_editable(node)
            cmd_root.addChild(node)

        style_item = QTreeWidgetItem(["Styles"])
        style_item.setData(0, Qt.ItemDataRole.UserRole, ("styles", self._config["styles"]))
        self._mark_item_editable(style_item)
        root.addChild(style_item)
        code_item = QTreeWidgetItem(["Code"])
        code_item.setData(0, Qt.ItemDataRole.UserRole, ("code", {"code": self._config.get("code", "")}))
        self._mark_item_editable(code_item)
        root.addChild(code_item)
        self.tree.expandAll()
        self.tree.setCurrentItem(root)
        self._tree_sync = False

    @staticmethod
    def _mark_item_editable(item: QTreeWidgetItem) -> None:
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

    def _rebuild_workspace(self) -> None:
        for subwindow in self.workspace_mdi.subWindowList():
            subwindow.close()
        self.workspace_mdi.closeAllSubWindows()
        self._designer_tabs.clear()
        self._designer_windows.clear()
        for form in self._config["forms"]:
            tab = FormDesignerTab(form)
            tab.selected.connect(self._on_canvas_selected)
            tab.changed.connect(self._on_designer_changed)
            self._designer_tabs[form["id"]] = tab
            subwindow = QMdiSubWindow()
            subwindow.setWidget(tab)
            subwindow.setWindowTitle(form["name"])
            subwindow.resize(int(form.get("width", 960)), int(form.get("height", 620)))
            self.workspace_mdi.addSubWindow(subwindow)
            subwindow.show()
            self._designer_windows[form["id"]] = subwindow
        self.code_editor.setPlainText(self._config.get("code", ""))

    def _refresh_lists(self) -> None:
        self.requisites_list.clear()
        for item in self._config["requisites"]:
            self.requisites_list.addItem(item.get("name", "Requisite"))
        self.commands_list.clear()
        for item in self._config["commands"]:
            self.commands_list.addItem(item.get("name", "Command"))

    def _refresh_module_info(self) -> None:
        lines = [
            f"context = {self._current_context}",
            f"forms = {len(self._config['forms'])}",
            f"requisites = {len(self._config['requisites'])}",
            f"commands = {len(self._config['commands'])}",
            "",
            "forms tree:",
        ]
        for form in self._config["forms"]:
            lines.append(f"- {form['name']} ({len(form['pages'])} page(s))")
            for page in form["pages"]:
                lines.append(f"  - {page['name']} [{len(page['controls'])} controls]")
        self.module_info.setPlainText("\n".join(lines))

    def _on_designer_changed(self) -> None:
        self._rebuild_tree()
        self._refresh_module_info()

    def _on_canvas_selected(self, form_id: str, page_id: str, control_id: str) -> None:
        control = None
        for form in self._config["forms"]:
            if form["id"] != form_id:
                continue
            for page in form["pages"]:
                if page["id"] != page_id:
                    continue
                for item in page["controls"]:
                    if item["id"] == control_id:
                        control = item
                        break
        if control is None:
            return
        self._set_selection("control", control)
        self.bottom_tabs.setCurrentIndex(0)

    def _on_tree_changed(self, current, previous) -> None:
        if current is None:
            return
        kind, payload = current.data(0, Qt.ItemDataRole.UserRole)
        self._set_selection(kind, payload)
        if kind == "form":
            self._open_form_tab(payload["id"])
        elif kind == "page":
            self._open_page(payload["id"])
        elif kind == "control":
            self._open_control(payload["id"])

    def _on_tree_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._tree_sync:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        kind, payload = data
        new_name = item.text(0).strip()
        if not new_name:
            return
        if isinstance(payload, dict):
            if kind in {"form", "page", "requisite", "command"}:
                payload["name"] = new_name
            if kind == "control":
                payload["text"] = new_name
            if kind == "root":
                payload["title"] = new_name
        if kind in {"form", "page", "control"}:
            self._rebuild_workspace()
        self._refresh_lists()
        self._refresh_module_info()

    def _set_selection(self, kind: str, payload: Any) -> None:
        self._node_kind = kind
        self._node_payload = payload
        self._fill_properties(kind, payload)

    def _fill_properties(self, kind: str, payload: Any) -> None:
        self.prop_name.setText(payload.get("name", payload.get("title", "")) if isinstance(payload, dict) else "")
        self._set_combo_value(self.prop_type, payload.get("type", kind) if isinstance(payload, dict) else kind)
        self.prop_text.setText(payload.get("text", payload.get("title", "")) if isinstance(payload, dict) else "")
        self._reload_property_sources(payload if isinstance(payload, dict) else {})
        self.prop_x.setText(str(payload.get("x", "")) if isinstance(payload, dict) else "")
        self.prop_y.setText(str(payload.get("y", "")) if isinstance(payload, dict) else "")
        self.prop_w.setText(str(payload.get("w", payload.get("width", ""))) if isinstance(payload, dict) else "")
        self.prop_h.setText(str(payload.get("h", payload.get("height", ""))) if isinstance(payload, dict) else "")
        if kind == "code":
            self.prop_value.setPlainText(payload.get("code", ""))
        elif kind in {"styles", "root", "forms", "requisites", "commands"}:
            self.prop_value.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))
        elif kind == "requisite":
            self.prop_value.setPlainText(str(payload.get("default", "")))
        elif kind == "command":
            self.prop_value.setPlainText(str(payload.get("parameter", "")))
        else:
            self.prop_value.setPlainText("")

    def _reload_property_sources(self, payload: dict[str, Any]) -> None:
        self._fill_combo(self.prop_requisite, [""] + [item.get("name", "") for item in self._config.get("requisites", [])], payload.get("requisite", ""))
        self._fill_combo(self.prop_command, [""] + [item.get("name", "") for item in self._config.get("commands", [])], payload.get("command", payload.get("handler", "")))
        form_ids = [form.get("id", "") for form in self._config.get("forms", [])]
        self._fill_combo(self.prop_target_form, [""] + form_ids, payload.get("target_form", ""))
        self._reload_target_pages(payload.get("target_page", ""))

    def _reload_target_pages(self, value: str | int | None = None) -> None:
        selected_form = self.prop_target_form.currentText()
        pages = [""]
        if selected_form:
            for form in self._config.get("forms", []):
                if form.get("id") == selected_form:
                    pages.extend(page.get("id", "") for page in form.get("pages", []))
                    break
        selected_page = value if isinstance(value, str) else ""
        if isinstance(value, int):
            selected_page = self.prop_target_page.currentText()
        self._fill_combo(self.prop_target_page, pages, selected_page)

    def _open_form_tab(self, form_id: str) -> None:
        window = self._designer_windows.get(form_id)
        if window is None:
            return
        self.workspace_mdi.setActiveSubWindow(window)
        window.showNormal()

    def _open_page(self, page_id: str) -> None:
        for form in self._config["forms"]:
            for index, page in enumerate(form["pages"]):
                if page["id"] == page_id:
                    tab = self._designer_tabs.get(form["id"])
                    if tab:
                        window = self._designer_windows.get(form["id"])
                        if window:
                            self.workspace_mdi.setActiveSubWindow(window)
                        tab.page_selector.setCurrentIndex(index)
                    return

    def _open_control(self, control_id: str) -> None:
        for form in self._config["forms"]:
            for page_index, page in enumerate(form["pages"]):
                for control in page["controls"]:
                    if control["id"] == control_id:
                        tab = self._designer_tabs.get(form["id"])
                        if tab:
                            window = self._designer_windows.get(form["id"])
                            if window:
                                self.workspace_mdi.setActiveSubWindow(window)
                            tab.page_selector.setCurrentIndex(page_index)
                            tab.canvas.select_control(control_id)
                        return

    def add_form(self) -> None:
        index = len(self._config["forms"]) + 1
        form = {
            "id": make_id("form"),
            "name": f"Form{index}",
            "title": f"Form {index}",
            "width": 960,
            "height": 620,
            "pages": [{"id": make_id("page"), "name": "Page1", "title": "Page 1", "controls": []}],
        }
        self._config["forms"].append(form)
        self._rebuild_tree()
        self._rebuild_workspace()
        self._refresh_module_info()
        self._open_form_tab(form["id"])

    def create_module_from_configurator(self) -> None:
        module_id, ok = QInputDialog.getText(self, "Create module", "Module ID (latin, underscore)")
        if not ok or not module_id.strip():
            return
        name, ok = QInputDialog.getText(self, "Create module", "Module name")
        if not ok or not name.strip():
            return
        try:
            self.core.call_api("app.create_module", module_id=module_id.strip(), name=name.strip())
        except Exception as exc:
            QMessageBox.warning(self, "Create module", str(exc))
            return
        self.core.modules.discover()
        QMessageBox.information(self, "Create module", f"Module '{module_id.strip()}' created.")

    def add_requisite(self) -> None:
        self._config["requisites"].append({"name": f"Requisite{len(self._config['requisites']) + 1}", "type": "String", "default": ""})
        self._refresh_lists()
        self._rebuild_tree()
        self._refresh_module_info()

    def remove_requisite(self) -> None:
        row = self.requisites_list.currentRow()
        if row < 0:
            return
        self._config["requisites"].pop(row)
        self._refresh_lists()
        self._rebuild_tree()
        self._refresh_module_info()

    def add_command(self) -> None:
        self._config["commands"].append(
            {
                "name": f"Command{len(self._config['commands']) + 1}",
                "handler": "handler_name",
                "target_form": "",
                "target_page": "",
                "parameter": "",
            }
        )
        self._refresh_lists()
        self._rebuild_tree()
        self._refresh_module_info()

    def remove_command(self) -> None:
        row = self.commands_list.currentRow()
        if row < 0:
            return
        self._config["commands"].pop(row)
        self._refresh_lists()
        self._rebuild_tree()
        self._refresh_module_info()

    def _on_requisite_clicked(self, current, previous) -> None:
        row = self.requisites_list.currentRow()
        if row < 0:
            return
        self._set_selection("requisite", self._config["requisites"][row])

    def _on_command_clicked(self, current, previous) -> None:
        row = self.commands_list.currentRow()
        if row < 0:
            return
        self._set_selection("command", self._config["commands"][row])

    def apply_properties(self) -> None:
        kind = self._node_kind
        payload = self._node_payload
        if not isinstance(payload, dict):
            return

        if kind == "control":
            payload["text"] = self.prop_text.text()
            payload["type"] = self.prop_type.currentText() or payload.get("type", "button")
            payload["requisite"] = self.prop_requisite.currentText()
            payload["command"] = self.prop_command.currentText()
            payload["target_form"] = self.prop_target_form.currentText()
            payload["target_page"] = self.prop_target_page.currentText()
            payload["x"] = self._as_int(self.prop_x.text(), payload.get("x", 0))
            payload["y"] = self._as_int(self.prop_y.text(), payload.get("y", 0))
            payload["w"] = self._as_int(self.prop_w.text(), payload.get("w", 140))
            payload["h"] = self._as_int(self.prop_h.text(), payload.get("h", 34))
        elif kind == "form":
            payload["name"] = self.prop_name.text() or payload["name"]
            payload["title"] = self.prop_text.text() or payload["title"]
            payload["width"] = self._as_int(self.prop_w.text(), payload.get("width", 960))
            payload["height"] = self._as_int(self.prop_h.text(), payload.get("height", 620))
        elif kind == "page":
            payload["name"] = self.prop_name.text() or payload["name"]
            payload["title"] = self.prop_text.text() or payload["title"]
        elif kind == "requisite":
            payload["name"] = self.prop_name.text() or payload["name"]
            payload["type"] = self.prop_type.currentText() or payload["type"]
            payload["default"] = self.prop_value.toPlainText()
        elif kind == "command":
            payload["name"] = self.prop_name.text() or payload["name"]
            payload["handler"] = self.prop_command.currentText() or payload.get("handler", "")
            payload["target_form"] = self.prop_target_form.currentText()
            payload["target_page"] = self.prop_target_page.currentText()
            payload["parameter"] = self.prop_value.toPlainText()
        elif kind == "styles":
            try:
                self._config["styles"] = json.loads(self.prop_value.toPlainText() or "{}")
            except json.JSONDecodeError:
                pass
        elif kind == "code":
            self._config["code"] = self.prop_value.toPlainText()
            self.code_editor.setPlainText(self._config["code"])

        for tab in self._designer_tabs.values():
            tab.canvas.render_page()
        self._refresh_lists()
        self._refresh_module_info()
        self._rebuild_tree()

    def save_config(self) -> None:
        self._config["code"] = self.code_editor.toPlainText()
        if self._current_context == "app":
            self.core.set_setting("app_config", self._config)
            theme = self._config.get("styles", {}).get("theme")
            if theme:
                self.core.call_api("app.set_theme", theme=theme)
        else:
            self.core.modules.save_module_config(self._current_context, self._config)
        self._refresh_module_info()

    @staticmethod
    def _as_int(raw: str, fallback: int) -> int:
        try:
            return int(raw)
        except ValueError:
            return fallback

    @staticmethod
    def _fill_combo(combo: QComboBox, values: list[str], current: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        index = combo.findText(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)

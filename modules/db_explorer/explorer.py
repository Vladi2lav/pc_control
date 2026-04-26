"""
Database and SQL test module.
"""

from __future__ import annotations

import json
import time
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from components.module_system import BaseModule


class DBExplorerModule(BaseModule):
    def __init__(self, core, parent=None, **kwargs):
        super().__init__(core=core, parent=parent, **kwargs)
        self._current_table = "records"
        self.widget = QWidget(parent)
        self._build_ui()
        self.register_local_api(
            {
                "health": self.api_health,
                "run_sql": self.api_run_sql,
                "summary": self.api_summary,
            }
        )
        self.refresh_table()
        self.refresh_summary()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self.widget)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("SQL Console")
        title.setProperty("style_", "title")
        subtitle = QLabel("Database check, raw SQL, and service calls")
        subtitle.setProperty("style_", "muted")
        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(2)
        title_wrap.addWidget(title)
        title_wrap.addWidget(subtitle)
        header.addLayout(title_wrap)
        header.addStretch(1)

        # Temporarily removed config and runtime buttons to fix AttributeError

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._build_data_tab()
        self._build_sql_tab()
        self._build_service_tab()

    def _build_data_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.btn_records = QPushButton("records")
        self.btn_kv = QPushButton("kv_store")
        self.btn_events = QPushButton("event_log")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setProperty("style_", "accent")
        for button, table in (
            (self.btn_records, "records"),
            (self.btn_kv, "kv_store"),
            (self.btn_events, "event_log"),
        ):
            button.clicked.connect(lambda checked=False, t=table: self.set_table(t))
            top.addWidget(button)
        top.addStretch(1)
        self.btn_refresh.clicked.connect(self.refresh_table)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        self.table_list = QListWidget()
        self.table_details = QTextEdit()
        self.table_details.setReadOnly(True)
        self.table_list.currentItemChanged.connect(self._show_current_row)
        splitter.addWidget(self.table_list)
        splitter.addWidget(self.table_details)
        splitter.setSizes([430, 530])

        footer = QHBoxLayout()
        self.table_status = QLabel("Ready")
        self.table_status.setProperty("style_", "muted")
        self.table_count = QLabel("")
        self.table_count.setProperty("style_", "accent")
        footer.addWidget(self.table_status)
        footer.addStretch(1)
        footer.addWidget(self.table_count)
        layout.addLayout(footer)

        self.tabs.addTab(page, "Data")

    def _build_sql_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText(
            "SELECT * FROM records LIMIT 20;\nUPDATE kv_store SET value='demo' WHERE key='theme';"
        )
        self.sql_input.setMinimumHeight(140)
        layout.addWidget(self.sql_input)

        actions = QHBoxLayout()
        self.btn_run_sql = QPushButton("Run SQL")
        self.btn_run_sql.setProperty("style_", "accent")
        self.btn_clear_sql = QPushButton("Clear")
        self.btn_examples = QPushButton("Insert example")
        self.btn_run_sql.clicked.connect(self.run_sql)
        self.btn_clear_sql.clicked.connect(self._clear_sql)
        self.btn_examples.clicked.connect(self._fill_example)
        actions.addWidget(self.btn_run_sql)
        actions.addWidget(self.btn_clear_sql)
        actions.addWidget(self.btn_examples)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.sql_output = QTextEdit()
        self.sql_output.setReadOnly(True)
        layout.addWidget(self.sql_output, 1)

        self.sql_status = QLabel("Ready")
        self.sql_status.setProperty("style_", "muted")
        layout.addWidget(self.sql_status)

        self.tabs.addTab(page, "SQL")

    def _build_service_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        actions = QHBoxLayout()
        self.btn_add_record = QPushButton("Add test record")
        self.btn_add_record.setProperty("style_", "accent")
        self.btn_log_event = QPushButton("Write event")
        self.btn_log_event.setProperty("style_", "accent")
        self.btn_summary = QPushButton("Refresh status")
        self.btn_summary.clicked.connect(self.refresh_summary)
        self.btn_add_record.clicked.connect(self.add_test_record)
        self.btn_log_event.clicked.connect(self.log_event)
        actions.addWidget(self.btn_add_record)
        actions.addWidget(self.btn_log_event)
        actions.addWidget(self.btn_summary)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        layout.addWidget(self.summary_output, 1)

        self.tabs.addTab(page, "Service")

    def _clear_sql(self) -> None:
        self.sql_output.clear()
        self.sql_status.setText("Cleared")

    def _fill_example(self) -> None:
        self.sql_input.setPlainText(
            "SELECT * FROM records LIMIT 20;\n"
            "SELECT * FROM kv_store;\n"
            "SELECT * FROM event_log ORDER BY id DESC LIMIT 10;"
        )

    def _show_current_row(self, current, previous) -> None:
        if current is None:
            self.table_details.clear()
            return
        payload = current.data(Qt.ItemDataRole.UserRole)
        self.table_details.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def set_table(self, table: str) -> None:
        self._current_table = table
        self.refresh_table()

    def refresh_table(self) -> None:
        rows = self.core.run_sync(self.core.db.get_all(self._current_table, limit=200))
        self.table_list.clear()
        for row in rows:
            title = row.get("key") or row.get("event_type") or row.get("namespace") or row.get("id")
            preview = json.dumps(row, ensure_ascii=False, default=str)
            item = QListWidgetItem(str(title))
            item.setToolTip(preview)
            item.setData(Qt.ItemDataRole.UserRole, row)
            self.table_list.addItem(item)
        if rows:
            self.table_list.setCurrentRow(0)
        self.table_status.setText(f"Table: {self._current_table}")
        self.table_count.setText(f"{len(rows)} rows")

    def run_sql(self) -> None:
        source = self.sql_input.toPlainText().strip()
        if not source:
            self.sql_status.setText("SQL is empty")
            return

        statements = [part.strip() for part in source.split(";") if part.strip()]
        self.sql_output.append(">>> run")
        errors = 0
        for statement in statements:
            self.sql_output.append(f"SQL> {statement}")
            try:
                result = self.core.run_sync(self.core.db.execute(statement))
                if result["mode"] == "rows":
                    if not result["rows"]:
                        self.sql_output.append("(no rows)\n")
                    else:
                        for row in result["rows"][:100]:
                            self.sql_output.append(json.dumps(row, ensure_ascii=False, default=str))
                        if len(result["rows"]) > 100:
                            self.sql_output.append(f"... and {len(result['rows']) - 100} more rows")
                        self.sql_output.append("")
                else:
                    self.sql_output.append(f"affected={result['rowcount']}\n")
            except Exception as exc:
                errors += 1
                self.sql_output.append(f"ERROR: {exc}\n")
        self.sql_status.setText(f"Completed: {len(statements)} statement(s), errors={errors}")
        self.refresh_summary()
        self.refresh_table()

    def add_test_record(self) -> None:
        payload = {
            "table_name": "test",
            "key": f"ping_{int(time.time())}",
            "value": {"timestamp": time.time(), "module": "sql_console"},
            "text_data": "test row from sql module",
        }
        self.core.run_sync(self.core.db.add("records", payload))
        self.refresh_summary()
        self.refresh_table()

    def log_event(self) -> None:
        self.core.run_sync(
            self.core.db.log_event(
                "sql_console",
                "manual_test",
                {"at": time.time(), "source": "ui"},
            )
        )
        self.refresh_summary()

    def refresh_summary(self) -> None:
        summary = self.core.run_sync(self.core.db.get_summary())
        lines = [f"db_ready = {summary['ready']}"]
        for table, count in summary["tables"].items():
            lines.append(f"{table}: {count}")
        lines.append("")
        lines.append("api routes:")
        for route in self.core.list_api():
            if route.startswith("sql_console.") or route.startswith("app.") or route.startswith("modules."):
                lines.append(f" - {route}")
        self.summary_output.setPlainText("\n".join(lines))

    def api_health(self) -> dict[str, Any]:
        summary = self.core.run_sync(self.core.db.get_summary())
        return {"module": "sql_console", "ready": summary["ready"], "tables": summary["tables"]}

    def api_run_sql(self, sql: str) -> dict[str, Any]:
        return self.core.run_sync(self.core.db.execute(sql))

    def api_summary(self) -> dict[str, Any]:
        return self.core.run_sync(self.core.db.get_summary())

    def safe_close(self) -> None:
        super().safe_close()

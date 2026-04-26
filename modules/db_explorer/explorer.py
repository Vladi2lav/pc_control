"""
modules/db_explorer/explorer.py — Бекенд DB Explorer модуля. Документация: docs/explorer.md
"""

import json
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QObject, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor

_MODULE_DIR = Path(__file__).resolve().parent
_LAYOUT_XML = _MODULE_DIR / "layout.xml"

logger = logging.getLogger("db_explorer")

# ─── Вспомогательные стили ────────────────────────────────────────────────────

_TAB_ACTIVE = """
    QPushButton {
        background: rgba(100,160,255,0.18);
        border: 1px solid rgba(100,160,255,0.40);
        border-radius: 10px;
        color: #7EB8F7;
        font-size: 12px;
        font-weight: 600;
        padding: 6px 14px;
    }
"""
_TAB_IDLE = """
    QPushButton {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 10px;
        color: rgba(180,185,210,0.55);
        font-size: 12px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background: rgba(255,255,255,0.10);
        color: #D0D4E8;
    }
"""
_CHIP_ACTIVE = """
    QPushButton {
        background: rgba(100,160,255,0.15);
        border: 1px solid rgba(100,160,255,0.35);
        border-radius: 8px;
        color: #7EB8F7;
        font-size: 11px;
        padding: 4px 10px;
    }
"""
_CHIP_IDLE = """
    QPushButton {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        color: rgba(180,185,210,0.50);
        font-size: 11px;
        padding: 4px 10px;
    }
    QPushButton:hover { background: rgba(255,255,255,0.09); color: #D0D4E8; }
"""

_ROW_EVEN = "background: rgba(255,255,255,0.03); border-radius: 5px;"
_ROW_ODD  = "background: transparent; border-radius: 5px;"
_ROW_HOVER = "background: rgba(100,160,255,0.10); border-radius: 5px;"


# ─── Строка таблицы ───────────────────────────────────────────────────────────

class _TableRow(QWidget):
    def __init__(self, row_data: dict, idx: int, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ROW_EVEN if idx % 2 == 0 else _ROW_ODD)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(8)

        def cell(text: str, max_w: Optional[int] = None, stretch: int = 0) -> QLabel:
            lbl = QLabel(str(text)[:80])
            lbl.setStyleSheet(
                "color: rgba(200,205,230,0.85); font-size: 11px; background: transparent;"
            )
            if max_w:
                lbl.setMaximumWidth(max_w)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lay.addWidget(lbl, stretch)
            return lbl

        cell(row_data.get("id", "—"), max_w=40)

        # Ключ зависит от таблицы
        key = (
            row_data.get("key") or
            row_data.get("event_type") or
            row_data.get("namespace") or "—"
        )
        cell(key, max_w=120)

        val = row_data.get("value") or row_data.get("payload") or row_data.get("text_data") or "—"
        if isinstance(val, dict):
            val = json.dumps(val, ensure_ascii=False)
        cell(str(val), stretch=1)

        ts = str(row_data.get("created_at") or row_data.get("updated_at") or "")[:19]
        cell(ts, max_w=140)

        self.enterEvent  = lambda e: self.setStyleSheet(_ROW_HOVER)
        self.leaveEvent  = lambda e: self.setStyleSheet(
            _ROW_EVEN if idx % 2 == 0 else _ROW_ODD
        )


# ─── DBExplorerModule ─────────────────────────────────────────────────────────

class DBExplorerModule(QObject):

    # thread-safe сигналы
    _sig_rows      = Signal(list)
    _sig_status    = Signal(str, str)   # (text, style: accent|danger|muted)
    _sig_count     = Signal(int)
    _sig_sql_out   = Signal(str, bool)  # (text, is_error)
    _sig_kv_result = Signal(str)
    _sig_db_stat   = Signal(str)

    def __init__(self, core, parent=None, **kwargs):
        super().__init__()
        self._core     = core
        self._closing  = False
        self._cur_table = "records"

        # ── Строим виджет из XML ──────────────────────────────────────────────
        from components.UIBase import UIRenderer
        renderer = UIRenderer()

        if _LAYOUT_XML.exists():
            self.widget, self._refs = renderer.load_file(str(_LAYOUT_XML))
        else:
            raise FileNotFoundError(f"layout.xml не найден: {_LAYOUT_XML}")

        self.widget.setParent(parent)

        # ── Применяем кастомные стили ─────────────────────────────────────────
        self._apply_styles()

        # ── Подключаем сигналы к слотам UI ───────────────────────────────────
        self._sig_rows.connect(self._render_rows)
        self._sig_status.connect(self._set_status)
        self._sig_count.connect(self._set_count)
        self._sig_sql_out.connect(self._append_sql_output)
        self._sig_kv_result.connect(self._set_kv_result)
        self._sig_db_stat.connect(self._set_db_stat)

        # ── Подключаем кнопки ────────────────────────────────────────────────
        self._wire_buttons()

        # ── Первая загрузка ───────────────────────────────────────────────────
        self._switch_table("records")
        self._refresh_tools_status()

    # ── Публичный интерфейс ───────────────────────────────────────────────────

    def safe_close(self) -> None:
        self._closing = True
        logger.info("[DBExplorer] safe_close called.")

    # ── Стили компонентов ─────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        r = self._refs

        for tid, style in [
            ("tab_tables",   _TAB_ACTIVE),
            ("tab_terminal", _TAB_IDLE),
            ("tab_tools",    _TAB_IDLE),
        ]:
            if tid in r:
                r[tid].setStyleSheet(style)

        for cid in ("btn_tbl_records", "btn_tbl_kv", "btn_tbl_events"):
            if cid in r:
                r[cid].setStyleSheet(
                    _CHIP_ACTIVE if cid == "btn_tbl_records" else _CHIP_IDLE
                )

        # Заголовки колонок таблицы
        for col in ("col_id", "col_key", "col_val", "col_ts"):
            if col in r:
                r[col].setStyleSheet(
                    "color: rgba(140,148,180,0.70); font-size: 10px; "
                    "font-weight: 600; letter-spacing: 0.5px; background: transparent;"
                )

        # Заголовок таблицы-header
        if "tbl_header" in r:
            r["tbl_header"].setStyleSheet(
                "background: rgba(255,255,255,0.04); border-radius: 6px;"
            )

        # SQL output
        if "sql_output" in r:
            r["sql_output"].setStyleSheet("""
                QTextEdit {
                    background: rgba(8, 10, 18, 0.80);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 10px;
                    color: #9ECBFF;
                    font-family: 'Consolas', 'Cascadia Code', monospace;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
            r["sql_output"].setReadOnly(True)

        # SQL input
        if "sql_input" in r:
            r["sql_input"].setStyleSheet("""
                QLineEdit {
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.10);
                    border-radius: 8px;
                    color: #D0D4E8;
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                    padding: 6px 10px;
                }
                QLineEdit:focus { border-color: rgba(100,160,255,0.45); }
            """)

        # Кнопки инструментов
        accent_btn = """
            QPushButton {
                background: rgba(100,160,255,0.16);
                border: 1px solid rgba(100,160,255,0.32);
                border-radius: 9px; color: #7EB8F7;
                font-size: 12px; padding: 6px 14px;
            }
            QPushButton:hover { background: rgba(100,160,255,0.28); color: #C2DCFF; }
        """
        danger_btn = """
            QPushButton {
                background: rgba(220,60,60,0.13);
                border: 1px solid rgba(220,60,60,0.28);
                border-radius: 9px; color: #F78080;
                font-size: 12px; padding: 6px 14px;
            }
            QPushButton:hover { background: rgba(220,60,60,0.26); color: #FFAAAA; }
        """
        for bid in ("btn_sql_run", "btn_add_record", "btn_kv_set", "btn_kv_get",
                    "btn_log_event", "btn_tools_refresh", "btn_tbl_refresh"):
            if bid in r:
                r[bid].setStyleSheet(accent_btn)

        for bid in ("btn_sql_clear", "btn_delete_last", "btn_kv_del", "btn_clear_events"):
            if bid in r:
                r[bid].setStyleSheet(danger_btn)

    # ── Подключение кнопок ────────────────────────────────────────────────────

    def _wire_buttons(self) -> None:
        r = self._refs

        # ── Переключение вкладок ──────────────────────────────────────────────
        if "tab_tables"   in r: r["tab_tables"].clicked.connect(lambda: self._switch_tab("tables"))
        if "tab_terminal" in r: r["tab_terminal"].clicked.connect(lambda: self._switch_tab("terminal"))
        if "tab_tools"    in r: r["tab_tools"].clicked.connect(lambda: self._switch_tab("tools"))

        # ── Таблицы ───────────────────────────────────────────────────────────
        if "btn_tbl_records" in r:
            r["btn_tbl_records"].clicked.connect(lambda: self._switch_table("records"))
        if "btn_tbl_kv" in r:
            r["btn_tbl_kv"].clicked.connect(lambda: self._switch_table("kv_store"))
        if "btn_tbl_events" in r:
            r["btn_tbl_events"].clicked.connect(lambda: self._switch_table("event_log"))
        if "btn_tbl_refresh" in r:
            r["btn_tbl_refresh"].clicked.connect(lambda: self._switch_table(self._cur_table))

        # ── SQL терминал ──────────────────────────────────────────────────────
        if "btn_sql_run" in r:
            r["btn_sql_run"].clicked.connect(self._run_sql)
        if "btn_sql_clear" in r:
            r["btn_sql_clear"].clicked.connect(self._clear_sql)
        if "sql_input" in r:
            r["sql_input"].returnPressed.connect(self._run_sql)

        # ── Функции ───────────────────────────────────────────────────────────
        if "btn_add_record"    in r: r["btn_add_record"].clicked.connect(self._add_test_record)
        if "btn_delete_last"   in r: r["btn_delete_last"].clicked.connect(self._delete_last_record)
        if "btn_kv_set"        in r: r["btn_kv_set"].clicked.connect(self._kv_set)
        if "btn_kv_get"        in r: r["btn_kv_get"].clicked.connect(self._kv_get)
        if "btn_kv_del"        in r: r["btn_kv_del"].clicked.connect(self._kv_del)
        if "btn_log_event"     in r: r["btn_log_event"].clicked.connect(self._log_event)
        if "btn_clear_events"  in r: r["btn_clear_events"].clicked.connect(self._clear_events)
        if "btn_tools_refresh" in r: r["btn_tools_refresh"].clicked.connect(self._refresh_tools_status)

    # ── Переключение вкладок ──────────────────────────────────────────────────

    def _switch_tab(self, tab: str) -> None:
        pages = {
            "tables":   "page_tables",
            "terminal": "page_terminal",
            "tools":    "page_tools",
        }
        tabs = {
            "tables":   "tab_tables",
            "terminal": "tab_terminal",
            "tools":    "tab_tools",
        }
        r = self._refs
        for key, pid in pages.items():
            if pid in r:
                r[pid].setVisible(key == tab)
        for key, tid in tabs.items():
            if tid in r:
                r[tid].setStyleSheet(_TAB_ACTIVE if key == tab else _TAB_IDLE)

        if tab == "tables":
            self._switch_table(self._cur_table)
        elif tab == "tools":
            self._refresh_tools_status()

    # ── Таблицы ───────────────────────────────────────────────────────────────

    def _switch_table(self, table: str) -> None:
        self._cur_table = table
        r = self._refs
        chip_map = {
            "records":   "btn_tbl_records",
            "kv_store":  "btn_tbl_kv",
            "event_log": "btn_tbl_events",
        }
        for t, cid in chip_map.items():
            if cid in r:
                r[cid].setStyleSheet(_CHIP_ACTIVE if t == table else _CHIP_IDLE)

        self._sig_status.emit(f"Загрузка {table}…", "muted")
        future = self._core.submit(self._fetch_rows(table))
        future.add_done_callback(self._on_rows_fetched)

    async def _fetch_rows(self, table: str) -> dict:
        try:
            rows = await self._core.db.get_all(table, limit=200)
            return {"ok": True, "table": table, "rows": rows}
        except Exception as e:
            return {"ok": False, "table": table, "error": str(e), "rows": []}

    def _on_rows_fetched(self, future) -> None:
        try:
            data = future.result()
        except Exception as e:
            self._sig_status.emit(f"Ошибка: {e}", "danger")
            return
        if data["ok"]:
            self._sig_rows.emit(data["rows"])
            self._sig_status.emit(f"Таблица: {data['table']}", "muted")
            self._sig_count.emit(len(data["rows"]))
        else:
            self._sig_status.emit(f"Ошибка: {data['error']}", "danger")
            self._sig_rows.emit([])

    @Slot(list)
    def _render_rows(self, rows: list) -> None:
        """Перерисовывает строки в scroll-области."""
        scroll: QScrollArea = self._refs.get("tbl_scroll")
        if not scroll:
            return

        inner = scroll.widget()
        if inner is None:
            inner = QWidget()
            inner.setStyleSheet("background: transparent;")
            scroll_lay = QVBoxLayout(inner)
            scroll_lay.setContentsMargins(0, 0, 0, 0)
            scroll_lay.setSpacing(2)
            scroll.setWidget(inner)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet("background: transparent; border: none;")

        lay = inner.layout()
        # Очищаем старые строки
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rows:
            empty = QLabel("— нет данных —")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: rgba(180,185,210,0.35); font-size: 12px; padding: 20px;")
            lay.addWidget(empty)
        else:
            for i, row in enumerate(rows):
                lay.addWidget(_TableRow(row, i, inner))

        lay.addStretch()

    @Slot(str, str)
    def _set_status(self, text: str, style: str) -> None:
        lbl = self._refs.get("lbl_tbl_status")
        if lbl:
            colors = {"accent": "#7EB8F7", "danger": "#F78080", "muted": "rgba(180,185,210,0.55)"}
            lbl.setText(text)
            lbl.setStyleSheet(
                f"color: {colors.get(style, colors['muted'])}; "
                f"font-size: 11px; background: transparent;"
            )

    @Slot(int)
    def _set_count(self, count: int) -> None:
        lbl = self._refs.get("lbl_tbl_count")
        if lbl:
            lbl.setText(f"{count} записей")

    # ── SQL Терминал ──────────────────────────────────────────────────────────

    def _run_sql(self) -> None:
        inp = self._refs.get("sql_input")
        if not inp:
            return
        sql = inp.text().strip()
        if not sql:
            return
        self._sig_sql_out.emit(f"▶ {sql}", False)
        inp.clear()

        future = self._core.submit(self._exec_sql(sql))
        future.add_done_callback(self._on_sql_done)

    async def _exec_sql(self, sql: str) -> dict:
        try:
            rows = await self._core.db.execute(sql)
            return {"ok": True, "rows": rows, "sql": sql}
        except Exception as e:
            return {"ok": False, "error": str(e), "sql": sql}

    def _on_sql_done(self, future) -> None:
        try:
            data = future.result()
        except Exception as e:
            self._sig_sql_out.emit(f"⚠ {e}", True)
            return
        if data["ok"]:
            rows = data["rows"]
            if not rows:
                self._sig_sql_out.emit("  (нет результатов)", False)
            else:
                for r in rows[:100]:
                    self._sig_sql_out.emit("  " + json.dumps(r, ensure_ascii=False), False)
                if len(rows) > 100:
                    self._sig_sql_out.emit(f"  … и ещё {len(rows)-100} строк", False)
        else:
            self._sig_sql_out.emit(f"⚠ {data['error']}", True)

    @Slot(str, bool)
    def _append_sql_output(self, text: str, is_error: bool) -> None:
        out: QTextEdit = self._refs.get("sql_output")
        if not out:
            return
        color = "#FF8080" if is_error else "#9ECBFF"
        # Для команды ▶ - другой цвет
        if text.startswith("▶"):
            color = "#C8F0A0"
        out.append(f'<span style="color:{color};font-family:Consolas;font-size:12px;">'
                   f'{text.replace("<","&lt;").replace(">","&gt;")}</span>')
        sb = out.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def _clear_sql(self) -> None:
        out: QTextEdit = self._refs.get("sql_output")
        if out:
            out.clear()
        stat = self._refs.get("lbl_sql_status")
        if stat:
            stat.setText("Очищено")

    # ── Функции / Инструменты ─────────────────────────────────────────────────

    def _add_test_record(self) -> None:
        data = {
            "table_name": "test",
            "key":        f"ping_{int(time.time())}",
            "value":      {"ts": time.time(), "source": "db_explorer"},
            "text_data":  "test from db_explorer",
        }
        f = self._core.submit(self._core.db.add("records", data))
        f.add_done_callback(lambda fut: self._refresh_tools_status())

    def _delete_last_record(self) -> None:
        async def _del():
            rows = await self._core.db.get_all("records", limit=1000)
            if rows:
                await self._core.db.delete("records", rows[-1]["id"])
                return f"Удалена запись id={rows[-1]['id']}"
            return "Нет записей для удаления"
        f = self._core.submit(_del())
        f.add_done_callback(lambda fut: self._refresh_tools_status())

    def _kv_set(self) -> None:
        key = self._refs.get("inp_kv_key")
        val = self._refs.get("inp_kv_value")
        if not key or not val:
            return
        k, v = key.text().strip(), val.text().strip()
        if not k:
            return
        f = self._core.submit(self._core.db.kv_set("explorer", k, v))
        f.add_done_callback(lambda fut: self._sig_kv_result.emit(f"✓ Set: {k}={v}"))

    def _kv_get(self) -> None:
        key = self._refs.get("inp_kv_key")
        if not key:
            return
        k = key.text().strip()
        if not k:
            return
        async def _get():
            return await self._core.db.kv_get("explorer", k, default="(не найдено)")
        f = self._core.submit(_get())
        def _cb(fut):
            try:
                v = fut.result()
                self._sig_kv_result.emit(f"{k} = {v}")
            except Exception as e:
                self._sig_kv_result.emit(f"⚠ {e}")
        f.add_done_callback(_cb)

    def _kv_del(self) -> None:
        key = self._refs.get("inp_kv_key")
        if not key:
            return
        k = key.text().strip()
        if not k:
            return
        f = self._core.submit(self._core.db.kv_delete("explorer", k))
        f.add_done_callback(lambda fut: self._sig_kv_result.emit(f"✕ Удалён: {k}"))

    def _log_event(self) -> None:
        f = self._core.submit(
            self._core.db.log_event(
                "db_explorer", "manual_test",
                {"ts": time.time(), "note": "ручной тест из db_explorer"}
            )
        )
        f.add_done_callback(lambda fut: self._refresh_tools_status())

    def _clear_events(self) -> None:
        async def _clear():
            rows = await self._core.db.get_all("event_log", limit=10000)
            for r in rows:
                await self._core.db.delete("event_log", r["id"])
            return len(rows)
        f = self._core.submit(_clear())
        f.add_done_callback(lambda fut: self._refresh_tools_status())

    def _refresh_tools_status(self) -> None:
        async def _stat():
            is_ready = self._core.db.is_ready
            count = 0
            if is_ready:
                count = await self._core.db.count("records")
            return f"{'● Готова' if is_ready else '○ Нет'} | records: {count}"
        f = self._core.submit(_stat())
        def _cb(fut):
            try:
                self._sig_db_stat.emit(fut.result())
            except Exception as e:
                self._sig_db_stat.emit(f"⚠ {e}")
        f.add_done_callback(_cb)

    @Slot(str)
    def _set_kv_result(self, text: str) -> None:
        lbl = self._refs.get("lbl_kv_result")
        if lbl:
            lbl.setText(text)

    @Slot(str)
    def _set_db_stat(self, text: str) -> None:
        lbl = self._refs.get("lbl_tools_db")
        if lbl:
            lbl.setText(text)

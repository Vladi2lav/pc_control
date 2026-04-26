"""
db.py — Асинхронный модуль базы данных.

Использует SQLAlchemy 2.x + aiosqlite (для SQLite) или asyncpg (для PostgreSQL).
Запускается через CORE.py, доступен как core.db.*

Основные операции:
    core.db.add(table, data)           → добавить запись
    core.db.get(table, id)             → получить по id
    core.db.get_all(table, filters)    → получить все (с фильтрами)
    core.db.update(table, id, data)    → обновить запись
    core.db.delete(table, id)          → удалить запись
    core.db.execute(sql, params)       → сырой SQL-запрос
    core.db.close()                    → корректное закрытие сессии
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Text, Boolean, Float,
    inspect as sa_inspect, text, MetaData, Table, select, update, delete, insert
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

logger = logging.getLogger("db")

# ─── Конфигурация URL ────────────────────────────────────────────────────────

_RAW_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

def _make_async_url(url: str) -> str:
    """Конвертирует sync URL в async-совместимый драйвер."""
    if url.startswith("sqlite:///"):
        # sqlite:/// → sqlite+aiosqlite:///
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
            "postgres://", "postgresql+asyncpg://", 1
        )
    return url

DATABASE_URL = _make_async_url(_RAW_URL)

# ─── ORM Base ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass

# ─── Встроенные универсальные модели ─────────────────────────────────────────

class GenericRecord(Base):
    """Универсальная таблица для произвольных JSON-данных."""
    __tablename__ = "records"

    id         = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(128), nullable=False, index=True)
    key        = Column(String(256), nullable=True, index=True)
    value      = Column(JSON,    nullable=True)
    text_data  = Column(Text,    nullable=True)
    num_data   = Column(Float,   nullable=True)
    flag       = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":         self.id,
            "table_name": self.table_name,
            "key":        self.key,
            "value":      self.value,
            "text_data":  self.text_data,
            "num_data":   self.num_data,
            "flag":       self.flag,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }


class KVStore(Base):
    """Key-Value хранилище настроек / состояния."""
    __tablename__ = "kv_store"

    id         = Column(Integer, primary_key=True, index=True)
    namespace  = Column(String(128), default="global", index=True)
    key        = Column(String(256), nullable=False, index=True)
    value      = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":        self.id,
            "namespace": self.namespace,
            "key":       self.key,
            "value":     self.value,
            "updated_at": str(self.updated_at),
        }


class EventLog(Base):
    """Журнал событий системы."""
    __tablename__ = "event_log"

    id         = Column(Integer, primary_key=True, index=True)
    source     = Column(String(128), nullable=True)
    event_type = Column(String(128), nullable=False)
    payload    = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":         self.id,
            "source":     self.source,
            "event_type": self.event_type,
            "payload":    self.payload,
            "created_at": str(self.created_at),
        }

# ─── Движок и сессия ─────────────────────────────────────────────────────────

_engine: Optional[Any] = None
_session_factory: Optional[async_sessionmaker] = None
_ready = asyncio.Event()
_closed = False

# ─── DatabaseManager ─────────────────────────────────────────────────────────

class DatabaseManager:
    """
    Главный интерфейс БД. Используется через core.db.*

    Пример:
        await core.db.add("records", {"table_name": "users", "key": "name", "value": "Vlad"})
        row = await core.db.get("records", 1)
        rows = await core.db.get_all("records", {"table_name": "users"})
        await core.db.update("records", 1, {"value": "NewName"})
        await core.db.delete("records", 1)
        await core.db.kv_set("settings", "theme", "dark")
        val = await core.db.kv_get("settings", "theme")
        await core.db.log_event("UI", "window_open", {"module": "glass_panel"})
    """

    _MODEL_MAP: Dict[str, Type[Base]] = {
        "records":   GenericRecord,
        "kv_store":  KVStore,
        "event_log": EventLog,
    }

    # ── init ──────────────────────────────────────────────────────────────────

    async def init(self) -> None:
        """Инициализирует движок и создаёт таблицы."""
        global _engine, _session_factory, _closed
        _closed = False
        logger.info(f"[DB] Connecting: {DATABASE_URL}")
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            future=True,
        )
        _session_factory = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _ready.set()
        logger.info("[DB] Ready.")

    async def wait_ready(self) -> None:
        """Ожидает готовности БД."""
        await _ready.wait()

    # ── Сессия ───────────────────────────────────────────────────────────────

    def _session(self) -> AsyncSession:
        if _session_factory is None:
            raise RuntimeError("DB not initialised. Call await core.db.init() first.")
        return _session_factory()

    def _get_model(self, table: str) -> Type[Base]:
        model = self._MODEL_MAP.get(table)
        if model is None:
            raise ValueError(
                f"Unknown table '{table}'. Available: {list(self._MODEL_MAP.keys())}"
            )
        return model

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def add(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Добавить запись в таблицу. Возвращает созданный объект."""
        model = self._get_model(table)
        async with self._session() as session:
            obj = model(**data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            logger.debug(f"[DB] add → {table} id={obj.id}")
            return obj.to_dict()

    async def get(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Получить запись по id."""
        model = self._get_model(table)
        async with self._session() as session:
            obj = await session.get(model, record_id)
            return obj.to_dict() if obj else None

    async def get_all(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Получить все записи с опциональными фильтрами (равенство)."""
        model = self._get_model(table)
        async with self._session() as session:
            stmt = select(model)
            if filters:
                for col, val in filters.items():
                    stmt = stmt.where(getattr(model, col) == val)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [r.to_dict() for r in rows]

    async def update(
        self, table: str, record_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Обновить запись по id. Возвращает обновлённый объект."""
        model = self._get_model(table)
        async with self._session() as session:
            obj = await session.get(model, record_id)
            if obj is None:
                return None
            data["updated_at"] = datetime.now(timezone.utc)
            for k, v in data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            await session.commit()
            await session.refresh(obj)
            logger.debug(f"[DB] update → {table} id={record_id}")
            return obj.to_dict()

    async def delete(self, table: str, record_id: int) -> bool:
        """Удалить запись по id. Возвращает True если удалена."""
        model = self._get_model(table)
        async with self._session() as session:
            obj = await session.get(model, record_id)
            if obj is None:
                return False
            await session.delete(obj)
            await session.commit()
            logger.debug(f"[DB] delete → {table} id={record_id}")
            return True

    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Подсчитать количество записей."""
        rows = await self.get_all(table, filters, limit=10_000)
        return len(rows)

    # ── Key-Value хранилище ───────────────────────────────────────────────────

    async def kv_set(self, namespace: str, key: str, value: Any) -> Dict[str, Any]:
        """Установить значение в KV-хранилище (upsert)."""
        async with self._session() as session:
            stmt = select(KVStore).where(
                KVStore.namespace == namespace,
                KVStore.key == key
            )
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj:
                obj.value = value
                obj.updated_at = datetime.now(timezone.utc)
            else:
                obj = KVStore(namespace=namespace, key=key, value=value)
                session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj.to_dict()

    async def kv_get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Получить значение из KV-хранилища."""
        async with self._session() as session:
            stmt = select(KVStore).where(
                KVStore.namespace == namespace,
                KVStore.key == key
            )
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            return obj.value if obj else default

    async def kv_delete(self, namespace: str, key: str) -> bool:
        """Удалить ключ из KV-хранилища."""
        async with self._session() as session:
            stmt = select(KVStore).where(
                KVStore.namespace == namespace,
                KVStore.key == key
            )
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj:
                await session.delete(obj)
                await session.commit()
                return True
            return False

    async def kv_all(self, namespace: str) -> Dict[str, Any]:
        """Получить все ключи пространства имён."""
        async with self._session() as session:
            stmt = select(KVStore).where(KVStore.namespace == namespace)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return {r.key: r.value for r in rows}

    # ── Журнал событий ────────────────────────────────────────────────────────

    async def log_event(
        self,
        source: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Записать событие в журнал."""
        return await self.add("event_log", {
            "source": source,
            "event_type": event_type,
            "payload": payload or {},
        })

    async def get_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Получить события с фильтрацией."""
        filters: Dict[str, Any] = {}
        if event_type:
            filters["event_type"] = event_type
        if source:
            filters["source"] = source
        return await self.get_all("event_log", filters, limit=limit)

    # ── Сырой SQL ─────────────────────────────────────────────────────────────

    async def execute(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute raw SQL and return rows or command metadata."""
        async with self._session() as session:
            result = await session.execute(text(sql), params or {})
            if result.returns_rows:
                keys = list(result.keys())
                rows = result.fetchall()
                return {
                    "mode": "rows",
                    "rows": [dict(zip(keys, row)) for row in rows],
                    "rowcount": len(rows),
                }

            await session.commit()
            return {
                "mode": "command",
                "rows": [],
                "rowcount": result.rowcount if result.rowcount is not None else 0,
            }

    async def list_known_tables(self) -> List[str]:
        return sorted(self._MODEL_MAP.keys())

    async def get_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {"ready": self.is_ready, "tables": {}}
        for table in await self.list_known_tables():
            summary["tables"][table] = await self.count(table)
        return summary

    # ── Закрытие ──────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Корректно закрывает соединение с базой данных."""
        global _closed
        if _engine and not _closed:
            _closed = True
            _ready.clear()
            await _engine.dispose()
            logger.info("[DB] Connection closed.")

    @property
    def is_ready(self) -> bool:
        return _ready.is_set() and not _closed

    @property
    def is_closed(self) -> bool:
        return _closed

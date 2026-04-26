"""
CORE.py — Ядро системы. Документация: docs/CORE.md
"""

import asyncio
import logging
import threading
from concurrent.futures import Future
from typing import Any, Coroutine, Optional

from components.db import DatabaseManager

logger = logging.getLogger("core")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# ─── Core ────────────────────────────────────────────────────────────────────

class Core:
    def __init__(self) -> None:
        self.db = DatabaseManager()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ── Запуск / Остановка ───────────────────────────────────────────────────

    def start(self) -> None:
        """Запускает фоновый поток с event loop и инициализирует БД."""
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="CoreEventLoop",
        )
        self._thread.start()
        logger.info("[Core] Background loop started.")

        # Инициализируем БД (блокирует текущий поток до готовности)
        self.run_sync(self.db.init())
        logger.info("[Core] DB initialised.")

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self, timeout: float = 5.0) -> None:
        """
        Корректно останавливает ядро:
        1. Закрывает БД
        2. Останавливает event loop
        3. Ждёт завершения потока
        """
        logger.info("[Core] Stopping...")
        if self._loop and self._loop.is_running():
            # Корректно закрываем БД перед выходом
            future = asyncio.run_coroutine_threadsafe(self.db.close(), self._loop)
            try:
                future.result(timeout=timeout)
            except Exception as e:
                logger.warning(f"[Core] DB close warning: {e}")

            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("[Core] Stopped.")

    # ── Хелперы для вызова async из sync-кода ───────────────────────────────

    def submit(self, coro: Coroutine) -> Future:
        """
        Отправляет корутину в фоновый loop.
        Возвращает concurrent.futures.Future.

        Пример:
            f = core.submit(core.db.add("records", {...}))
            result = f.result(timeout=5)
        """
        if self._loop is None:
            raise RuntimeError("Core not started. Call core.start() first.")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def run_sync(self, coro: Coroutine, timeout: float = 30.0) -> Any:
        """
        Запускает корутину и блокирует текущий поток до результата.
        Удобно для инициализации из main-потока.

        Пример:
            result = core.run_sync(core.db.kv_get("app", "theme"))
        """
        future = self.submit(coro)
        return future.result(timeout=timeout)

    @property
    def is_ready(self) -> bool:
        return self.db.is_ready


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

core = Core()
"""
Application core.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from concurrent.futures import Future
from typing import Any, Callable, Coroutine, Optional

from components.db import DatabaseManager
from components.module_system import ModuleManager


logger = logging.getLogger("core")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


class Core:
    def __init__(self) -> None:
        self.db = DatabaseManager()
        self.modules = ModuleManager(self)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._api_handlers: dict[str, Callable[..., Any]] = {}

    def start(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="CoreEventLoop",
        )
        self._thread.start()
        logger.info("[Core] Background loop started.")
        self.run_sync(self.db.init())
        self.modules.discover()
        logger.info("[Core] Ready.")

    def _run_loop(self) -> None:
        if self._loop is None:
            return
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self, timeout: float = 5.0) -> None:
        logger.info("[Core] Stopping...")
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.db.close(), self._loop)
            try:
                future.result(timeout=timeout)
            except Exception as exc:
                logger.warning("[Core] DB close warning: %s", exc)
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("[Core] Stopped.")

    def submit(self, coro: Coroutine) -> Future:
        if self._loop is None:
            raise RuntimeError("Core is not started.")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def run_sync(self, coro: Coroutine, timeout: float = 30.0) -> Any:
        future = self.submit(coro)
        return future.result(timeout=timeout)

    def register_api(self, route: str, handler: Callable[..., Any]) -> None:
        self._api_handlers[route] = handler

    def unregister_api(self, route: str) -> None:
        self._api_handlers.pop(route, None)

    def list_api(self) -> list[str]:
        return sorted(self._api_handlers)

    def call_api(self, route: str, **params) -> Any:
        handler = self._api_handlers.get(route)
        if handler is None:
            raise KeyError(f"Unknown API route: {route}")
        return handler(**params)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.run_sync(self.db.kv_get("app_settings", key, default=default))

    def set_setting(self, key: str, value: Any) -> Any:
        return self.run_sync(self.db.kv_set("app_settings", key, value))

    @property
    def is_ready(self) -> bool:
        return self.db.is_ready


core = Core()

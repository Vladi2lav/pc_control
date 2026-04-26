# CORE.py — Ядро системы

Запускает и управляет всеми подсистемами.
Предоставляет глобальный доступ через паттерн singleton.

---

## Использование

```python
from components.CORE import core

# Запуск (автоматически делает GlassWindow)
core.start()

# Асинхронный запрос через фоновый event loop
future = core.submit(core.db.add("records", {...}))
result = future.result(timeout=5)

# Синхронный вызов (блокирует текущий поток)
value = core.run_sync(core.db.kv_get("app", "theme"))

# Остановка
core.stop()
```

---

## Архитектура

```
Core (singleton)
│
├── db: DatabaseManager     — async CRUD, kv-store, event log
├── _loop: asyncio.EventLoop — фоновый поток CoreEventLoop
└── _thread: Thread          — поток с event loop
```

Asyncio loop запускается в **отдельном фоновом потоке**, чтобы
async-операции с БД не блокировали UI-поток Qt.

---

## API

| Метод | Описание |
|-------|----------|
| `core.start()` | Запустить фоновый поток + инициализировать БД |
| `core.stop()` | Закрыть БД, остановить loop, дождаться потока |
| `core.submit(coro)` | Отправить корутину в loop → `concurrent.futures.Future` |
| `core.run_sync(coro)` | Запустить корутину и заблокироваться до результата |
| `core.is_ready` | Проверить, готова ли БД |

---

## DatabaseManager (core.db)

Полный API см. в `docs/db.md`.

Краткий список:
```python
await core.db.add("records", {"key": "x", "value": {...}})
await core.db.get_all("records", limit=100)
await core.db.get_by_id("records", record_id)
await core.db.delete("records", record_id)
await core.db.kv_set("namespace", "key", value)
await core.db.kv_get("namespace", "key", default=None)
await core.db.kv_delete("namespace", "key")
await core.db.log_event("source", "event_type", payload={})
await core.db.execute("SELECT * FROM records")
await core.db.count("records")
```

---

## Жизненный цикл

```
GlassWindow.__init__()
    └── core.start()
            ├── Создаёт asyncio.new_event_loop()
            ├── Запускает Thread("CoreEventLoop")
            └── run_sync(db.init())   ← инициализирует БД синхронно

GlassWindow._request_close()
    └── core.stop()
            ├── run_coroutine_threadsafe(db.close())
            └── loop.stop() + thread.join()
```

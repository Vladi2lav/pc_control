"""
modules/db_explorer/__init__.py

Публичный экспорт модуля.

Использование в UI.py:
    from modules.db_explorer import DBExplorerModule
    self._mount(DBExplorerModule)
"""

from modules.db_explorer.explorer import DBExplorerModule

__all__ = ["DBExplorerModule"]

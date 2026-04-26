CONTROL MVP

Run:
python init.py

Architecture:
- components/CORE.py            background core, DB access, app API registry
- components/db.py              async database layer
- components/module_system.py   module manifests, config import/export
- components/theme.py           dark glass and white glass themes
- components/UI.py              desktop shell window with snap-to-edge behavior
- modules/module_studio         built-in configurator module
- modules/db_explorer           SQL module for DB checks and SQL queries

Current app API:
- app.set_theme(theme)
- app.get_theme()
- modules.list()
- modules.call(module_id, action, params)

Module API examples:
- sql_console.health()
- sql_console.run_sql(sql)
- sql_console.summary()
- module_studio.list_modules()
- module_studio.get_config(module_id)
- module_studio.save_config(module_id, config)

Config storage:
- namespace app_settings
- namespace module_config

Export/import format:
- JSON file with manifest + config

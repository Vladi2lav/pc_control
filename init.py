"""
Application entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.CORE import core
from components.configurator import ConfiguratorWindow
from components.runtime_forms import ModuleRuntimeWorkspace
from components.UI import GlassWindow
from components.theme import apply_theme
from PySide6.QtWidgets import QMainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    core.start()
    theme = core.get_setting("theme", "dark")
    apply_theme(app, theme)

    window = GlassWindow("Control")
    configurator = ConfiguratorWindow(core, parent=window)
    runtime_windows: dict[str, QMainWindow] = {}
    has_stopped = {"value": False}

    def stop_core_once() -> None:
        if has_stopped["value"]:
            return
        has_stopped["value"] = True
        core.stop()

    def set_theme(theme: str) -> dict:
        apply_theme(app, theme)
        core.set_setting("theme", theme)
        return {"ok": True, "theme": theme}

    core.register_api("app.set_theme", set_theme)
    core.register_api("app.get_theme", lambda: core.get_setting("theme", "dark"))
    core.register_api("app.open_configurator", lambda context="app": configurator.open_context(context))
    def open_module_runtime(module_id: str):
        config = core.modules.get_module_config(module_id)
        host = runtime_windows.get(module_id)
        if host is None:
            host = QMainWindow(window)
            host.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
            host.resize(1280, 860)
            runtime_windows[module_id] = host
        runtime = ModuleRuntimeWorkspace(module_id, config, parent=host)
        host.setCentralWidget(runtime)
        host.setWindowTitle(f"Runtime: {module_id}")
        host.show()
        host.raise_()
        host.activateWindow()
        return {"ok": True, "module_id": module_id}
    core.register_api("app.open_module_runtime", open_module_runtime)
    def create_module(module_id: str, name: str):
        manifest = core.modules.create_module(module_id=module_id, name=name)
        module_class = core.modules.load_module_class(manifest.module_id)
        window._mount(module_class, icon=manifest.icon, name=manifest.name)
        return manifest.to_dict()
    core.register_api("app.create_module", create_module)
    core.register_api(
        "modules.list",
        lambda: [manifest.to_dict() for manifest in core.modules.list_manifests()],
    )
    core.register_api(
        "modules.call",
        lambda module_id, action, params=None: core.call_api(
            f"{module_id}.{action}", **(params or {})
        ),
    )

    for manifest in core.modules.list_manifests():
        module_class = core.modules.load_module_class(manifest.module_id)
        window._mount(module_class, icon=manifest.icon, name=manifest.name)

    window.show()
    app.aboutToQuit.connect(stop_core_once)
    code = app.exec()
    stop_core_once()
    return code


if __name__ == "__main__":
    raise SystemExit(main())

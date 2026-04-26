"""
Application entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.CORE import core
from components.UI import GlassWindow
from components.theme import apply_theme


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    core.start()
    theme = core.get_setting("theme", "dark")
    apply_theme(app, theme)

    window = GlassWindow("Control")

    def set_theme(theme: str) -> dict:
        apply_theme(app, theme)
        core.set_setting("theme", theme)
        return {"ok": True, "theme": theme}

    core.register_api("app.set_theme", set_theme)
    core.register_api("app.get_theme", lambda: core.get_setting("theme", "dark"))
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
    code = app.exec()
    core.stop()
    return code


if __name__ == "__main__":
    raise SystemExit(main())

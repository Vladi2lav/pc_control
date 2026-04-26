"""
Module system for Control.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject


MODULES_DIR = Path(__file__).resolve().parent.parent / "modules"


@dataclass(slots=True)
class ModuleManifest:
    module_id: str
    package: str
    class_name: str
    name: str
    icon: str = "[]"
    version: str = "0.1.0"
    description: str = ""
    entry_file: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], package: str) -> "ModuleManifest":
        return cls(
            module_id=data["module_id"],
            package=package,
            class_name=data["class_name"],
            name=data.get("name", package),
            icon=data.get("icon", "[]"),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            entry_file=data.get("entry_file", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseModule(QObject):
    """
    Common base class for app modules.
    """

    manifest: ModuleManifest | None = None

    def __init__(self, core, parent=None, **kwargs):
        super().__init__(parent)
        self.core = core
        self.widget = None
        self._registered_api: list[str] = []

    def register_local_api(self, handlers: dict[str, Callable[..., Any]]) -> None:
        if self.manifest is None:
            return
        for action, handler in handlers.items():
            route = f"{self.manifest.module_id}.{action}"
            self.core.register_api(route, handler)
            self._registered_api.append(route)

    def unregister_local_api(self) -> None:
        for route in self._registered_api:
            self.core.unregister_api(route)
        self._registered_api.clear()

    def module_id(self) -> str:
        return self.manifest.module_id if self.manifest else ""

    def open_configurator(self) -> None:
        module_id = self.module_id()
        if module_id:
            self.core.call_api("app.open_configurator", context=module_id)

    def safe_close(self) -> None:
        self.unregister_local_api()


class ModuleManager:
    def __init__(self, core) -> None:
        self.core = core
        self._manifests: dict[str, ModuleManifest] = {}

    def discover(self) -> list[ModuleManifest]:
        manifests: dict[str, ModuleManifest] = {}
        if not MODULES_DIR.exists():
            self._manifests = manifests
            return []

        for manifest_path in MODULES_DIR.glob("*/manifest.json"):
            package = manifest_path.parent.name
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = ModuleManifest.from_dict(data, package=package)
            manifests[manifest.module_id] = manifest

        self._manifests = dict(sorted(manifests.items(), key=lambda item: item[1].name.lower()))
        return list(self._manifests.values())

    def list_manifests(self) -> list[ModuleManifest]:
        return list(self._manifests.values())

    def get_manifest(self, module_id: str) -> ModuleManifest:
        return self._manifests[module_id]

    def load_module_class(self, module_id: str):
        manifest = self.get_manifest(module_id)
        module = importlib.import_module(f"modules.{manifest.package}")
        cls = getattr(module, manifest.class_name)
        cls.manifest = manifest
        return cls

    def load_module_source(self, module_id: str) -> str:
        manifest = self.get_manifest(module_id)
        if manifest.entry_file:
            path = MODULES_DIR / manifest.package / manifest.entry_file
        else:
            path = MODULES_DIR / manifest.package / "__init__.py"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def get_module_config(self, module_id: str) -> dict[str, Any]:
        config = self.core.run_sync(
            self.core.db.kv_get("module_config", module_id, default={})
        ) or {}
        if not config:
            config = self.build_default_config(module_id)
        return config

    def save_module_config(self, module_id: str, config: dict[str, Any]) -> dict[str, Any]:
        return self.core.run_sync(self.core.db.kv_set("module_config", module_id, config))

    def export_module(self, module_id: str, target_path: str) -> Path:
        payload = {
            "manifest": self.get_manifest(module_id).to_dict(),
            "config": self.get_module_config(module_id),
        }
        path = Path(target_path)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def import_module_config(self, source_path: str) -> dict[str, Any]:
        path = Path(source_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest = payload.get("manifest", {})
        module_id = manifest.get("module_id")
        if not module_id:
            raise ValueError("Missing module_id in imported manifest.")
        if module_id not in self._manifests:
            raise ValueError(f"Module '{module_id}' is not installed.")
        config = payload.get("config", {})
        self.save_module_config(module_id, config)
        return config

    def build_default_config(self, module_id: str) -> dict[str, Any]:
        manifest = self.get_manifest(module_id)
        title = manifest.name
        return {
            "module_id": module_id,
            "title": title,
            "forms": [
                {
                    "id": "main_form",
                    "name": "MainForm",
                    "title": title,
                    "width": 960,
                    "height": 620,
                    "pages": [
                        {
                            "id": "main_page",
                            "name": "MainPage",
                            "title": "Main Page",
                            "controls": [
                                {
                                    "id": "header_label",
                                    "type": "label",
                                    "text": title,
                                    "x": 32,
                                    "y": 24,
                                    "w": 280,
                                    "h": 36,
                                    "requisite": "",
                                    "command": "",
                                    "target_form": "",
                                    "target_page": "",
                                },
                                {
                                    "id": "open_button",
                                    "type": "button",
                                    "text": "Open",
                                    "x": 32,
                                    "y": 88,
                                    "w": 140,
                                    "h": 34,
                                    "requisite": "",
                                    "command": "Open",
                                    "target_form": "",
                                    "target_page": "",
                                },
                            ],
                        }
                    ],
                }
            ],
            "styles": {
                "theme": self.core.get_setting("theme", "dark"),
                "accent": "#7EB8F7",
                "density": "comfortable",
            },
            "requisites": [
                {"name": "Title", "type": "String", "default": title},
                {"name": "Visible", "type": "Boolean", "default": True},
            ],
            "commands": [
                {"name": "Open", "handler": "open", "target_form": "", "target_page": "", "parameter": ""},
                {"name": "Refresh", "handler": "refresh", "target_form": "", "target_page": "", "parameter": ""},
            ],
            "code": (
                "def open(context):\n"
                "    pass\n\n"
                "def refresh(context):\n"
                "    pass\n"
            ),
        }

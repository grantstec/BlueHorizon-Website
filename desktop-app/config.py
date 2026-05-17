"""Tiny persistent settings store.

Stored as JSON in the user's home dir so it survives between sessions and
doesn't require any DB / extra dependency.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field


CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".bluehorizon-desktop.json")


@dataclass
class Settings:
    repo_path: str = ""
    auto_pull_seconds: int = 30
    auto_pull_enabled: bool = True
    notify_on_pull: bool = True

    @classmethod
    def load(cls) -> "Settings":
        if not os.path.exists(CONFIG_FILE):
            return cls()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: data.get(k, getattr(cls(), k)) for k in cls().__dict__})
        except Exception:
            return cls()

    def save(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception:
            # Persistence is best-effort; not worth crashing the app
            pass

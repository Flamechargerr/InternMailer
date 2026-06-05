"""Atlas dashboard synchronization helpers for paused review jobs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class AtlasSyncClient:
    """Best-effort Atlas tab sync; failures are non-blocking."""

    def __init__(
        self,
        enabled: bool = True,
        label_prefix: str = "apply-review",
        index_path: str = "output/atlas/review_index.json",
        atlas_cli: Optional[str] = None,
        timeout_s: int = 12,
    ):
        self.enabled = enabled
        self.label_prefix = label_prefix
        self.index_path = Path(index_path)
        self.timeout_s = timeout_s
        codex_home = os.getenv("CODEX_HOME", os.path.join(str(Path.home()), ".codex"))
        self.atlas_cli = atlas_cli or os.path.join(codex_home, "skills", "atlas", "scripts", "atlas_cli.py")
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_index(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(self._index, indent=2), encoding="utf-8")

    def _run(self, *args: str, json_output: bool = False) -> Optional[Any]:
        if not self.enabled:
            return None

        cmd = ["uv", "run", "--python", "3.12", "python", self.atlas_cli, *args]
        if json_output:
            cmd.append("--json")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=True,
            )
            out = result.stdout.strip()
            if json_output and out:
                return json.loads(out)
            return out
        except Exception:
            self.enabled = False
            return None

    def sync_paused_job(self, worker_id: int, job_key: str, url: str, provider: str) -> None:
        if not self.enabled or not url:
            return

        _ = self._run("open-tab", url)
        tabs = self._run("tabs", json_output=True)
        if isinstance(tabs, list):
            for tab in reversed(tabs):
                if (tab.get("url") or "") == url:
                    self._index[job_key] = {
                        "label": f"{self.label_prefix}-w{worker_id}-{provider}",
                        "url": url,
                        "worker_id": worker_id,
                        "provider": provider,
                        "window_id": tab.get("window_id"),
                        "tab_index": tab.get("tab_index"),
                        "state": "paused_review",
                    }
                    self._save_index()
                    return

    def sync_completed_job(self, job_key: str, state: str) -> None:
        if job_key not in self._index:
            return

        info = self._index[job_key]
        info["state"] = state
        window_id = info.get("window_id")
        tab_index = info.get("tab_index")
        if self.enabled and window_id is not None and tab_index is not None:
            _ = self._run("close-tab", str(window_id), str(tab_index))

        self._save_index()

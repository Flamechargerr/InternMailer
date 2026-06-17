"""Root conftest — bootstrap TCC workarounds before any test imports."""
import sys
from pathlib import Path

import pytest

_root = str(Path(__file__).resolve().parent.parent.parent)
_src = str(Path(__file__).resolve().parent.parent.parent / "src")
for p in [_src, _root]:
    if p not in sys.path:
        sys.path.insert(0, p)

from utils.bootstrap import bootstrap  # noqa: E402
bootstrap()


def pytest_ignore_collect(collection_path, config):
    """Silently skip paths that macOS TCC blocks (e.g. .DS_Store)."""
    try:
        collection_path.stat()
    except (PermissionError, OSError):
        return True
    return None

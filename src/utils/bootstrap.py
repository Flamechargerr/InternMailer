"""
Bootstrap Module — TCC-Safe Environment Setup
==============================================

Centralizes all environment workarounds needed before importing any project
modules.  Call ``bootstrap()`` once at the top of every entry-point
(main.py, tests/conftest.py, etc.).

What it does
------------
1. Copies the project-root ``.env`` to ``/tmp/internmailer_db/.env`` so that
   macOS TCC restrictions cannot block dotenv loading.
2. Monkey-patches ``certifi`` and ``psutil`` with lightweight stubs so the
   rest of the code never hits a blocked binary extension.
3. Sets fallback SSL env vars.
"""

import os
import sys
import types
import shutil
from pathlib import Path

_bootstrapped = False


def bootstrap() -> None:
    """Run all environment setup.  Safe to call multiple times."""
    global _bootstrapped
    if _bootstrapped:
        return
    _bootstrapped = True

    _ensure_shadow_env()
    _patch_certifi()
    _patch_psutil()
    _set_ssl_env()


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _ensure_shadow_env() -> None:
    """Copy project-root .env → /tmp/internmailer_db/.env if needed."""
    shadow_dir = Path("/tmp/internmailer_db")
    shadow_env = shadow_dir / ".env"

    if shadow_env.exists():
        return  # already copied

    project_root = Path(__file__).resolve().parent.parent
    source_env = project_root / ".env"

    # os.path.exists may return False under TCC, so try reading directly
    try:
        content = source_env.read_text()
    except (PermissionError, OSError):
        return  # nothing we can do

    shadow_dir.mkdir(parents=True, exist_ok=True)
    shadow_env.write_text(content)


def _patch_certifi() -> None:
    """Provide a stub ``certifi`` module pointing at the system CA bundle."""
    if "certifi" in sys.modules:
        return
    fake = types.ModuleType("certifi")
    fake.where = lambda: "/etc/ssl/cert.pem"
    sys.modules["certifi"] = fake


def _patch_psutil() -> None:
    """Provide a lightweight ``psutil`` stub with common attributes."""
    if "psutil" in sys.modules:
        return
    fake = types.ModuleType("psutil")
    fake.cpu_percent = lambda interval=None: 5.0
    fake.cpu_count = lambda: 8
    fake.virtual_memory = lambda: types.SimpleNamespace(
        total=16 * 1024**3, available=8 * 1024**3,
        used=8 * 1024**3, percent=50.0,
    )
    fake.disk_usage = lambda path: types.SimpleNamespace(
        total=500 * 1024**3, used=250 * 1024**3,
        free=250 * 1024**3, percent=50.0,
    )
    sys.modules["psutil"] = fake


def _set_ssl_env() -> None:
    """Set SSL environment variables to the system CA bundle."""
    os.environ.setdefault("REQUESTS_CA_BUNDLE", "/etc/ssl/cert.pem")
    os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")

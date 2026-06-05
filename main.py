#!/usr/bin/env python3
"""
🚀 InternMailer - Main Entry Point
==================================
Single launcher for the Flask dashboard and CLI utilities.

Usage:
    python main.py
    python main.py --cli
    python main.py --validate
    python main.py --production-check
"""

from __future__ import annotations

import argparse
import atexit
import logging
import os
import signal
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Centralised TCC workarounds (psutil/certifi stubs, .env shadow-copy, SSL)
from utils.bootstrap import bootstrap

bootstrap()

from utils.config import config

logger = logging.getLogger(__name__)


class Launcher:
    """Single runtime entrypoint for InternMailer."""

    def __init__(self) -> None:
        self.shutdown_requested = False
        self._install_signal_handlers()
        atexit.register(self._cleanup)

    def _install_signal_handlers(self) -> None:
        """Handle termination signals so production shutdown is graceful."""
        for signame in ("SIGINT", "SIGTERM"):
            if hasattr(signal, signame):
                signal.signal(getattr(signal, signame), self._handle_shutdown_signal)

    def _handle_shutdown_signal(self, signum, frame) -> None:  # noqa: D401, ANN001
        signal_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.info("Received %s, shutting down...", signal_name)
        self.shutdown_requested = True

    def _cleanup(self) -> None:
        """Final cleanup hook for any future managed components."""
        if self.shutdown_requested:
            logger.info("Cleanup complete")

    def _setup_validation(self, strict: bool = False) -> bool:
        """Run setup validation and print a useful report."""
        from utils.validate_setup import SetupValidator

        validator = SetupValidator()
        result = validator.validate_all()

        if result["valid"]:
            print("✅ Setup validation passed.")
            return True

        header = "❌ Setup validation failed." if strict else "⚠️  Setup validation found issues."
        print(header)
        for message in result["errors"]:
            print(f"   {message}")
        for message in result["warnings"]:
            print(f"   {message}")

        return not strict

    def _production_check(self) -> bool:
        """Run the production readiness report."""
        from utils.production_check import ProductionChecker

        checker = ProductionChecker()
        production_ready = checker.print_report()

        # Also enforce setup validation so a production check can gate deployment.
        setup_ok = self._setup_validation(strict=True)
        return production_ready and setup_ok

    def _run_cli(self) -> int:
        """Launch the legacy CLI menu."""
        print("🖥️  Starting CLI menu...")
        from utils.run import main as cli_main

        cli_main()
        return 0

    def _run_gunicorn(self, app) -> int:
        """Run the Flask app under Gunicorn when available."""
        try:
            from gunicorn.app.base import BaseApplication
        except ImportError:
            print("⚠️ Gunicorn not installed. Falling back to Flask development server.")
            self._run_flask_server(app)
            return 0

        class StandaloneApplication(BaseApplication):
            def __init__(self, flask_app, options=None):
                self.options = options or {}
                self.application = flask_app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            "bind": f"{config.FLASK_HOST}:{config.FLASK_PORT}",
            "workers": 4,
            "worker_class": "sync",
            "timeout": 120,
            "keepalive": 5,
            "max_requests": 1000,
            "max_requests_jitter": 50,
            "preload_app": True,
            "loglevel": config.LOG_LEVEL.lower(),
            "accesslog": str(config.LOGS_DIR / "access.log"),
            "errorlog": str(config.LOGS_DIR / "error.log"),
        }

        print(f"🚀 Starting Gunicorn on {config.FLASK_HOST}:{config.FLASK_PORT}")
        StandaloneApplication(app, options).run()
        return 0

    def _run_flask_server(self, app) -> int:
        """Run the Flask development server as the final fallback."""
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.DEBUG,
            use_reloader=config.DEBUG,
        )
        return 0

    def run_web(self) -> int:
        """Start the web dashboard with production-aware behavior."""
        from web.web_dashboard import app

        display_host = "localhost" if config.FLASK_HOST in {"0.0.0.0", "::"} else config.FLASK_HOST
        print("🌐 Starting web dashboard...")
        print(f"Open http://{display_host}:{config.FLASK_PORT} in your browser\n")

        # Development keeps going with warnings. Production exits on missing setup.
        strict = config.is_production()
        setup_ok = self._setup_validation(strict=strict)
        if not setup_ok:
            return 1

        if config.is_production():
            return self._run_gunicorn(app)

        return self._run_flask_server(app)

    def run(self, args: argparse.Namespace) -> int:
        """Dispatch to the requested runtime mode."""
        if args.validate:
            return 0 if self._setup_validation(strict=True) else 1

        if args.production_check:
            return 0 if self._production_check() else 1

        if args.cli:
            return self._run_cli()

        return self.run_web()


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="InternMailer - Single production launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py
    python main.py --cli
    python main.py --validate
    python main.py --production-check
        """,
    )

    parser.add_argument(
        "--cli",
        "-c",
        action="store_true",
        help="Launch the CLI menu instead of the web dashboard",
    )
    parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Validate configuration and data sources, then exit",
    )
    parser.add_argument(
        "--production-check",
        "--prod-check",
        action="store_true",
        help="Run the production readiness check and exit",
    )
    parser.add_argument(
        "--web",
        "-w",
        action="store_true",
        help="Launch the web dashboard explicitly",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    launcher = Launcher()
    return launcher.run(args)


if __name__ == "__main__":
    sys.exit(main())

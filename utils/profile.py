"""
Profile Management - User profile data for personalization
Loads profile details from a JSON/YAML file and environment variables.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except Exception:  # pragma: no cover - yaml is optional at runtime
    yaml = None


DEFAULT_PROFILE: Dict[str, Any] = {
    "name": "Your Name",
    "title": "Your Title",
    "email": "your.email@example.com",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "calendar_link": "",
    "signature_lines": [],
    "resume_paths": ["resumes/resume.pdf", "resume.pdf"],
    "skills": [
        "Python",
        "SQL",
        "Data Analysis",
        "APIs",
        "Automation",
    ],
    "experience_highlights": [
        "In my previous role, I built and automated data workflows to improve reliability and speed.",
        "I have experience collaborating across teams to deliver production-ready systems.",
    ],
    "project_highlights": [
        "Delivered end-to-end project work including design, implementation, and testing.",
    ],
    "ats": {
        "summary": "",
        "coursework": [],
        "education": [],
        "experience": [],
        "projects": [],
        "skills": {},
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_profile_file(path: Path) -> Dict[str, Any]:
    """Load profile from JSON/YAML file."""
    if not path.exists():
        return {}

    if path.suffix.lower() in [".yaml", ".yml"]:
        if not yaml:
            raise RuntimeError("PyYAML is required to read YAML profile files.")
        return yaml.safe_load(path.read_text()) or {}

    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())

    raise ValueError(f"Unsupported profile file type: {path.suffix}")


def _resolve_profile_path(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Resolve profile path from env or defaults."""
    if explicit_path:
        return Path(explicit_path)

    env_path = os.getenv("PROFILE_PATH", "").strip()
    if env_path:
        return Path(env_path)

    candidates = [
        Path("data/profile.yaml"),
        Path("data/profile.yml"),
        Path("data/profile.json"),
        Path("profile.yaml"),
        Path("profile.yml"),
        Path("profile.json"),
    ]
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except (PermissionError, OSError):
            continue

    return None


class Profile:
    """Convenience wrapper for profile data."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def signature_lines(self) -> List[str]:
        lines = self.data.get("signature_lines") or []
        if lines:
            return lines

        lines = [self.data.get("name", "Your Name")]
        title = self.data.get("title")
        if title:
            lines.append(title)
        location = self.data.get("location")
        if location:
            lines.append(location)
        email = self.data.get("email")
        if email:
            lines.append(email)
        linkedin = self.data.get("linkedin")
        if linkedin:
            lines.append(linkedin)
        portfolio = self.data.get("portfolio")
        if portfolio:
            lines.append(portfolio)
        return [line for line in lines if line]

    def signature_text(self) -> str:
        return "\n".join(self.signature_lines())

    def signature_html(self) -> str:
        return "<br>".join(self.signature_lines())

    def resume_paths(self) -> List[str]:
        return self.data.get("resume_paths") or []


_PROFILE_CACHE: Optional[Profile] = None


def get_profile(profile_path: Optional[str] = None, force_reload: bool = False) -> Profile:
    """Load and cache the user profile."""
    global _PROFILE_CACHE

    if _PROFILE_CACHE and not force_reload:
        return _PROFILE_CACHE

    profile_data: Dict[str, Any] = dict(DEFAULT_PROFILE)

    resolved_path = _resolve_profile_path(profile_path)
    if resolved_path:
        profile_data = _deep_merge(profile_data, _load_profile_file(resolved_path))

    # Environment overrides
    profile_data["name"] = os.getenv("YOUR_NAME", profile_data.get("name", "Your Name"))
    profile_data["email"] = os.getenv(
        "YOUR_EMAIL",
        os.getenv("EMAIL_ADDRESS", os.getenv("GMAIL_USER", profile_data.get("email", ""))),
    )
    profile_data["phone"] = os.getenv("YOUR_PHONE", profile_data.get("phone", ""))
    profile_data["title"] = os.getenv("YOUR_TITLE", profile_data.get("title", ""))
    profile_data["location"] = os.getenv("YOUR_LOCATION", profile_data.get("location", ""))
    profile_data["linkedin"] = os.getenv("LINKEDIN_URL", profile_data.get("linkedin", ""))
    profile_data["github"] = os.getenv("GITHUB_URL", profile_data.get("github", ""))
    profile_data["portfolio"] = os.getenv("PORTFOLIO_URL", profile_data.get("portfolio", ""))
    profile_data["calendar_link"] = os.getenv("CALENDAR_LINK", profile_data.get("calendar_link", ""))

    # Resume paths override
    resume_paths_env = os.getenv("RESUME_PATHS", "").strip()
    if resume_paths_env:
        profile_data["resume_paths"] = [p.strip() for p in resume_paths_env.split(",") if p.strip()]

    _PROFILE_CACHE = Profile(profile_data)
    return _PROFILE_CACHE

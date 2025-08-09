import os
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

HR_TEMPLATE_PRIMARY = PROJECT_ROOT / 'templates' / 'enhanced_hr_template.html'
HR_TEMPLATE_FALLBACK = PROJECT_ROOT / 'production' / 'ultra_system' / 'templates' / 'enhanced_hr_template.html'

PROF_TEMPLATE_PRIMARY = PROJECT_ROOT / 'templates' / 'enhanced_academic_research_template.html'
PROF_TEMPLATE_FALLBACK = PROJECT_ROOT / 'production' / 'ultra_system' / 'templates' / 'enhanced_academic_research_template.html'

# Optional Jinja2 support for full template features
try:
    from jinja2 import Environment, BaseLoader, select_autoescape
    _HAS_JINJA = True
except Exception:
    Environment = None  # type: ignore
    BaseLoader = object  # type: ignore
    select_autoescape = lambda *args, **kwargs: None  # type: ignore
    _HAS_JINJA = False

def _read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def load_hr_template() -> str:
    for p in (HR_TEMPLATE_PRIMARY, HR_TEMPLATE_FALLBACK):
        if p.exists():
            try:
                return _read_text(p)
            except Exception:
                continue
    # Minimal fallback
    return (
        """
        <html><body>
        <p>Dear <strong>{{ name }}</strong>,</p>
        <p>I'm reaching out regarding internship opportunities at <strong>{{ company_name }}</strong> ({{ company_niche }}).</p>
        </body></html>
        """
    )


def load_professor_template() -> str:
    for p in (PROF_TEMPLATE_PRIMARY, PROF_TEMPLATE_FALLBACK):
        if p.exists():
            try:
                return _read_text(p)
            except Exception:
                continue
    # Minimal fallback
    return (
        """
        <html><body>
        <p>Dear <strong>{{ prof_name }}</strong>,</p>
        <p>I'm reaching out regarding your work in <em>{{ research_area }}</em> at <strong>{{ university }}</strong>.</p>
        </body></html>
        """
    )


def _flatten(prefix: str, data: Any, out: Dict[str, str]):
    if isinstance(data, dict):
        for k, v in data.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            _flatten(new_prefix, v, out)
    else:
        out[prefix] = '' if data is None else str(data)


def render(template_html: str, placeholders: Dict[str, Any]) -> str:
    """Render template with Jinja2 if available; otherwise do a simple key replace.

    - Jinja2 path supports loops, conditionals, filters, and dotted placeholders.
    - Fallback path only supports replacing {{ key }} and {{ a.b }} with strings.
    """
    if _HAS_JINJA:
        try:
            env = Environment(
                loader=BaseLoader(),
                autoescape=select_autoescape(['html', 'xml'])
            )
            tmpl = env.from_string(template_html)
            return tmpl.render(**placeholders)
        except Exception:
            # Fall back to simple replacement if Jinja rendering fails
            pass

    flat: Dict[str, str] = {}
    _flatten('', placeholders, flat)
    out = template_html
    for k, v in flat.items():
        out = out.replace(f'{{{{ {k} }}}}', v)
    return out

"""
InternMailer - LaTeX Builder

Safely substitutes rewritten bullet points into the locked LaTeX CV template
using %% BLOCK: %% comment tags.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional, Union

logger = logging.getLogger("internmailer.latex_builder")

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = PACKAGE_DIR / "base_cv.tex"

BLOCK_TYPES = {
    "experience_intellect": "\\item",
    "project_yaanbarpe": "\\item",
    "project_crimeconnect": "\\item",
    "project_medrag": "\\item",
    "project_florafight": "\\item",
    "project_hackops": "\\item",
    "summary": None,
    "coursework": None,
}


def load_template() -> str:
    """Load the base LaTeX template."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"LaTeX template not found: {TEMPLATE_PATH}")
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _escape_latex(text: str) -> str:
    """Escape LaTeX special characters in text."""
    replacements = {
        "&": "\\&",
        "%": "\\%",
        "#": "\\#",
        "_": "\\_",
    }
    result = text
    for char, escaped in replacements.items():
        result = re.sub(rf"(?<!\\){re.escape(char)}", escaped, result)
    return result


def replace_block(tex_content: str, block_name: str, new_content: Union[list[str], str]) -> str:
    """
    Replace content inside a %% BLOCK: %% region.

    Args:
        tex_content: Current .tex file contents
        block_name: Name of the block (e.g. "experience_intellect")
        new_content: Either a list of bullet strings or a single string
    """
    start_tag = f"%% BLOCK:{block_name}_start %%"
    end_tag = f"%% BLOCK:{block_name}_end %%"

    pattern = re.compile(
        rf"({re.escape(start_tag)})\s*\n(.*?)(\n\s*{re.escape(end_tag)})",
        re.DOTALL,
    )

    match = pattern.search(tex_content)
    if not match:
        logger.warning("Block '%s' not found in template", block_name)
        return tex_content

    if isinstance(new_content, list):
        block_type = BLOCK_TYPES.get(block_name, "\\item")
        if block_type == "\\item":
            replacement_text = "\n".join(f"\\item {_escape_latex(bullet)}" for bullet in new_content)
        else:
            replacement_text = "\n".join(str(item) for item in new_content)
    else:
        replacement_text = str(new_content)
        if block_name == "summary":
            replacement_text = _escape_latex(replacement_text)

    replacement = f"{match.group(1)}\n{replacement_text}\n{match.group(3).lstrip()}"
    new_tex = pattern.sub(lambda _m: replacement, tex_content, count=1)

    item_count = len(new_content) if isinstance(new_content, list) else 1
    logger.info("Replaced block '%s' with %s item(s)", block_name, item_count)
    return new_tex


def build_tailored_cv(rewrite_result: dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Build a complete tailored .tex file from rewrite output.

    Returns the path to the generated .tex file.
    """
    tex = load_template()

    bullets = rewrite_result.get("bullets", {})
    block_name_map = {
        "intellect": "experience_intellect",
        "yaanbarpe": "project_yaanbarpe",
        "crimeconnect": "project_crimeconnect",
        "medrag": "project_medrag",
        "florafight": "project_florafight",
        "hackops": "project_hackops",
    }

    for profile_key, block_name in block_name_map.items():
        if profile_key in bullets:
            tex = replace_block(tex, block_name, bullets[profile_key])

    summary = rewrite_result.get("summary", "")
    if summary:
        tex = replace_block(tex, "summary", summary)

    keywords = rewrite_result.get("keywords", {})
    tech_keywords = keywords.get("tech", [])
    if tech_keywords:
        course_keywords = [k for k in tech_keywords if len(str(k)) > 3][:6]
        if course_keywords:
            coursework_line = " \\(\\cdot\\) ".join(str(k) for k in course_keywords)
            tex = replace_block(tex, "coursework", coursework_line)

    if output_path is None:
        output_path = "/tmp/internmailer_tailored_cv.tex"

    output = Path(output_path)
    output.write_text(tex, encoding="utf-8")
    logger.info("Tailored .tex saved to %s", output_path)
    return str(output)


def verify_template_integrity(original_tex: str, modified_tex: str) -> bool:
    """
    Verify that only block regions were modified.
    """
    block_pattern = re.compile(r"%% BLOCK:\w+_start %%.*?%% BLOCK:\w+_end %%", re.DOTALL)
    original_stripped = block_pattern.sub("<<BLOCK>>", original_tex)
    modified_stripped = block_pattern.sub("<<BLOCK>>", modified_tex)
    if original_stripped == modified_stripped:
        logger.info("Template integrity verified - only block regions modified")
        return True

    logger.error("INTEGRITY VIOLATION: Non-block regions were modified!")
    return False


def list_blocks(tex_content: Optional[str] = None) -> list[str]:
    """List all block names found in the template."""
    if tex_content is None:
        tex_content = load_template()
    pattern = re.compile(r"%% BLOCK:(\w+)_start %%")
    return pattern.findall(tex_content)

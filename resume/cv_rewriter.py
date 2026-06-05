"""
InternMailer - AI CV Rewriter

Two-step AI pipeline:
  1. Extract ATS keywords from the job description
  2. Rewrite profile bullets to surface those keywords

Falls back to local keyword extraction if AI is unavailable.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from utils.config import config
from utils.profile import get_profile

logger = logging.getLogger("internmailer.cv_rewriter")


def _strip_code_fences(text: str) -> str:
    """Remove markdown fences and obvious label prefixes from model output."""
    clean = str(text or "").strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        if len(lines) > 2:
            clean = "\n".join(lines[1:-1]).strip()

    for prefix in ("Here's", "Here is", "Summary:", "Bullets:", "Output:"):
        if clean.lower().startswith(prefix.lower()):
            clean = clean[len(prefix):].lstrip(" :\n\t-")
    return clean


def _get_groq_client():
    if not config.GROQ_API_KEY:
        return None
    from groq import Groq

    return Groq(api_key=config.GROQ_API_KEY)


def _get_openai_client():
    if not config.OPENAI_API_KEY:
        return None
    from openai import OpenAI

    return OpenAI(api_key=config.OPENAI_API_KEY)


def _call_llm(messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 1000) -> str:
    """Call Groq first, fall back to OpenAI."""
    groq = _get_groq_client()
    if groq:
        try:
            resp = groq.chat.completions.create(
                model=config.GROQ_MODEL or "llama-3.1-8b-instant",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return str(resp.choices[0].message.content).strip()
        except Exception as exc:
            logger.warning("Groq API failed, falling back to OpenAI: %s", exc)

    openai = _get_openai_client()
    if openai:
        try:
            model = getattr(config, "OPENAI_MODEL", None) or "gpt-4o-mini"
            resp = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return str(resp.choices[0].message.content).strip()
        except Exception as exc:
            logger.error("OpenAI API also failed: %s", exc)
            raise

    raise RuntimeError("No AI provider available - set GROQ_API_KEY or OPENAI_API_KEY")


def extract_jd_keywords(job_description: str) -> dict[str, Any]:
    """
    Extract ATS keywords from a job description.

    Returns:
        {"tech": [...], "soft": [...], "level": "intern|junior|mid"}
    """
    system = "You are an ATS expert. Return ONLY valid JSON, no markdown."

    jd_text = str(job_description or "")
    prompt = (
        "Given this job description, extract:\n"
        "1. Top 10 technical skills / keywords (exact phrasing from JD)\n"
        "2. Top 5 soft skills / competencies\n"
        "3. Seniority level (intern / junior / mid)\n\n"
        'Return JSON: { "tech": [...], "soft": [...], "level": "..." }\n\n'
        f"JD:\n{jd_text[:3000]}"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = _call_llm(messages, temperature=0.1, max_tokens=500)
        clean = _strip_code_fences(raw)
        parsed = json.loads(clean)
        return parsed if isinstance(parsed, dict) else {"tech": [], "soft": [], "level": "intern"}
    except Exception as exc:
        logger.error("Failed to extract keywords: %s", exc)
        return {"tech": [], "soft": [], "level": "intern"}


def rewrite_bullets(original_bullets: list[str], keywords: dict[str, Any]) -> list[str]:
    """Rewrite resume bullets using ATS keywords."""
    if not original_bullets:
        return []

    system = "You are a professional resume writer specializing in ATS optimization."
    prompt = (
        "Rewrite these resume bullets to better match the job description.\n"
        "Use the extracted keywords where appropriate.\n"
        "Keep each bullet under 120 characters.\n"
        "Do not invent accomplishments; only rewrite existing ones.\n\n"
        f"Keywords: {keywords}\n"
        f"Bullets:\n{original_bullets}\n\n"
        'Return JSON list of strings: ["rewritten bullet 1", ...]'
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = _call_llm(messages, temperature=0.3, max_tokens=1500)
        clean = _strip_code_fences(raw)

        bullets_raw = json.loads(clean)
        if not isinstance(bullets_raw, list):
            raise ValueError("Response is not a list")

        bullets = [str(b) for b in bullets_raw]
        if len(bullets) < len(original_bullets):
            bullets.extend(str(original_bullets[i]) for i in range(len(bullets), len(original_bullets)))
        elif len(bullets) > len(original_bullets):
            bullets = bullets[: len(original_bullets)]

        for idx, bullet in enumerate(bullets):
            if len(bullet) > 120:
                bullets[idx] = bullet[:117] + "..."

        return bullets
    except Exception as exc:
        logger.error("Failed to rewrite bullets as JSON: %s", exc)
        try:
            fallback_lines = []
            raw_text = _strip_code_fences(str(raw)) if "raw" in locals() else ""
            for line in raw_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                bullet_match = re.match(r"^(?:[-*]|\d+[.)])\s+(.*)$", stripped)
                if bullet_match:
                    fallback_lines.append(bullet_match.group(1).strip())
                elif fallback_lines:
                    fallback_lines[-1] = f"{fallback_lines[-1]} {stripped}"

            if fallback_lines:
                if len(fallback_lines) < len(original_bullets):
                    fallback_lines.extend(
                        str(original_bullets[i])
                        for i in range(len(fallback_lines), len(original_bullets))
                    )
                return [line[:117] + "..." if len(line) > 120 else line for line in fallback_lines[: len(original_bullets)]]
        except Exception as fallback_exc:
            logger.warning("Bullet fallback parsing failed: %s", fallback_exc)

        return list(original_bullets)


def _rewrite_summary(original_summary: str, keywords: dict[str, Any], profile: dict[str, Any]) -> str:
    """Rewrite the summary paragraph."""
    if not original_summary:
        return ""

    tech = list(keywords.get("tech", []))[:5]
    soft = list(keywords.get("soft", []))[:3]
    keyword_terms = ", ".join([str(item) for item in (tech + soft) if item])

    prompt = (
        "Rewrite this resume summary for ATS optimization.\n"
        f"Original Summary: {original_summary}\n"
        f"Keywords: {keyword_terms}\n"
        f"Profile: {profile}\n\n"
        "Keep the summary concise, specific, and human."
    )

    messages = [
        {"role": "system", "content": "You are a professional resume writer specializing in ATS optimization."},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = _call_llm(messages, temperature=0.25, max_tokens=250)
        clean = _strip_code_fences(raw)
        clean = clean.replace("**", "").replace("__", "").strip()

        # Prefer the best plain-text paragraph and discard prompt leakage or bullet lists.
        candidate_lines = []
        for line in clean.splitlines():
            stripped = line.strip().strip("-•*")
            if not stripped:
                continue
            lower = stripped.lower()
            if lower.startswith("summary:"):
                stripped = stripped.split(":", 1)[1].strip()
                lower = stripped.lower()
            if any(
                marker in lower
                for marker in (
                    "rewritten ats-optimized summary",
                    "ats optimization",
                    "i made the following",
                    "this rewritten summary",
                    "changes for ats optimization",
                    "should improve",
                )
            ):
                continue
            if re.match(r"^\d+[.)]\s+", stripped):
                continue
            candidate_lines.append(stripped)

        if candidate_lines:
            best = max(candidate_lines, key=len).strip()
            if best:
                return best

        return clean
    except Exception as exc:
        logger.warning("Failed to rewrite summary: %s", exc)
        return original_summary


def _profile_dict(profile: Optional[Any] = None) -> dict[str, Any]:
    """Normalize profile objects/dicts into a plain dictionary."""
    if profile is None:
        profile = get_profile()
    if hasattr(profile, "data"):
        return dict(profile.data)
    if isinstance(profile, dict):
        return dict(profile)
    return dict(getattr(profile, "__dict__", {}))


def _build_bullet_library(profile_dict: dict[str, Any]) -> dict[str, list[str]]:
    """
    Build a rewrite-friendly bullet library from multiple profile shapes.

    Supports:
    - legacy bullet_library dicts
    - structured ats.experience / ats.projects sections
    - simpler experience_highlights / project_highlights lists
    """
    if isinstance(profile_dict.get("bullet_library"), dict):
        result: dict[str, list[str]] = {}
        for key, value in profile_dict["bullet_library"].items():
            if isinstance(value, list):
                result[str(key)] = [str(item) for item in value if str(item).strip()]
        return result

    bullet_library: dict[str, list[str]] = {}
    ats_section = profile_dict.get("ats", {})
    if isinstance(ats_section, dict):
        experience_items = ats_section.get("experience", [])
        if isinstance(experience_items, list) and experience_items:
            first_experience = experience_items[0]
            if isinstance(first_experience, dict):
                bullets = first_experience.get("bullets") or first_experience.get("points") or []
                if isinstance(bullets, list) and bullets:
                    bullet_library["intellect"] = [str(item) for item in bullets if str(item).strip()]

        project_items = ats_section.get("projects", [])
        if isinstance(project_items, list) and project_items:
            project_keys = ["yaanbarpe", "crimeconnect", "medrag", "florafight", "hackops"]
            for idx, project in enumerate(project_items[: len(project_keys)]):
                if not isinstance(project, dict):
                    continue
                bullets = project.get("bullets") or project.get("points") or []
                if isinstance(bullets, list) and bullets:
                    bullet_library[project_keys[idx]] = [str(item) for item in bullets if str(item).strip()]

    if bullet_library:
        return bullet_library

    experience_highlights = profile_dict.get("experience_highlights", [])
    if isinstance(experience_highlights, list) and experience_highlights:
        bullet_library["intellect"] = [str(item) for item in experience_highlights if str(item).strip()]

    project_highlights = profile_dict.get("project_highlights", [])
    if isinstance(project_highlights, list) and project_highlights:
        project_keys = ["yaanbarpe", "crimeconnect", "medrag", "florafight", "hackops"]
        for idx, highlight in enumerate(project_highlights[: len(project_keys)]):
            bullet_library[project_keys[idx]] = [str(highlight)]

    return bullet_library


def rewrite_cv(jd_text: str, profile: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Run the full resume rewrite pipeline."""
    profile_dict = _profile_dict(profile)
    logger.info("Rewriting CV for JD snippet: %s", str(jd_text or "")[:500])

    keywords = extract_jd_keywords(jd_text)
    bullet_library = _build_bullet_library(profile_dict)
    rewritten_blocks: dict[str, Any] = {}

    for block_name, original in bullet_library.items():
        if isinstance(original, list) and original:
            rewritten_blocks[block_name] = rewrite_bullets(original, keywords)
        else:
            rewritten_blocks[block_name] = original

    summary_text = (
        profile_dict.get("summary")
        or profile_dict.get("experience_summary")
        or profile_dict.get("ats", {}).get("summary", "")
    )
    rewritten_summary = _rewrite_summary(str(summary_text), keywords, profile_dict)

    return {
        "keywords": keywords,
        "bullets": rewritten_blocks,
        "summary": rewritten_summary,
    }

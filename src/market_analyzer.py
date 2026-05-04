from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .jd_parser import jd_snippets, load_job_descriptions
from .skill_extractor import (
    extract_project_themes,
    extract_responsibility_signals,
    extract_skill_signals,
    top_skills,
)


def _chat_with_ollama(prompt: str, model: str, host: str) -> str:
    try:
        from ollama import Client

        client = Client(host=host)
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2},
        )
        return response["message"]["content"]
    except Exception as exc:
        return f"[fallback] Ollama response unavailable: {exc}"


def _load_prompt(prompt_path: str | Path) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def run_jd_intelligence_engine(
    raw_jd_dir: str | Path,
    prompt_path: str | Path,
    output_dir: str | Path,
    model: str,
    host: str,
) -> Dict[str, Any]:
    jds = load_job_descriptions(raw_jd_dir)
    skill_signals = extract_skill_signals(jds)
    responsibility_signals = extract_responsibility_signals(jds)
    project_themes = extract_project_themes(skill_signals)
    ranked_skills = top_skills(skill_signals)

    role_distribution: Dict[str, int] = {}
    for jd in jds:
        role_distribution[jd.role] = role_distribution.get(jd.role, 0) + 1

    payload: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "jd_count": len(jds),
        "role_distribution": role_distribution,
        "top_skills": ranked_skills,
        "skill_frequency": skill_signals,
        "repeated_responsibilities": responsibility_signals,
        "project_worthy_themes": project_themes,
    }

    prompt_template = _load_prompt(prompt_path)
    prompt = prompt_template.format(
        jd_count=len(jds),
        analysis_json=json.dumps(payload, indent=2),
        jd_snippets=jd_snippets(jds),
    )
    llm_summary = _chat_with_ollama(prompt, model=model, host=host)
    payload["llm_market_summary"] = llm_summary

    out_base = Path(output_dir)
    out_base.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_base / f"market_report_{timestamp}.json"
    md_path = out_base / f"market_report_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# MarketFit-AI JD Intelligence Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"JD Count: {payload['jd_count']}",
        "",
        "## Top Skills",
    ]
    for row in ranked_skills:
        lines.append(
            f"- {row['skill']}: {row['documents_with_skill']} docs, {row['total_mentions']} mentions"
        )

    lines.append("")
    lines.append("## Repeated Responsibilities")
    for row in responsibility_signals:
        lines.append(f"- ({row['frequency']}x) {row['responsibility']}")

    lines.append("")
    lines.append("## Project-Worthy Themes")
    for row in project_themes:
        lines.append(f"- {row['theme']} (score: {row['score']})")

    lines.append("")
    lines.append("## Ollama Market Narrative")
    lines.append(llm_summary)

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload["output_files"] = {
        "market_report_json": str(json_path),
        "market_report_markdown": str(md_path),
    }
    return payload

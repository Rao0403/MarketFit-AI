from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .jd_parser import load_job_descriptions
from .skill_extractor import (
    extract_cluster_frequency,
    extract_project_themes,
    extract_responsibility_signals,
    extract_role_expectations,
    extract_role_tag_counts,
    extract_signal_frequency,
    split_signal_frequency,
    top_skills,
    top_tools,
)


def _to_skill_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed = []
    for row in rows:
        transformed.append(
            {
                "skill": row["name"],
                "cluster": row["cluster"],
                "documents_with_skill": row["documents_with_signal"],
                "total_mentions": row["total_mentions"],
            }
        )
    return transformed


def _to_tool_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed = []
    for row in rows:
        transformed.append(
            {
                "tool": row["name"],
                "cluster": row["cluster"],
                "documents_with_tool": row["documents_with_signal"],
                "total_mentions": row["total_mentions"],
            }
        )
    return transformed


def run_jd_intelligence_engine(
    raw_jd_dir: str | Path,
    prompt_path: str | Path,
    output_dir: str | Path,
    model: str,
    host: str,
) -> Dict[str, Any]:
    _ = prompt_path
    _ = model
    _ = host

    jds = load_job_descriptions(raw_jd_dir)

    signal_frequency = extract_signal_frequency(jds)
    split_frequency = split_signal_frequency(signal_frequency)
    ranked_skills = _to_skill_rows(top_skills(signal_frequency, top_k=12))
    ranked_tools = _to_tool_rows(top_tools(signal_frequency, top_k=12))

    role_distribution: Dict[str, int] = {}
    for jd in jds:
        role_distribution[jd.role] = role_distribution.get(jd.role, 0) + 1

    payload: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jd_count": len(jds),
        "source_files": [jd.file_name for jd in jds],
        "role_distribution": role_distribution,
        "role_tag_distribution": extract_role_tag_counts(jds),
        "top_skills": ranked_skills,
        "top_tools": ranked_tools,
        "skill_frequency": split_frequency["skill_frequency"],
        "tool_frequency": split_frequency["tool_frequency"],
        "cluster_frequency": extract_cluster_frequency(signal_frequency),
        "common_role_expectations": extract_role_expectations(jds),
        "repeated_responsibilities": extract_responsibility_signals(jds),
        "project_worthy_themes": extract_project_themes(signal_frequency),
    }

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
            f"- {row['skill']} ({row['cluster']}): {row['documents_with_skill']} docs, {row['total_mentions']} mentions"
        )

    lines.append("")
    lines.append("## Top Tools")
    for row in ranked_tools:
        lines.append(
            f"- {row['tool']} ({row['cluster']}): {row['documents_with_tool']} docs, {row['total_mentions']} mentions"
        )

    lines.append("")
    lines.append("## Common Role Expectations")
    for row in payload["common_role_expectations"][:12]:
        lines.append(f"- ({row['frequency']}x) {row['expectation']}")

    lines.append("")
    lines.append("## Repeated Responsibilities")
    for row in payload["repeated_responsibilities"][:12]:
        lines.append(f"- ({row['frequency']}x) {row['responsibility']}")

    lines.append("")
    lines.append("## Project-Worthy Themes")
    for row in payload["project_worthy_themes"]:
        evidence = ", ".join(row.get("evidence_signals", []))
        lines.append(f"- {row['theme']} (score: {row['score']}, evidence: {evidence})")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload["output_files"] = {
        "market_report_json": str(json_path),
        "market_report_markdown": str(md_path),
    }
    return payload

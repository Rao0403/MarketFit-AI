from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .jd_parser import load_job_descriptions
from .skill_clusterer import assign_clusters, build_cluster_counts, load_cluster_map
from .skill_extractor import (
    extract_project_themes,
    extract_responsibility_signals,
    extract_role_expectations,
    extract_role_tag_counts,
    extract_signal_frequency,
)
from .trend_analyzer import build_trend_payload


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


def _split_frequency(clustered_signal_frequency: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    skill_frequency: Dict[str, Dict[str, Any]] = {}
    tool_frequency: Dict[str, Dict[str, Any]] = {}

    for signal, payload in clustered_signal_frequency.items():
        compact = {
            "documents_with_signal": payload["documents_with_signal"],
            "total_mentions": payload["total_mentions"],
            "cluster": payload["cluster"],
        }

        if payload.get("signal_type") == "tool":
            tool_frequency[signal] = compact
        else:
            skill_frequency[signal] = compact

    return {"skill_frequency": skill_frequency, "tool_frequency": tool_frequency}


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
    cluster_map = load_cluster_map(Path(raw_jd_dir).parent / "processed" / "skill_cluster_map.json")
    clustered_signal_frequency = assign_clusters(signal_frequency, cluster_map)

    cluster_counts = build_cluster_counts(clustered_signal_frequency)
    trend_payload = build_trend_payload(clustered_signal_frequency, cluster_counts, top_k=12)
    split_frequency = _split_frequency(clustered_signal_frequency)

    ranked_skills = _to_skill_rows(trend_payload["ranked_skills"])
    ranked_tools = _to_tool_rows(trend_payload["ranked_tools"])

    role_distribution: Dict[str, int] = {}
    for jd in jds:
        role_distribution[jd.role] = role_distribution.get(jd.role, 0) + 1

    payload: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jd_count": len(jds),
        "source_files": [jd.file_name for jd in jds],
        "role_distribution": role_distribution,
        "role_tag_distribution": extract_role_tag_counts(jds),
        "cluster_map": cluster_map,
        "top_skills": ranked_skills,
        "top_tools": ranked_tools,
        "skill_frequency": split_frequency["skill_frequency"],
        "tool_frequency": split_frequency["tool_frequency"],
        "cluster_frequency": cluster_counts,
        "trend_layer": trend_payload,
        "common_role_expectations": extract_role_expectations(jds),
        "repeated_responsibilities": extract_responsibility_signals(jds),
        "project_worthy_themes": extract_project_themes(clustered_signal_frequency),
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
        "## Cluster Trend Table",
    ]

    for row in trend_payload["cluster_trend_table"]:
        lines.append(
            f"- {row['cluster']}: score={row['cluster_score']}, docs={row['documents_with_signal_total']}, mentions={row['total_mentions']}"
        )

    lines.append("")
    lines.append("## Top Skills")
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

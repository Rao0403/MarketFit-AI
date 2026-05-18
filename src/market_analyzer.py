from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .jd_parser import jd_snippets, load_job_descriptions
from .skill_clusterer import assign_clusters, build_cluster_counts, load_cluster_map
from .skill_extractor import (
    extract_project_themes,
    extract_responsibility_signals,
    extract_role_expectations,
    extract_role_tag_counts,
    extract_signal_frequency,
)
from .trend_analyzer import build_trend_payload


REQUIRED_KEYS = {
    "role_distribution",
    "role_tag_distribution",
    "top_skills",
    "top_tools",
    "skill_frequency",
    "tool_frequency",
    "cluster_frequency",
    "trend_layer",
    "common_role_expectations",
    "repeated_responsibilities",
    "project_worthy_themes",
}


def _chat_with_ollama(prompt: str, model: str, host: str) -> str:
    try:
        from ollama import Client

        client = Client(host=host)
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.1},
        )
        return response["message"]["content"]
    except Exception as exc:
        return f"[fallback] Ollama response unavailable: {exc}"


def _load_prompt(prompt_path: str | Path) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def _extract_json_candidates(text: str) -> List[str]:
    candidates: List[str] = []
    if not text:
        return candidates

    fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    for block in fenced_blocks:
        block = block.strip()
        if block:
            candidates.append(block)

    trimmed = text.strip()
    if trimmed:
        candidates.append(trimmed)

    first_obj = text.find("{")
    last_obj = text.rfind("}")
    if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
        candidates.append(text[first_obj : last_obj + 1].strip())

    seen = set()
    unique_candidates: List[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    return unique_candidates


def _has_required_structure(payload: Dict[str, Any]) -> bool:
    if not REQUIRED_KEYS.issubset(set(payload.keys())):
        return False
    if not isinstance(payload.get("top_skills"), list):
        return False
    if not isinstance(payload.get("top_tools"), list):
        return False
    if not isinstance(payload.get("skill_frequency"), dict):
        return False
    if not isinstance(payload.get("tool_frequency"), dict):
        return False
    if not isinstance(payload.get("cluster_frequency"), dict):
        return False
    if not isinstance(payload.get("trend_layer"), dict):
        return False
    if not _has_meaningful_content(payload):
        return False
    return True


def _has_meaningful_content(payload: Dict[str, Any]) -> bool:
    role_distribution = payload.get("role_distribution", {})
    if not isinstance(role_distribution, dict) or not role_distribution:
        return False

    invalid_role_keys = any("<" in str(key) or ">" in str(key) for key in role_distribution.keys())
    if invalid_role_keys:
        return False

    if sum(int(value) for value in role_distribution.values() if isinstance(value, (int, float))) <= 0:
        return False

    top_skills = payload.get("top_skills", [])
    if not isinstance(top_skills, list) or len(top_skills) == 0:
        return False

    has_non_placeholder_skill = False
    for row in top_skills:
        if not isinstance(row, dict):
            continue
        skill = str(row.get("skill", ""))
        if skill and "<" not in skill and ">" not in skill:
            has_non_placeholder_skill = True
            break
    if not has_non_placeholder_skill:
        return False

    trend_layer = payload.get("trend_layer", {})
    cluster_rows = trend_layer.get("cluster_trend_table", []) if isinstance(trend_layer, dict) else []
    if not isinstance(cluster_rows, list) or len(cluster_rows) == 0:
        return False

    return True


def _try_parse_llm_payload(text: str) -> Dict[str, Any] | None:
    if not text or text.startswith("[fallback]"):
        return None

    for candidate in _extract_json_candidates(text):
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue

        if isinstance(parsed, dict) and _has_required_structure(parsed):
            return parsed
    return None


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


def _build_deterministic_payload(raw_jd_dir: str | Path) -> Dict[str, Any]:
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
    return payload


def _write_market_report(payload: Dict[str, Any], output_dir: str | Path) -> Dict[str, Any]:
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
        f"Extraction Source: {payload.get('extraction_source', 'unknown')}",
        "",
        "## Cluster Trend Table",
    ]

    for row in payload.get("trend_layer", {}).get("cluster_trend_table", []):
        lines.append(
            f"- {row['cluster']}: score={row['cluster_score']}, docs={row['documents_with_signal_total']}, mentions={row['total_mentions']}"
        )

    lines.append("")
    lines.append("## Top Skills")
    for row in payload.get("top_skills", [])[:12]:
        lines.append(
            f"- {row['skill']} ({row['cluster']}): {row['documents_with_skill']} docs, {row['total_mentions']} mentions"
        )

    lines.append("")
    lines.append("## Top Tools")
    for row in payload.get("top_tools", [])[:12]:
        lines.append(
            f"- {row['tool']} ({row['cluster']}): {row['documents_with_tool']} docs, {row['total_mentions']} mentions"
        )

    lines.append("")
    lines.append("## Common Role Expectations")
    for row in payload.get("common_role_expectations", [])[:12]:
        lines.append(f"- ({row['frequency']}x) {row['expectation']}")

    lines.append("")
    lines.append("## Repeated Responsibilities")
    for row in payload.get("repeated_responsibilities", [])[:12]:
        lines.append(f"- ({row['frequency']}x) {row['responsibility']}")

    lines.append("")
    lines.append("## Project-Worthy Themes")
    for row in payload.get("project_worthy_themes", []):
        evidence = ", ".join(row.get("evidence_signals", []))
        lines.append(f"- {row['theme']} (score: {row['score']}, evidence: {evidence})")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload["output_files"] = {
        "market_report_json": str(json_path),
        "market_report_markdown": str(md_path),
    }
    return payload


def run_jd_intelligence_engine(
    raw_jd_dir: str | Path,
    prompt_path: str | Path,
    output_dir: str | Path,
    model: str,
    host: str,
) -> Dict[str, Any]:
    deterministic_payload = _build_deterministic_payload(raw_jd_dir)
    jds = load_job_descriptions(raw_jd_dir)

    prompt_template = _load_prompt(prompt_path)
    prompt = prompt_template.format(
        jd_count=deterministic_payload["jd_count"],
        cluster_map_json=json.dumps(deterministic_payload["cluster_map"], indent=2),
        baseline_json=json.dumps(deterministic_payload, indent=2),
        jd_snippets=jd_snippets(jds, max_chars=1800),
    )

    llm_raw = _chat_with_ollama(prompt, model=model, host=host)
    llm_payload = _try_parse_llm_payload(llm_raw)

    if llm_payload is not None:
        payload = llm_payload
        payload["extraction_source"] = "llm"
    else:
        payload = deterministic_payload
        payload["extraction_source"] = "rule_based_fallback"

    # Keep runtime-grounded metadata authoritative.
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["jd_count"] = deterministic_payload["jd_count"]
    payload["source_files"] = deterministic_payload["source_files"]
    payload["cluster_map"] = deterministic_payload["cluster_map"]
    payload["llm_extraction_raw_response"] = llm_raw

    return _write_market_report(payload, output_dir)

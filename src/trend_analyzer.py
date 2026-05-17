from __future__ import annotations

from typing import Any, Dict, List


def rank_signals(
    clustered_signal_frequency: Dict[str, Dict[str, Any]],
    signal_type: str,
    top_k: int = 12,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for signal, payload in clustered_signal_frequency.items():
        if payload.get("signal_type") != signal_type:
            continue
        rows.append(
            {
                "name": signal,
                "cluster": payload.get("cluster", "Uncategorized"),
                "documents_with_signal": int(payload.get("documents_with_signal", 0)),
                "total_mentions": int(payload.get("total_mentions", 0)),
            }
        )

    rows.sort(
        key=lambda row: (row["documents_with_signal"], row["total_mentions"]),
        reverse=True,
    )
    return rows[:top_k]


def build_cluster_trend_table(
    cluster_counts: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    table: List[Dict[str, Any]] = []
    for cluster, payload in cluster_counts.items():
        table.append(
            {
                "cluster": cluster,
                "cluster_score": payload["cluster_score"],
                "documents_with_signal_total": payload["documents_with_signal_total"],
                "total_mentions": payload["total_mentions"],
                "skills": payload["skills"],
                "tools": payload["tools"],
                "signals": payload["signals"],
            }
        )

    table.sort(key=lambda row: row["cluster_score"], reverse=True)
    return table


def build_trend_payload(
    clustered_signal_frequency: Dict[str, Dict[str, Any]],
    cluster_counts: Dict[str, Dict[str, Any]],
    top_k: int = 12,
) -> Dict[str, Any]:
    ranked_skills = rank_signals(clustered_signal_frequency, signal_type="skill", top_k=top_k)
    ranked_tools = rank_signals(clustered_signal_frequency, signal_type="tool", top_k=top_k)
    cluster_trend_table = build_cluster_trend_table(cluster_counts)

    return {
        "cluster_trend_table": cluster_trend_table,
        "ranked_skills": ranked_skills,
        "ranked_tools": ranked_tools,
    }

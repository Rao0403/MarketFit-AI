from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_cluster_map(path: str | Path) -> Dict[str, List[str]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return {cluster: list(signals) for cluster, signals in payload.items()}


def _reverse_index(cluster_map: Dict[str, List[str]]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for cluster, signals in cluster_map.items():
        for signal in signals:
            index[signal] = cluster
    return index


def assign_clusters(
    signal_frequency: Dict[str, Dict[str, Any]],
    cluster_map: Dict[str, List[str]],
) -> Dict[str, Dict[str, Any]]:
    index = _reverse_index(cluster_map)
    enriched: Dict[str, Dict[str, Any]] = {}

    for signal, payload in signal_frequency.items():
        cluster = index.get(signal, "Uncategorized")
        enriched[signal] = {**payload, "cluster": cluster}

    return enriched


def build_cluster_counts(
    clustered_signal_frequency: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    cluster_counts: Dict[str, Dict[str, Any]] = {}

    for signal, payload in clustered_signal_frequency.items():
        cluster = payload["cluster"]
        cluster_payload = cluster_counts.setdefault(
            cluster,
            {
                "documents_with_signal_total": 0,
                "total_mentions": 0,
                "skills": 0,
                "tools": 0,
                "signals": [],
                "cluster_score": 0.0,
            },
        )

        cluster_payload["documents_with_signal_total"] += int(payload["documents_with_signal"])
        cluster_payload["total_mentions"] += int(payload["total_mentions"])
        cluster_payload["signals"].append(signal)
        if payload.get("signal_type") == "tool":
            cluster_payload["tools"] += 1
        else:
            cluster_payload["skills"] += 1

    for cluster_payload in cluster_counts.values():
        cluster_payload["signals"] = sorted(cluster_payload["signals"])
        # Weighted score: emphasizes breadth across JDs and mention depth.
        cluster_payload["cluster_score"] = round(
            cluster_payload["documents_with_signal_total"] * 0.7
            + cluster_payload["total_mentions"] * 0.3,
            2,
        )

    return cluster_counts

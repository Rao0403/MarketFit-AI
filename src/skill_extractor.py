from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List

from .jd_parser import JobDescription


SIGNAL_CATALOG: Dict[str, Dict[str, Any]] = {
    "python": {"aliases": ["python"], "type": "skill", "cluster": "Software Engineering"},
    "sql": {"aliases": ["sql"], "type": "skill", "cluster": "Data/ML Foundations"},
    "statistics": {"aliases": ["statistics", "probability"], "type": "skill", "cluster": "Data/ML Foundations"},
    "machine_learning": {"aliases": ["machine learning", "ml"], "type": "skill", "cluster": "Data/ML Foundations"},
    "deep_learning": {"aliases": ["deep learning", "neural network"], "type": "skill", "cluster": "Data/ML Foundations"},
    "llms": {"aliases": ["llm", "large language model", "language model"], "type": "skill", "cluster": "LLM Systems"},
    "prompt_engineering": {"aliases": ["prompt engineering", "prompt strategy", "prompting"], "type": "skill", "cluster": "LLM Systems"},
    "transformers": {"aliases": ["transformer", "transformers"], "type": "skill", "cluster": "LLM Systems"},
    "fine_tuning": {"aliases": ["fine-tune", "fine tuning", "lora", "qlora", "rlhf"], "type": "skill", "cluster": "LLM Systems"},
    "rag": {"aliases": ["rag", "retrieval augmented"], "type": "skill", "cluster": "RAG"},
    "retrieval": {"aliases": ["retrieval", "reranking", "semantic search"], "type": "skill", "cluster": "RAG"},
    "vector_databases": {"aliases": ["vector database", "vector db", "faiss", "pinecone", "weaviate", "chroma"], "type": "skill", "cluster": "RAG"},
    "agentic_workflows": {"aliases": ["agentic", "multi-agent", "tool use", "tool-using"], "type": "skill", "cluster": "Agents"},
    "tool_orchestration": {"aliases": ["orchestration", "workflow automation", "planner"], "type": "skill", "cluster": "Agents"},
    "model_evaluation": {"aliases": ["evaluation", "benchmark", "ablation", "factuality", "robustness"], "type": "skill", "cluster": "Evaluation"},
    "safety_guardrails": {"aliases": ["safety", "guardrails", "hallucination"], "type": "skill", "cluster": "Evaluation"},
    "deployment": {"aliases": ["deployment", "serving", "inference pipeline", "production"], "type": "skill", "cluster": "Deployment"},
    "mlops": {"aliases": ["mlops", "monitoring", "observability", "ci/cd"], "type": "skill", "cluster": "Deployment"},
    "langchain": {"aliases": ["langchain"], "type": "tool", "cluster": "LLM Systems"},
    "llamaindex": {"aliases": ["llamaindex"], "type": "tool", "cluster": "LLM Systems"},
    "pytorch": {"aliases": ["pytorch"], "type": "tool", "cluster": "Data/ML Foundations"},
    "tensorflow": {"aliases": ["tensorflow"], "type": "tool", "cluster": "Data/ML Foundations"},
    "huggingface": {"aliases": ["hugging face", "huggingface"], "type": "tool", "cluster": "LLM Systems"},
    "fastapi": {"aliases": ["fastapi"], "type": "tool", "cluster": "Deployment"},
    "docker": {"aliases": ["docker"], "type": "tool", "cluster": "Deployment"},
    "kubernetes": {"aliases": ["kubernetes", "k8s"], "type": "tool", "cluster": "Deployment"},
    "github_actions": {"aliases": ["github actions"], "type": "tool", "cluster": "Deployment"},
    "wandb": {"aliases": ["wandb", "weights and biases"], "type": "tool", "cluster": "Evaluation"},
}

PROJECT_THEME_MAP: Dict[str, List[str]] = {
    "production_rag_systems": ["rag", "retrieval", "vector_databases", "fastapi"],
    "llm_evaluation_and_safety": ["model_evaluation", "safety_guardrails", "wandb"],
    "agentic_ai_automation": ["agentic_workflows", "tool_orchestration", "llms"],
    "applied_deployment_and_mlops": ["deployment", "mlops", "docker", "kubernetes", "github_actions"],
    "llm_customization_and_adaptation": ["fine_tuning", "transformers", "huggingface"],
}

RESPONSIBILITY_VERBS = (
    "build",
    "develop",
    "deploy",
    "design",
    "implement",
    "evaluate",
    "collaborate",
    "reproduce",
    "run",
    "curate",
    "present",
    "maintain",
    "optimize",
)

EXPECTATION_HINTS = (
    "required",
    "requirements",
    "experience with",
    "familiarity with",
    "strong",
    "ability to",
    "understanding of",
    "knowledge of",
)


def _count_mentions(text: str, phrase: str) -> int:
    escaped = re.escape(phrase)
    pattern = rf"(?<!\w){escaped}(?!\w)"
    return len(re.findall(pattern, text.lower()))


def _normalize_line(line: str) -> str:
    line = line.strip(" -*\t")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def extract_signal_frequency(jds: List[JobDescription]) -> Dict[str, Dict[str, Any]]:
    signals: Dict[str, Dict[str, Any]] = {}
    for signal, meta in SIGNAL_CATALOG.items():
        doc_hits = 0
        total_mentions = 0
        for jd in jds:
            text = jd.content.lower()
            mentions = sum(_count_mentions(text, alias.lower()) for alias in meta["aliases"])
            if mentions > 0:
                doc_hits += 1
                total_mentions += mentions

        signals[signal] = {
            "documents_with_signal": doc_hits,
            "total_mentions": total_mentions,
            "signal_type": meta["type"],
            "cluster": meta["cluster"],
            "aliases": meta["aliases"],
        }
    return signals


def split_signal_frequency(signal_frequency: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    skill_frequency: Dict[str, Dict[str, Any]] = {}
    tool_frequency: Dict[str, Dict[str, Any]] = {}

    for signal, payload in signal_frequency.items():
        compact = {
            "documents_with_signal": payload["documents_with_signal"],
            "total_mentions": payload["total_mentions"],
            "cluster": payload["cluster"],
        }
        if payload["signal_type"] == "tool":
            tool_frequency[signal] = compact
        else:
            skill_frequency[signal] = compact

    return {"skill_frequency": skill_frequency, "tool_frequency": tool_frequency}


def _top_entities(
    signal_frequency: Dict[str, Dict[str, Any]],
    signal_type: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    rows = []
    for signal, payload in signal_frequency.items():
        if payload["signal_type"] != signal_type:
            continue
        rows.append(
            {
                "name": signal,
                "cluster": payload["cluster"],
                "documents_with_signal": payload["documents_with_signal"],
                "total_mentions": payload["total_mentions"],
            }
        )

    rows.sort(
        key=lambda row: (row["documents_with_signal"], row["total_mentions"]),
        reverse=True,
    )
    return rows[:top_k]


def top_skills(signal_frequency: Dict[str, Dict[str, Any]], top_k: int = 12) -> List[Dict[str, Any]]:
    return _top_entities(signal_frequency, signal_type="skill", top_k=top_k)


def top_tools(signal_frequency: Dict[str, Dict[str, Any]], top_k: int = 12) -> List[Dict[str, Any]]:
    return _top_entities(signal_frequency, signal_type="tool", top_k=top_k)


def extract_cluster_frequency(signal_frequency: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    cluster_accumulator: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "documents_with_signal_total": 0,
            "total_mentions": 0,
            "signals": set(),
        }
    )

    for signal, payload in signal_frequency.items():
        cluster = payload["cluster"]
        cluster_accumulator[cluster]["documents_with_signal_total"] += payload["documents_with_signal"]
        cluster_accumulator[cluster]["total_mentions"] += payload["total_mentions"]
        cluster_accumulator[cluster]["signals"].add(signal)

    output: Dict[str, Dict[str, Any]] = {}
    for cluster, payload in cluster_accumulator.items():
        output[cluster] = {
            "documents_with_signal_total": payload["documents_with_signal_total"],
            "total_mentions": payload["total_mentions"],
            "signals": sorted(payload["signals"]),
        }
    return output


def extract_responsibility_signals(jds: List[JobDescription], top_k: int = 20) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()

    for jd in jds:
        for raw_line in jd.content.splitlines():
            line = _normalize_line(raw_line)
            if len(line.split()) < 5:
                continue

            lower = line.lower()
            if any(hint in lower for hint in EXPECTATION_HINTS):
                continue
            if any(lower.startswith(verb) for verb in RESPONSIBILITY_VERBS):
                counter[line] += 1
                continue

            if raw_line.strip().startswith(("-", "*")) and any(
                f" {verb} " in f" {lower} " for verb in RESPONSIBILITY_VERBS
            ):
                counter[line] += 1

    return [
        {"responsibility": responsibility, "frequency": frequency}
        for responsibility, frequency in counter.most_common(top_k)
    ]


def extract_role_expectations(jds: List[JobDescription], top_k: int = 20) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()

    for jd in jds:
        for raw_line in jd.content.splitlines():
            line = _normalize_line(raw_line)
            if len(line.split()) < 4:
                continue
            lower = line.lower()
            if any(hint in lower for hint in EXPECTATION_HINTS):
                counter[line] += 1

    return [
        {"expectation": expectation, "frequency": frequency}
        for expectation, frequency in counter.most_common(top_k)
    ]


def extract_project_themes(signal_frequency: Dict[str, Dict[str, Any]], top_k: int = 8) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for theme, signals in PROJECT_THEME_MAP.items():
        score = 0
        evidence: List[str] = []
        for signal in signals:
            payload = signal_frequency.get(signal)
            if not payload:
                continue
            score += payload["documents_with_signal"]
            if payload["documents_with_signal"] > 0:
                evidence.append(signal)

        scored.append({"theme": theme, "score": score, "evidence_signals": evidence})

    scored.sort(key=lambda row: row["score"], reverse=True)
    return scored[:top_k]


def extract_role_tag_counts(jds: List[JobDescription]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for jd in jds:
        tags = jd.role_tags if jd.role_tags else [jd.role]
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    return counts

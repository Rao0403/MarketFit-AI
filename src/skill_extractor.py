from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

from .jd_parser import JobDescription


SKILL_KEYWORDS: Dict[str, List[str]] = {
    "python": ["python"],
    "llms": ["llm", "large language model", "language model"],
    "rag": ["rag", "retrieval augmented"],
    "vector_databases": ["vector database", "vector db", "faiss", "pinecone", "weaviate", "chroma"],
    "prompt_engineering": ["prompt engineering", "prompt strategy", "prompting"],
    "model_evaluation": ["evaluation", "benchmark", "ablation", "factuality", "robustness"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "transformers": ["transformer", "transformers", "hugging face"],
    "fine_tuning": ["fine-tune", "fine tuning", "lora", "qlora", "rlhf"],
    "mlops_deployment": ["docker", "kubernetes", "ci/cd", "github actions", "model serving", "deployment"],
    "agentic_workflows": ["agentic", "tool use", "reason over multiple tools"],
    "multimodal": ["multimodal"],
    "experiment_tracking": ["wandb", "weights and biases", "experiment tracking", "monitoring"],
}


PROJECT_THEME_MAP: Dict[str, List[str]] = {
    "production_rag_systems": ["rag", "vector_databases", "prompt_engineering"],
    "llm_evaluation_and_safety": ["model_evaluation", "llms"],
    "applied_model_deployment": ["mlops_deployment", "python"],
    "fine_tuning_and_adaptation": ["fine_tuning", "transformers"],
    "agentic_ai_automation": ["agentic_workflows", "llms"],
    "research_benchmarking": ["multimodal", "model_evaluation", "pytorch"],
}


RESPONSIBILITY_HINTS = (
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
)


def _count_mentions(text: str, phrase: str) -> int:
    escaped = re.escape(phrase)
    pattern = rf"\b{escaped}\b"
    return len(re.findall(pattern, text.lower()))


def extract_skill_signals(jds: List[JobDescription]) -> Dict[str, Dict[str, int]]:
    signals: Dict[str, Dict[str, int]] = {}
    for skill, aliases in SKILL_KEYWORDS.items():
        doc_hits = 0
        total_mentions = 0
        for jd in jds:
            text = jd.content.lower()
            mentions = sum(_count_mentions(text, alias.lower()) for alias in aliases)
            if mentions > 0:
                doc_hits += 1
                total_mentions += mentions
        signals[skill] = {
            "documents_with_skill": doc_hits,
            "total_mentions": total_mentions,
        }
    return signals


def extract_responsibility_signals(jds: List[JobDescription], top_k: int = 12) -> List[Dict[str, int | str]]:
    counter: Counter[str] = Counter()
    for jd in jds:
        for line in jd.content.splitlines():
            stripped = line.strip(" -\t").strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if any(lower.startswith(hint) for hint in RESPONSIBILITY_HINTS):
                counter[stripped] += 1

    return [
        {"responsibility": resp, "frequency": freq}
        for resp, freq in counter.most_common(top_k)
    ]


def extract_project_themes(skill_signals: Dict[str, Dict[str, int]], top_k: int = 6) -> List[Dict[str, int | str]]:
    scored = []
    for theme, required_skills in PROJECT_THEME_MAP.items():
        score = sum(skill_signals.get(skill, {}).get("documents_with_skill", 0) for skill in required_skills)
        scored.append({"theme": theme, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def top_skills(skill_signals: Dict[str, Dict[str, int]], top_k: int = 10) -> List[Dict[str, int | str]]:
    ranked = [
        {
            "skill": skill,
            "documents_with_skill": counts["documents_with_skill"],
            "total_mentions": counts["total_mentions"],
        }
        for skill, counts in skill_signals.items()
    ]
    ranked.sort(
        key=lambda x: (x["documents_with_skill"], x["total_mentions"]),
        reverse=True,
    )
    return ranked[:top_k]

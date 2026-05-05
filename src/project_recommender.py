from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _chat_with_ollama(prompt: str, model: str, host: str) -> str:
    try:
        from ollama import Client

        client = Client(host=host)
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3},
        )
        return response["message"]["content"]
    except Exception as exc:
        return f"[fallback] Ollama response unavailable: {exc}"


def _load_prompt(prompt_path: str | Path) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def _build_rule_based_projects(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "title": "Production-Ready RAG Support Assistant",
            "why_valuable": "RAG and vector retrieval appear repeatedly in AI Engineer hiring signals.",
            "skills_covered": ["python", "rag", "vector_databases", "prompt_engineering", "mlops_deployment"],
            "evidence_from_jds": [
                "Multiple JDs require RAG pipelines and vector databases.",
                "Deployment and API integration are common expectations.",
            ],
            "difficulty_level": "Intermediate",
            "portfolio_impact": "Shows full-stack AI engineering from retrieval to deployment.",
            "roadmap": [
                "Ingest domain docs and chunk content.",
                "Build retrieval + reranking pipeline.",
                "Add prompt guardrails and citations.",
                "Deploy with FastAPI + Docker and monitor quality.",
            ],
        },
        {
            "title": "LLM Evaluation and Safety Benchmark Suite",
            "why_valuable": "Evaluation, robustness, and factuality are strong market signals across engineering and research roles.",
            "skills_covered": ["model_evaluation", "llms", "python", "experiment_tracking"],
            "evidence_from_jds": [
                "JDs mention evaluation loops, benchmark scripts, and quality tracking.",
                "Research intern roles ask for factuality and robustness studies.",
            ],
            "difficulty_level": "Intermediate",
            "portfolio_impact": "Demonstrates measurable quality engineering for AI products.",
            "roadmap": [
                "Define task-specific evaluation metrics.",
                "Create benchmark dataset and test harness.",
                "Run model comparisons with error analysis.",
                "Publish dashboard and improvement report.",
            ],
        },
        {
            "title": "Domain LLM Fine-Tuning and Serving Pipeline",
            "why_valuable": "Fine-tuning and serving open-source models are directly requested in applied AI roles.",
            "skills_covered": ["fine_tuning", "transformers", "pytorch", "mlops_deployment"],
            "evidence_from_jds": [
                "Applied ML JD asks for fine-tuning and model serving.",
                "Hugging Face and transformer tooling are explicitly required.",
            ],
            "difficulty_level": "Advanced",
            "portfolio_impact": "Shows ownership from adaptation to production deployment.",
            "roadmap": [
                "Prepare and validate domain training data.",
                "Fine-tune using LoRA/QLoRA.",
                "Evaluate against baseline model.",
                "Serve model through API with monitoring.",
            ],
        },
        {
            "title": "Agentic Research Workflow Assistant",
            "why_valuable": "Agentic systems and tool-using AI workflows are increasing in job requirements.",
            "skills_covered": ["agentic_workflows", "llms", "python", "prompt_engineering"],
            "evidence_from_jds": [
                "JD responsibilities include building agentic workflows.",
                "Cross-tool reasoning and automation are highlighted.",
            ],
            "difficulty_level": "Intermediate",
            "portfolio_impact": "Demonstrates practical orchestration of multi-step AI agents.",
            "roadmap": [
                "Define tools and task planner design.",
                "Implement agent routing and tool calls.",
                "Add memory, fallback logic, and safeguards.",
                "Evaluate real-world tasks and document results.",
            ],
        },
        {
            "title": "Multimodal Paper Reproduction Mini-Lab",
            "why_valuable": "Research intern demand emphasizes paper implementation, ablations, and clear reporting.",
            "skills_covered": ["multimodal", "pytorch", "model_evaluation", "transformers"],
            "evidence_from_jds": [
                "Research role requires reproducing papers and running ablation studies.",
                "Benchmarking and technical presentation are repeated expectations.",
            ],
            "difficulty_level": "Advanced",
            "portfolio_impact": "Signals strong research execution and experiment discipline.",
            "roadmap": [
                "Select one recent multimodal paper.",
                "Reproduce baseline with open data.",
                "Run ablations and robustness tests.",
                "Publish technical report with findings.",
            ],
        },
    ]


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

    first_arr = text.find("[")
    last_arr = text.rfind("]")
    if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
        candidates.append(text[first_arr : last_arr + 1].strip())

    seen = set()
    unique_candidates: List[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    return unique_candidates


def _validate_project_list(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    projects = [item for item in value if isinstance(item, dict)]
    return projects if projects else []


def _infer_target_roles(project: Dict[str, Any], available_roles: List[str]) -> List[str]:
    combined = " ".join(
        [
            project.get("title", ""),
            project.get("why_valuable", ""),
            " ".join(project.get("evidence_from_jds", [])),
            " ".join(project.get("skills_covered", [])),
        ]
    ).lower()

    role_hits: List[str] = []
    for role in available_roles:
        role_lower = role.lower()
        if "research intern" in role_lower:
            research_signals = ("research", "ablation", "multimodal", "paper", "benchmark")
            if any(signal in combined for signal in research_signals):
                role_hits.append(role)
        elif "engineer" in role_lower:
            engineer_signals = ("deployment", "rag", "api", "pipeline", "production", "mlops")
            if any(signal in combined for signal in engineer_signals):
                role_hits.append(role)

    if role_hits:
        return role_hits
    return available_roles[:1] if available_roles else ["General"]


def _normalize_project(project: Dict[str, Any], available_roles: List[str]) -> Dict[str, Any]:
    normalized = {
        "title": str(project.get("title", "Untitled Project")),
        "why_valuable": str(project.get("why_valuable", "")),
        "skills_covered": [str(item) for item in project.get("skills_covered", []) if str(item).strip()],
        "evidence_from_jds": [str(item) for item in project.get("evidence_from_jds", []) if str(item).strip()],
        "difficulty_level": str(project.get("difficulty_level", "Intermediate")),
        "portfolio_impact": str(project.get("portfolio_impact", "")),
        "roadmap": [str(item) for item in project.get("roadmap", []) if str(item).strip()],
    }

    existing_roles = project.get("target_roles", [])
    if isinstance(existing_roles, list) and existing_roles:
        normalized["target_roles"] = [str(item) for item in existing_roles if str(item).strip()]
    else:
        normalized["target_roles"] = _infer_target_roles(normalized, available_roles)

    return normalized


def _normalize_projects(projects: List[Dict[str, Any]], available_roles: List[str]) -> List[Dict[str, Any]]:
    return [_normalize_project(project, available_roles) for project in projects]


def _try_parse_project_json(text: str) -> List[Dict[str, Any]]:
    if not text or text.startswith("[fallback]"):
        return []
    for candidate in _extract_json_candidates(text):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                if "projects" in parsed:
                    projects = _validate_project_list(parsed["projects"])
                    if projects:
                        return projects
                if "recommendations" in parsed:
                    projects = _validate_project_list(parsed["recommendations"])
                    if projects:
                        return projects
            if isinstance(parsed, list):
                projects = _validate_project_list(parsed)
                if projects:
                    return projects
        except Exception:
            continue
    return []


def run_market_project_recommender(
    market_report: Dict[str, Any],
    prompt_path: str | Path,
    output_dir: str | Path,
    model: str,
    host: str,
) -> Dict[str, Any]:
    available_roles = list(market_report.get("role_distribution", {}).keys())
    if not available_roles:
        available_roles = ["AI Engineer"]

    rule_based_projects = _build_rule_based_projects(market_report)
    rule_based_projects = _normalize_projects(rule_based_projects, available_roles)

    prompt_template = _load_prompt(prompt_path)
    prompt = prompt_template.format(
        analysis_json=json.dumps(market_report, indent=2),
        candidate_projects=json.dumps(rule_based_projects, indent=2),
    )

    llm_raw = _chat_with_ollama(prompt, model=model, host=host)
    llm_projects = _try_parse_project_json(llm_raw)
    llm_projects = _normalize_projects(llm_projects, available_roles) if llm_projects else []
    final_projects = llm_projects if llm_projects else rule_based_projects
    project_source = "llm" if llm_projects else "rule_based_fallback"

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_count": len(final_projects),
        "available_roles": available_roles,
        "projects": final_projects,
        "project_source": project_source,
        "ollama_raw_response": llm_raw,
    }

    out_base = Path(output_dir)
    out_base.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_base / f"project_recommendations_{timestamp}.json"
    md_path = out_base / f"project_recommendations_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# MarketFit-AI Project Recommendations",
        "",
        f"Generated: {payload['generated_at']}",
        f"Source: {project_source}",
        "",
    ]

    for idx, project in enumerate(final_projects, start=1):
        lines.append(f"## {idx}. {project.get('title', 'Untitled Project')}")
        lines.append(f"- Why valuable: {project.get('why_valuable', '')}")
        lines.append(f"- Skills covered: {', '.join(project.get('skills_covered', []))}")
        lines.append(f"- Difficulty: {project.get('difficulty_level', '')}")
        lines.append(f"- Portfolio impact: {project.get('portfolio_impact', '')}")
        lines.append("- Evidence from JDs:")
        for evidence in project.get("evidence_from_jds", []):
            lines.append(f"  - {evidence}")
        lines.append("- Suggested roadmap:")
        for step in project.get("roadmap", []):
            lines.append(f"  - {step}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload["output_files"] = {
        "project_recommendations_json": str(json_path),
        "project_recommendations_markdown": str(md_path),
    }
    return payload

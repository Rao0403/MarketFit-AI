from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


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


ROLE_THEME_PRIORITIES: Dict[str, List[str]] = {
    "AI Engineer": [
        "applied_deployment_and_mlops",
        "production_rag_systems",
        "agentic_ai_automation",
        "llm_evaluation_and_safety",
        "llm_customization_and_adaptation",
    ],
    "AI Research Intern": [
        "llm_evaluation_and_safety",
        "llm_customization_and_adaptation",
        "agentic_ai_automation",
        "production_rag_systems",
        "applied_deployment_and_mlops",
    ],
}

THEME_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "production_rag_systems": {
        "title": "Production RAG Knowledge Assistant",
        "problem_statement": "Build a reliable retrieval-augmented assistant that answers domain questions with grounded citations.",
        "market_relevance": "RAG and vector retrieval remain high-demand capabilities in AI Engineer job descriptions.",
        "skills_demonstrated": ["rag", "retrieval", "vector_databases", "prompt_engineering", "python"],
        "suggested_stack": ["Python", "FastAPI", "LangChain or LlamaIndex", "FAISS/Chroma", "Docker"],
        "difficulty_level": "Intermediate",
        "portfolio_impact": "Demonstrates end-to-end LLM system design from ingestion to production API.",
        "implementation_roadmap": [
            "Ingest and chunk domain documents with metadata strategy.",
            "Implement retrieval + reranking + citation formatting.",
            "Add quality checks for hallucination and unsupported claims.",
            "Deploy service with API endpoints and usage logging.",
        ],
    },
    "llm_evaluation_and_safety": {
        "title": "LLM Evaluation and Safety Harness",
        "problem_statement": "Create a repeatable evaluation harness to measure quality, factuality, and safety of LLM outputs.",
        "market_relevance": "Evaluation and reliability signals appear consistently across AI engineering and research hiring demand.",
        "skills_demonstrated": ["model_evaluation", "safety_guardrails", "llms", "python"],
        "suggested_stack": ["Python", "PyTest", "Pandas", "Weights & Biases", "Jupyter"],
        "difficulty_level": "Intermediate",
        "portfolio_impact": "Shows ability to make LLM systems measurable and production-trustworthy.",
        "implementation_roadmap": [
            "Define metrics for correctness, factuality, and robustness.",
            "Build benchmark dataset and evaluation scripts.",
            "Run comparative experiments across prompts/models.",
            "Publish failure analysis and mitigation recommendations.",
        ],
    },
    "agentic_ai_automation": {
        "title": "Agentic Workflow Automation Assistant",
        "problem_statement": "Develop a multi-step agent that plans tasks, calls tools, and returns verifiable outputs.",
        "market_relevance": "Agentic workflow and tool-using system requirements are increasingly visible in AI role expectations.",
        "skills_demonstrated": ["agentic_workflows", "tool_orchestration", "llms", "prompt_engineering"],
        "suggested_stack": ["Python", "LangChain/LangGraph", "FastAPI", "PostgreSQL", "Docker"],
        "difficulty_level": "Intermediate",
        "portfolio_impact": "Demonstrates practical orchestration for task automation beyond simple chatbots.",
        "implementation_roadmap": [
            "Define planner/executor architecture with tool contracts.",
            "Implement memory, retries, and error handling policy.",
            "Add audit logs with tool-call traceability.",
            "Evaluate on realistic workflow scenarios.",
        ],
    },
    "applied_deployment_and_mlops": {
        "title": "MLOps-Ready LLM Serving Pipeline",
        "problem_statement": "Ship an LLM-powered service with CI/CD, monitoring, and containerized deployment.",
        "market_relevance": "Deployment and MLOps capabilities are core expectations for applied AI engineering roles.",
        "skills_demonstrated": ["deployment", "mlops", "docker", "kubernetes", "github_actions"],
        "suggested_stack": ["Python", "FastAPI", "Docker", "Kubernetes", "GitHub Actions"],
        "difficulty_level": "Advanced",
        "portfolio_impact": "Shows readiness for real-world product deployment and operational ownership.",
        "implementation_roadmap": [
            "Containerize inference API and define health checks.",
            "Set up CI pipeline with tests and image publishing.",
            "Deploy to Kubernetes with autoscaling and logging.",
            "Track latency, errors, and model quality drift.",
        ],
    },
    "llm_customization_and_adaptation": {
        "title": "Domain LLM Adaptation with LoRA",
        "problem_statement": "Adapt an open LLM to a domain task and benchmark gains against a baseline model.",
        "market_relevance": "Fine-tuning and transformer adaptation appear in both applied and research-oriented JD trends.",
        "skills_demonstrated": ["fine_tuning", "transformers", "huggingface", "pytorch"],
        "suggested_stack": ["PyTorch", "Transformers", "PEFT/LoRA", "Weights & Biases", "FastAPI"],
        "difficulty_level": "Advanced",
        "portfolio_impact": "Signals model-level depth and experimentation rigor.",
        "implementation_roadmap": [
            "Prepare and validate task-specific training data.",
            "Run LoRA fine-tuning with reproducible configs.",
            "Benchmark against baseline with error analysis.",
            "Expose tuned model via inference API and report.",
        ],
    },
}


def _build_signal_index(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for source_key in ("skill_frequency", "tool_frequency"):
        source = report.get(source_key, {})
        for signal, payload in source.items():
            merged[signal] = payload
    return merged


def _extract_theme_scores(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    scores: Dict[str, Dict[str, Any]] = {}
    for row in report.get("project_worthy_themes", []):
        theme = str(row.get("theme", "")).strip()
        if not theme:
            continue
        scores[theme] = {
            "score": int(row.get("score", 0)),
            "evidence_signals": list(row.get("evidence_signals", [])),
        }
    return scores


def _compose_evidence(
    theme: str,
    theme_payload: Dict[str, Any],
    signal_index: Dict[str, Dict[str, Any]],
    role: str,
) -> List[str]:
    evidence: List[str] = []
    score = theme_payload.get("score", 0)
    evidence.append(f"Theme '{theme}' scored {score} in project_worthy_themes for current market demand.")

    for signal in theme_payload.get("evidence_signals", [])[:4]:
        stats = signal_index.get(signal, {})
        docs = stats.get("documents_with_signal", 0)
        mentions = stats.get("total_mentions", 0)
        evidence.append(f"Signal '{signal}' appears in {docs} JDs with {mentions} total mentions.")

    evidence.append(f"Recommendation is tailored for target role: {role}.")
    return evidence


def _select_themes_for_role(role: str, theme_scores: Dict[str, Dict[str, Any]], max_projects: int = 5) -> List[str]:
    priorities = ROLE_THEME_PRIORITIES.get(role, [])

    ranked_by_score = sorted(
        list(theme_scores.keys()),
        key=lambda theme: theme_scores[theme].get("score", 0),
        reverse=True,
    )

    selected: List[str] = []
    for theme in priorities:
        if theme in theme_scores and theme not in selected:
            selected.append(theme)
        if len(selected) >= max_projects:
            return selected

    for theme in ranked_by_score:
        if theme in THEME_BLUEPRINTS and theme not in selected:
            selected.append(theme)
        if len(selected) >= max_projects:
            break

    return selected


def _build_rule_based_projects_by_role(report: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    available_roles = list(report.get("role_distribution", {}).keys()) or ["AI Engineer"]
    theme_scores = _extract_theme_scores(report)
    signal_index = _build_signal_index(report)

    by_role: Dict[str, List[Dict[str, Any]]] = {}
    for role in available_roles:
        selected_themes = _select_themes_for_role(role, theme_scores, max_projects=5)
        role_projects: List[Dict[str, Any]] = []

        for theme in selected_themes:
            blueprint = THEME_BLUEPRINTS.get(theme)
            if not blueprint:
                continue

            theme_payload = theme_scores.get(theme, {"score": 0, "evidence_signals": []})
            evidence = _compose_evidence(theme, theme_payload, signal_index, role)

            project = {
                **blueprint,
                "target_role": role,
                "target_roles": [role],
                "evidence_from_jd_trends": evidence,
                "source_theme": theme,
            }
            role_projects.append(project)

        # Ensure minimum of 4 projects per role by filling from global blueprint order.
        if len(role_projects) < 4:
            for theme, blueprint in THEME_BLUEPRINTS.items():
                if any(item.get("source_theme") == theme for item in role_projects):
                    continue
                evidence = _compose_evidence(theme, theme_scores.get(theme, {"score": 0, "evidence_signals": []}), signal_index, role)
                role_projects.append(
                    {
                        **blueprint,
                        "target_role": role,
                        "target_roles": [role],
                        "evidence_from_jd_trends": evidence,
                        "source_theme": theme,
                    }
                )
                if len(role_projects) >= 4:
                    break

        by_role[role] = role_projects[:8]

    return by_role


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


def _normalize_project(project: Dict[str, Any], role: str) -> Dict[str, Any]:
    title = str(project.get("title", "Untitled Project")).strip() or "Untitled Project"
    roadmap = project.get("implementation_roadmap") or project.get("roadmap") or []

    normalized = {
        "title": title,
        "problem_statement": str(project.get("problem_statement", "")).strip(),
        "market_relevance": str(project.get("market_relevance", "")).strip(),
        "skills_demonstrated": [str(item).strip() for item in project.get("skills_demonstrated", []) if str(item).strip()],
        "suggested_stack": [str(item).strip() for item in project.get("suggested_stack", []) if str(item).strip()],
        "difficulty_level": str(project.get("difficulty_level", "Intermediate")).strip() or "Intermediate",
        "portfolio_impact": str(project.get("portfolio_impact", "")).strip(),
        "implementation_roadmap": [str(item).strip() for item in roadmap if str(item).strip()],
        "evidence_from_jd_trends": [str(item).strip() for item in project.get("evidence_from_jd_trends", []) if str(item).strip()],
        "target_role": str(project.get("target_role", role)).strip() or role,
        "target_roles": [str(item).strip() for item in project.get("target_roles", [role]) if str(item).strip()],
    }

    # Backward-compatible alias fields for existing consumers.
    normalized["skills_covered"] = normalized["skills_demonstrated"]
    normalized["roadmap"] = normalized["implementation_roadmap"]
    normalized["evidence_from_jds"] = normalized["evidence_from_jd_trends"]

    return normalized


def _parse_llm_projects_by_role(text: str, available_roles: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    if not text or text.startswith("[fallback]"):
        return {}

    for candidate in _extract_json_candidates(text):
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue

        role_map: Dict[str, List[Dict[str, Any]]] = {}
        if isinstance(parsed, dict):
            if isinstance(parsed.get("recommendations_by_role"), list):
                role_blocks = parsed["recommendations_by_role"]
            elif isinstance(parsed.get("roles"), list):
                role_blocks = parsed["roles"]
            else:
                role_blocks = []

            for block in role_blocks:
                if not isinstance(block, dict):
                    continue
                role = str(block.get("target_role", "")).strip()
                if not role:
                    continue
                projects = block.get("projects", [])
                if isinstance(projects, list):
                    role_map[role] = [project for project in projects if isinstance(project, dict)]

            # Optional flat fallback: { "projects": [...] }
            if not role_map and isinstance(parsed.get("projects"), list):
                role = available_roles[0] if available_roles else "AI Engineer"
                role_map[role] = [project for project in parsed["projects"] if isinstance(project, dict)]

        if role_map:
            return role_map

    return {}


def _normalize_role_payload(projects_by_role: Dict[str, List[Dict[str, Any]]], available_roles: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    normalized: Dict[str, List[Dict[str, Any]]] = {}
    for role in available_roles:
        raw_projects = projects_by_role.get(role, [])
        normalized[role] = [_normalize_project(project, role) for project in raw_projects][:8]

    return normalized


def _flatten_projects(projects_by_role: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for role, projects in projects_by_role.items():
        for project in projects:
            item = dict(project)
            item["target_role"] = role
            if "target_roles" not in item or not item["target_roles"]:
                item["target_roles"] = [role]
            flattened.append(item)
    return flattened


def _build_role_blocks(projects_by_role: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for role, projects in projects_by_role.items():
        blocks.append(
            {
                "target_role": role,
                "project_count": len(projects),
                "projects": projects,
            }
        )
    return blocks


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

    rule_based_projects_by_role = _build_rule_based_projects_by_role(market_report)

    prompt_template = _load_prompt(prompt_path)
    prompt = prompt_template.format(
        analysis_json=json.dumps(market_report, indent=2),
        candidate_projects=json.dumps(_build_role_blocks(rule_based_projects_by_role), indent=2),
    )

    llm_raw = _chat_with_ollama(prompt, model=model, host=host)
    llm_projects_by_role = _parse_llm_projects_by_role(llm_raw, available_roles)

    final_projects_by_role = (
        _normalize_role_payload(llm_projects_by_role, available_roles)
        if llm_projects_by_role
        else _normalize_role_payload(rule_based_projects_by_role, available_roles)
    )

    # Keep 4-8 projects per role and enforce minimum via fallback templates.
    for role in available_roles:
        current = final_projects_by_role.get(role, [])
        if len(current) < 4:
            fill = _normalize_role_payload(rule_based_projects_by_role, available_roles).get(role, [])
            used_titles = {item.get("title", "") for item in current}
            for project in fill:
                if project.get("title", "") in used_titles:
                    continue
                current.append(project)
                used_titles.add(project.get("title", ""))
                if len(current) >= 4:
                    break
        final_projects_by_role[role] = current[:8]

    final_projects = _flatten_projects(final_projects_by_role)
    project_source = "llm" if llm_projects_by_role else "rule_based_fallback"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "available_roles": available_roles,
        "recommendations_by_role": _build_role_blocks(final_projects_by_role),
        "projects": final_projects,
        "project_count": len(final_projects),
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

    for role_block in payload["recommendations_by_role"]:
        role = role_block["target_role"]
        lines.append(f"## Target Role: {role}")
        lines.append(f"Project Count: {role_block['project_count']}")
        lines.append("")

        for idx, project in enumerate(role_block["projects"], start=1):
            lines.append(f"### {idx}. {project.get('title', 'Untitled Project')}")
            lines.append(f"- Problem statement: {project.get('problem_statement', '')}")
            lines.append(f"- Market relevance: {project.get('market_relevance', '')}")
            lines.append(f"- Skills demonstrated: {', '.join(project.get('skills_demonstrated', []))}")
            lines.append(f"- Suggested stack: {', '.join(project.get('suggested_stack', []))}")
            lines.append(f"- Difficulty: {project.get('difficulty_level', '')}")
            lines.append(f"- Portfolio impact: {project.get('portfolio_impact', '')}")
            lines.append("- Evidence from JD trends:")
            for evidence in project.get("evidence_from_jd_trends", []):
                lines.append(f"  - {evidence}")
            lines.append("- Implementation roadmap:")
            for step in project.get("implementation_roadmap", []):
                lines.append(f"  - {step}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload["output_files"] = {
        "project_recommendations_json": str(json_path),
        "project_recommendations_markdown": str(md_path),
    }
    return payload

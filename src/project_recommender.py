from __future__ import annotations

import json
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
    top_skill_names = [row["skill"] for row in report.get("top_skills", [])]

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


def _try_parse_project_json(text: str) -> List[Dict[str, Any]]:
    if not text or text.startswith("[fallback]"):
        return []
    try:
        parsed = json.loads(text)
        projects = parsed.get("projects", [])
        if isinstance(projects, list):
            return projects
        return []
    except Exception:
        return []


def run_market_project_recommender(
    market_report: Dict[str, Any],
    prompt_path: str | Path,
    output_dir: str | Path,
    model: str,
    host: str,
) -> Dict[str, Any]:
    rule_based_projects = _build_rule_based_projects(market_report)

    prompt_template = _load_prompt(prompt_path)
    prompt = prompt_template.format(
        analysis_json=json.dumps(market_report, indent=2),
        candidate_projects=json.dumps(rule_based_projects, indent=2),
    )

    llm_raw = _chat_with_ollama(prompt, model=model, host=host)
    llm_projects = _try_parse_project_json(llm_raw)
    final_projects = llm_projects if llm_projects else rule_based_projects

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_count": len(final_projects),
        "projects": final_projects,
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

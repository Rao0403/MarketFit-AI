from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency fallback
    def load_dotenv() -> bool:
        return False

from .market_analyzer import run_jd_intelligence_engine
from .project_recommender import run_market_project_recommender


def main() -> None:
    load_dotenv()

    project_root = Path(__file__).resolve().parent.parent
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    market_report = run_jd_intelligence_engine(
        raw_jd_dir=project_root / "data" / "raw_jds",
        prompt_path=project_root / "prompts" / "jd_analysis_prompt.md",
        output_dir=project_root / "outputs" / "market_reports",
        model=model,
        host=host,
    )

    recommendations = run_market_project_recommender(
        market_report=market_report,
        prompt_path=project_root / "prompts" / "market_project_prompt.md",
        output_dir=project_root / "outputs" / "project_recommendations",
        model=model,
        host=host,
    )

    print("Market report files:")
    print(f"- {market_report['output_files']['market_report_json']}")
    print(f"- {market_report['output_files']['market_report_markdown']}")
    print("Project recommendation files:")
    print(f"- {recommendations['output_files']['project_recommendations_json']}")
    print(f"- {recommendations['output_files']['project_recommendations_markdown']}")


if __name__ == "__main__":
    main()

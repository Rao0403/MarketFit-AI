# MarketFit-AI (v1)

MarketFit-AI is a local-first, Ollama-based pipeline that reads job descriptions and turns them into market-aligned project recommendations.

## v1 Features

1. JD Intelligence Engine
- Reads synthetic or uploaded JDs from `data/raw_jds/`
- Extracts top skills, technology signals, repeated responsibilities, and project-worthy themes
- Uses Ollama to generate a concise market narrative
- Writes reports into `outputs/market_reports/`

2. Market-Based Project Recommender
- Uses only JD market analysis (no resume needed)
- Recommends portfolio projects based on demand signals
- Includes value proposition, skills covered, JD evidence, difficulty, portfolio impact, roadmap, and target roles
- Writes recommendations into `outputs/project_recommendations/`

## Project Structure

```text
MarketFit-AI/
|- README.md
|- requirements.txt
|- .env.example
|- .gitignore
|- data/
|  |- raw_jds/
|  |- processed/
|  `- resumes/
|- notebooks/
|  |- 01_jd_analysis.ipynb
|  `- 02_market_project_recommender.ipynb
|- src/
|  |- jd_parser.py
|  |- skill_extractor.py
|  |- market_analyzer.py
|  |- project_recommender.py
|  `- main.py
|- prompts/
|  |- jd_analysis_prompt.md
|  `- market_project_prompt.md
|- scripts/
|  `- collect_jds.py
|- frontend/
|  |- app/
|  |- components/
|  `- lib/
`- outputs/
   |- market_reports/
   `- project_recommendations/
```

## Quickstart

1. Create and activate a virtual environment.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Start Ollama and pull a model (example):
```bash
ollama pull llama3.2:1b
```
4. Configure environment:
```bash
cp .env.example .env
```
5. Run pipeline:
```bash
python -m src.main
```

## Collect Real JDs (API-based)

Collect normalized JD files into `data/raw_jds/`.

```bash
python scripts/collect_jds.py --sources remotive --queries "AI Engineer" "AI Research Intern" --limit-per-query 5
```

Optional additional sources:
- Adzuna: set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`
- USAJOBS: set `USAJOBS_API_KEY` and `USAJOBS_USER_AGENT_EMAIL`

Example with multiple sources:

```bash
python scripts/collect_jds.py --sources remotive adzuna usajobs --limit-per-query 4
```

## Frontend Dashboard (Next.js)

The dashboard reads the latest recommendation JSON from `outputs/project_recommendations/` and supports role filtering.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

API endpoint:
- `GET /api/recommendations`
- `GET /api/recommendations?role=AI%20Engineer`

## Outputs

- Market analysis JSON + Markdown in `outputs/market_reports/`
- Project recommendations JSON + Markdown in `outputs/project_recommendations/`
- Recommendation metadata includes `project_source` and per-project `target_roles`

If Ollama is unavailable, the pipeline still produces rule-based fallback outputs so local testing does not block.

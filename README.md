# MarketFit-AI

MarketFit-AI is a JD-driven career intelligence and project recommendation system for Computer Science and AI/ML students.

The project analyzes job descriptions (JDs) to understand market demand, extract trending skills, and recommend high-value portfolio projects. It also supports personalized analysis by comparing a user's resume or profile against current job-market demand and suggesting ways to improve their market fit.

---

## Objective

MarketFit-AI is built to answer two key questions:

1. What skills, tools, and project themes are currently in demand for CS and AI/ML roles?
2. How well does a student’s profile match that demand, and what should they improve next?

The system uses **job descriptions as the primary source of truth**.

---

## Core Idea

Job descriptions contain direct signals about what the market values.

MarketFit-AI extracts:

* Required skills
* Tools and frameworks
* Role expectations
* Responsibilities
* Preferred qualifications
* Emerging trends
* Project-relevant themes

These insights power two main features:

---

## Features

### 1. JD Intelligence Engine

The backbone of the system.

It analyzes a dataset of job descriptions and identifies:

* Top skills
* Trending technologies
* Common role expectations
* Skill frequency
* Repeated responsibilities
* Project-worthy themes

**Example output:**

```
For GenAI Intern roles:
- Python appears in 72% of JDs
- LLMs appear in 58% of JDs
- RAG appears in 46% of JDs
- Vector databases appear in 39% of JDs
- Evaluation appears in 34% of JDs
```

---

### 2. Market-Based Project Recommender

No resume required.

This feature recommends projects purely based on job-market demand.

It answers:

> What projects should someone build to become valuable for this role?

**Example projects:**

* RAG Evaluation Benchmark
* Agentic Research Assistant
* Fine-Tuning Small LLM for Domain QA
* Vector Search Recommendation System
* End-to-End ML Deployment Pipeline

Each recommendation includes:

* Why it is valuable
* Skills covered
* Evidence from JDs
* Difficulty level
* Portfolio impact
* Suggested roadmap

---

### 3. Personalized Market Fit Analyzer

This feature compares a user's resume/profile with job-market demand.

It answers:

> How in demand am I for this target role?

**Outputs:**

* Market fit score
* Matching skills
* Missing skills
* Weak profile signals
* Project recommendations
* Certification suggestions
* Resume improvement advice
* Learning roadmap

**Example output:**

```
Target Role: GenAI Intern

Market Fit Score: 68/100

Strong signals:
- Python
- PyTorch
- Transformers
- LLM experimentation

Weak or missing signals:
- Vector databases
- Deployment
- Docker
- LLM evaluation
- MLOps basics

Recommended improvements:
1. Build a RAG evaluation project
2. Add FastAPI + Docker deployment
3. Improve resume bullets with measurable results
4. Learn vector databases and evaluation
```

---

## Initial Scope

Focus areas for MVP:

* CS students
* AI/ML students
* Internship and entry-level roles

Target roles:

* ML Engineer Intern
* Data Science Intern
* GenAI Intern
* AI Research Intern
* Software Engineer Intern

---

## MVP Plan

### Phase 1: JD Analysis

* Upload job descriptions
* Clean and preprocess text
* Extract skills, tools, and responsibilities
* Generate market demand summary

### Phase 2: Project Recommendations

* Identify high-value project themes from JDs
* Generate project ideas
* Rank projects by relevance and impact

### Phase 3: Personalized Market Fit

* Parse resume/profile
* Extract skills and experience
* Compare against JD demand
* Generate improvement report

---

## Repository Structure

```
MarketFit-AI/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw_jds/
│   ├── processed/
│   └── resumes/
│
├── notebooks/
│   ├── 01_jd_analysis.ipynb
│   ├── 02_market_project_recommender.ipynb
│   └── 03_personalized_market_fit.ipynb
│
├── src/
│   ├── jd_parser.py
│   ├── skill_extractor.py
│   ├── market_analyzer.py
│   ├── resume_analyzer.py
│   ├── project_recommender.py
│   └── scoring.py
│
├── prompts/
│   ├── jd_analysis_prompt.md
│   ├── resume_analysis_prompt.md
│   ├── market_project_prompt.md
│   └── personalized_recommendation_prompt.md
│
└── outputs/
    ├── market_reports/
    ├── project_recommendations/
    └── personal_reports/
```

---

## Tech Stack

**Initial stack:**

* Python
* Pandas
* Jupyter Notebooks
* LLM APIs (OpenAI or local models)
* JSON / CSV outputs

**Future additions:**

* Streamlit UI
* Vector database
* Web scraping for JDs
* Dashboard visualizations
* Agent orchestration

---

## Current Status

Planning and initial repository setup.

---

## Future Improvements

* Live JD collection and updates
* Role-wise demand dashboards
* Project difficulty calibration
* Resume bullet rewriting
* Certification recommendations
* Trend tracking over time
* Location-specific analysis
* Company-type-specific insights

---

## License

MIT License

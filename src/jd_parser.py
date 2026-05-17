from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class JobDescription:
    file_name: str
    title: str
    role: str
    role_tags: List[str]
    content: str


ROLE_KEYWORDS: Dict[str, List[str]] = {
    "AI Engineer": [
        "ai engineer",
        "ml engineer",
        "machine learning engineer",
        "applied ai",
    ],
    "AI Research Intern": [
        "ai research intern",
        "research intern",
        "research scientist intern",
    ],
    "Data Scientist": [
        "data scientist",
        "applied scientist",
    ],
    "MLOps Engineer": [
        "mlops",
        "machine learning operations",
        "platform engineer",
    ],
}


def _infer_role_tags(title: str, text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    header_scope = " ".join(lines[:4]).lower()
    title_scope = title.lower()
    tags: List[str] = []
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in title_scope for keyword in keywords):
            tags.append(role)
            continue
        if any(keyword in header_scope for keyword in keywords):
            tags.append(role)
    return tags


def _infer_primary_role(text: str, role_tags: List[str]) -> str:
    if role_tags:
        return role_tags[0]
    lower = text.lower()
    if "research" in lower and "intern" in lower:
        return "AI Research Intern"
    return "AI Engineer"


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        line = line.strip().strip("#")
        if line:
            return line
    return fallback


def load_job_descriptions(raw_jd_dir: str | Path) -> List[JobDescription]:
    base = Path(raw_jd_dir)
    if not base.exists():
        raise FileNotFoundError(f"JD directory not found: {base}")

    jd_files = sorted(
        [*base.glob("*.txt"), *base.glob("*.md")],
        key=lambda p: p.name.lower(),
    )

    jds: List[JobDescription] = []
    for path in jd_files:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        title = _extract_title(content, path.stem)
        role_tags = _infer_role_tags(title, content)
        role = _infer_primary_role(content, role_tags)
        jds.append(
            JobDescription(
                file_name=path.name,
                title=title,
                role=role,
                role_tags=role_tags,
                content=content,
            )
        )

    if not jds:
        raise ValueError(f"No JD files found in {base}")

    return jds


def jd_snippets(jds: List[JobDescription], max_chars: int = 700) -> str:
    snippets = []
    for jd in jds:
        clipped = jd.content[:max_chars].replace("\n", " ")
        snippets.append(f"[{jd.file_name}] {clipped}")
    return "\n".join(snippets)

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class JobDescription:
    file_name: str
    title: str
    role: str
    content: str


def _infer_role(text: str) -> str:
    lower = text.lower()
    if "research intern" in lower:
        return "AI Research Intern"
    if "ai engineer" in lower:
        return "AI Engineer"
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
        role = _infer_role(content)
        jds.append(
            JobDescription(
                file_name=path.name,
                title=title,
                role=role,
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

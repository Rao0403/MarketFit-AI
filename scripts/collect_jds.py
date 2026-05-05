from __future__ import annotations

import argparse
import html
import json
import os
import re
import textwrap
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> bool:
        return False


DEFAULT_QUERIES = [
    "AI Engineer",
    "Machine Learning Engineer",
    "AI Research Intern",
]


@dataclass
class JDRecord:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    job_type: str = ""
    salary: str = ""
    posted_at: str = ""


def _clean_text(value: str) -> str:
    no_html = re.sub(r"<[^>]+>", " ", value or "")
    unescaped = html.unescape(no_html)
    squashed = re.sub(r"\s+", " ", unescaped).strip()
    return squashed


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value[:90] or "job_description"


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    merged_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MarketFit-AI/1.0; +https://example.local)",
        "Accept": "application/json",
    }
    if headers:
        merged_headers.update(headers)
    request = urllib.request.Request(url, headers=merged_headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def _fetch_remotive(queries: List[str], limit_per_query: int) -> List[JDRecord]:
    results: List[JDRecord] = []
    for query in queries:
        params = urllib.parse.urlencode({"search": query, "limit": str(limit_per_query)})
        url = f"https://remotive.com/api/remote-jobs?{params}"
        try:
            payload = _http_get_json(url)
        except Exception as exc:
            print(f"[remotive] Request failed for query '{query}': {exc}")
            continue
        for job in payload.get("jobs", [])[:limit_per_query]:
            results.append(
                JDRecord(
                    source="remotive",
                    external_id=str(job.get("id", "")),
                    title=str(job.get("title", "")),
                    company=str(job.get("company_name", "")),
                    location=str(job.get("candidate_required_location", "Remote")),
                    url=str(job.get("url", "")),
                    description=_clean_text(str(job.get("description", ""))),
                    job_type=str(job.get("job_type", "")),
                    salary=str(job.get("salary", "")),
                    posted_at=str(job.get("publication_date", "")),
                )
            )
    return results


def _fetch_adzuna(queries: List[str], limit_per_query: int) -> List[JDRecord]:
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")
    if not app_id or not app_key:
        print("[adzuna] Skipping: ADZUNA_APP_ID / ADZUNA_APP_KEY not set.")
        return []

    country = os.getenv("ADZUNA_COUNTRY", "us")
    results: List[JDRecord] = []
    per_page = min(limit_per_query, 20)
    pages = max(1, (limit_per_query + per_page - 1) // per_page)

    for query in queries:
        for page_idx in range(1, pages + 1):
            params = urllib.parse.urlencode(
                {
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": query,
                    "results_per_page": str(per_page),
                }
            )
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page_idx}?{params}"
            try:
                payload = _http_get_json(url)
            except Exception as exc:
                print(f"[adzuna] Request failed for query '{query}': {exc}")
                continue

            for job in payload.get("results", []):
                company = (job.get("company") or {}).get("display_name", "")
                location = (job.get("location") or {}).get("display_name", "")
                results.append(
                    JDRecord(
                        source="adzuna",
                        external_id=str(job.get("id", "")),
                        title=str(job.get("title", "")),
                        company=str(company),
                        location=str(location),
                        url=str(job.get("redirect_url", "")),
                        description=_clean_text(str(job.get("description", ""))),
                        job_type=str(job.get("contract_time", "")),
                        salary=f"{job.get('salary_min', '')}-{job.get('salary_max', '')}",
                        posted_at=str(job.get("created", "")),
                    )
                )

    return results[: len(queries) * limit_per_query]


def _fetch_usajobs(queries: List[str], limit_per_query: int) -> List[JDRecord]:
    api_key = os.getenv("USAJOBS_API_KEY", "")
    user_email = os.getenv("USAJOBS_USER_AGENT_EMAIL", "")
    if not api_key or not user_email:
        print("[usajobs] Skipping: USAJOBS_API_KEY / USAJOBS_USER_AGENT_EMAIL not set.")
        return []

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": user_email,
        "Authorization-Key": api_key,
    }

    results: List[JDRecord] = []
    per_page = min(limit_per_query, 25)
    for query in queries:
        params = urllib.parse.urlencode(
            {
                "Keyword": query,
                "ResultsPerPage": str(per_page),
                "Fields": "Full",
            }
        )
        url = f"https://data.usajobs.gov/api/Search?{params}"
        try:
            payload = _http_get_json(url, headers=headers)
        except Exception as exc:
            print(f"[usajobs] Request failed for query '{query}': {exc}")
            continue

        items = payload.get("SearchResult", {}).get("SearchResultItems", [])
        for item in items:
            descriptor = item.get("MatchedObjectDescriptor", {})
            details = descriptor.get("UserArea", {}).get("Details", {})
            summary_bits = [
                details.get("JobSummary", ""),
                details.get("MajorDuties", ""),
                details.get("Requirements", ""),
                details.get("Evaluations", ""),
            ]
            summary = _clean_text(" ".join(bit for bit in summary_bits if bit))
            results.append(
                JDRecord(
                    source="usajobs",
                    external_id=str(descriptor.get("PositionID", "")),
                    title=str(descriptor.get("PositionTitle", "")),
                    company=str(descriptor.get("OrganizationName", "")),
                    location=str(descriptor.get("PositionLocationDisplay", "")),
                    url=str(descriptor.get("PositionURI", "")),
                    description=summary,
                    job_type=", ".join(
                        item_.get("Name", "")
                        for item_ in descriptor.get("PositionSchedule", [])
                        if item_.get("Name")
                    ),
                    posted_at=str(descriptor.get("PublicationStartDate", "")),
                )
            )

    return results[: len(queries) * limit_per_query]


def _render_jd_text(record: JDRecord) -> str:
    description = textwrap.fill(record.description, width=100)
    return (
        f"{record.title}\n"
        f"Source: {record.source}\n"
        f"Company: {record.company or 'N/A'}\n"
        f"Location: {record.location or 'N/A'}\n"
        f"Job Type: {record.job_type or 'N/A'}\n"
        f"Salary: {record.salary or 'N/A'}\n"
        f"Posted At: {record.posted_at or 'N/A'}\n"
        f"Original URL: {record.url or 'N/A'}\n\n"
        f"Job Description:\n{description}\n"
    )


def _dedupe_records(records: Iterable[JDRecord]) -> List[JDRecord]:
    unique: Dict[str, JDRecord] = {}
    for rec in records:
        key = f"{rec.title.lower()}::{rec.company.lower()}::{rec.source}::{rec.external_id}"
        if key not in unique:
            unique[key] = rec
    return list(unique.values())


def _write_records(records: List[JDRecord], output_dir: Path, overwrite: bool) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    written = 0
    for rec in records:
        role_slug = _slugify(rec.title)[:55]
        file_name = f"{stamp}_{rec.source}_{role_slug}_{_slugify(rec.external_id)[:20]}.txt"
        path = output_dir / file_name
        if path.exists() and not overwrite:
            continue
        path.write_text(_render_jd_text(rec), encoding="utf-8")
        written += 1
    return written


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Collect job descriptions from public job APIs.")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["remotive"],
        choices=["remotive", "adzuna", "usajobs"],
        help="Sources to fetch from.",
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        default=DEFAULT_QUERIES,
        help="Queries to search, e.g. --queries \"AI Engineer\" \"AI Research Intern\"",
    )
    parser.add_argument("--limit-per-query", type=int, default=5, help="Max results per source/query.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite files if names collide.")
    parser.add_argument(
        "--output-dir",
        default="data/raw_jds",
        help="Directory where normalized JD text files are stored.",
    )
    args = parser.parse_args()

    all_records: List[JDRecord] = []
    if "remotive" in args.sources:
        all_records.extend(_fetch_remotive(args.queries, args.limit_per_query))
    if "adzuna" in args.sources:
        all_records.extend(_fetch_adzuna(args.queries, args.limit_per_query))
    if "usajobs" in args.sources:
        all_records.extend(_fetch_usajobs(args.queries, args.limit_per_query))

    deduped = _dedupe_records(all_records)
    written = _write_records(deduped, Path(args.output_dir), overwrite=args.overwrite)
    print(f"Fetched: {len(all_records)} | Deduped: {len(deduped)} | Written: {written}")


if __name__ == "__main__":
    main()

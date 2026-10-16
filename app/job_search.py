import json
from typing import List, Dict, Tuple

from app.config import (
    MOCK_JOBS_PATH,
    ADZUNA_APP_ID, ADZUNA_APP_KEY,
    INFOJOBS_CLIENT_ID, INFOJOBS_CLIENT_SECRET,
)
from app.apis.adzuna import search_adzuna
from app.apis.infojobs import search_infojobs

# Jobs must contain at least one of these terms to pass the domain filter.
_DOMAIN_TERMS = [
    "data scien", "data analy", "data engineer", "machine learning",
    "deep learning", "artificial intelligence", "nlp", "computer vision",
    "big data", "business intelligence", "bi analyst", "analytics engineer",
    "ciencia de datos", "analítica", "ml engineer", "ai engineer",
    "data architect", "data warehouse", "etl", "scientist", "analytics",
    "data platform", "data management", "data governance",
]

# Default query used when the user leaves the position field empty.
_DEFAULT_QUERY = "data scientist data analyst machine learning"


def _is_data_related(job: dict) -> bool:
    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    return any(term in text for term in _DOMAIN_TERMS)


def _load_mock_jobs() -> List[Dict]:
    with open(MOCK_JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_jobs(
    position: str = "",
    location: str = "",
    include_remote: bool = True,
    min_exp: int = 0,
    max_exp: int = 20,
) -> Tuple[List[Dict], List[str]]:
    query = position.strip() or _DEFAULT_QUERY
    results: List[Dict] = []
    errors: List[str] = []

    using_real_apis = False

    if ADZUNA_APP_ID and ADZUNA_APP_KEY:
        using_real_apis = True
        try:
            results.extend(search_adzuna(query=query, location=location,
                                         app_id=ADZUNA_APP_ID, app_key=ADZUNA_APP_KEY))
        except Exception as exc:
            errors.append(f"Adzuna: {exc}")

    if INFOJOBS_CLIENT_ID and INFOJOBS_CLIENT_SECRET:
        using_real_apis = True
        try:
            results.extend(search_infojobs(query=query, location=location,
                                           client_id=INFOJOBS_CLIENT_ID,
                                           client_secret=INFOJOBS_CLIENT_SECRET))
        except Exception as exc:
            errors.append(f"InfoJobs: {exc}")

    if not using_real_apis:
        results = _load_mock_jobs()

    # ── Domain filter ──────────────────────────────────────────────────────────
    results = [j for j in results if _is_data_related(j)]

    # ── Remote / location filter ───────────────────────────────────────────────
    loc = location.strip().lower()
    filtered = []
    for job in results:
        job_loc = job.get("location", "").lower().strip()
        truly_remote = job_loc == "remote"

        if truly_remote:
            if include_remote:
                filtered.append(job)
        else:
            if loc and loc not in job_loc:
                continue
            filtered.append(job)
    results = filtered

    # ── Experience filter (mock data has explicit min/max; API data defaults 0-20) ─
    results = [
        j for j in results
        if j.get("experience_max", 20) >= min_exp and j.get("experience_min", 0) <= max_exp
    ]

    return results, errors

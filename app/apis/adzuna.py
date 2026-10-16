import requests
from typing import List, Dict

_BASE = "https://api.adzuna.com/v1/api/jobs/es/search"


def search_adzuna(
    query: str,
    location: str = "",
    app_id: str = "",
    app_key: str = "",
    results_per_page: int = 20,
) -> List[Dict]:
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    resp = requests.get(f"{_BASE}/1", params=params, timeout=10)
    resp.raise_for_status()

    jobs = []
    for item in resp.json().get("results", []):
        sal_min = item.get("salary_min") or 0
        sal_max = item.get("salary_max") or 0
        salary = f"{int(sal_min):,} – {int(sal_max):,} €" if sal_min and sal_max else "No especificado"

        loc_name = item.get("location", {}).get("display_name", "")
        jobs.append({
            "id": f"adzuna_{item['id']}",
            "title": item.get("title", ""),
            "company": item.get("company", {}).get("display_name", ""),
            "location": loc_name,
            "remote": False,
            "description": item.get("description", "")[:600],
            "required_skills": [],
            "nice_to_have": [],
            "experience_min": 0,
            "experience_max": 20,
            "salary_range": salary,
            "contract_type": item.get("contract_type") or "Full-time",
            "posted_date": (item.get("created") or "")[:10],
            "url": item.get("redirect_url", ""),
            "source": "Adzuna",
        })

    return jobs

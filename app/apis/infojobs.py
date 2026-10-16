import base64
import requests
from typing import List, Dict

_BASE = "https://api.infojobs.net/api/9/offer"


def search_infojobs(
    query: str,
    location: str = "",
    client_id: str = "",
    client_secret: str = "",
    max_results: int = 20,
) -> List[Dict]:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    params: dict = {"q": query, "maxResults": max_results, "sinceDate": "ANY"}
    if location:
        params["province"] = location

    resp = requests.get(_BASE, headers=headers, params=params, timeout=10)
    resp.raise_for_status()

    jobs = []
    for item in resp.json().get("items", []):
        sal_min = (item.get("salaryMin") or {}).get("value") or 0
        sal_max = (item.get("salaryMax") or {}).get("value") or 0
        salary = f"{sal_min:,} – {sal_max:,} €" if sal_min and sal_max else "No especificado"

        telework = (item.get("teleworking") or {}).get("value", "")
        truly_remote = "completo" in telework.lower() or "100" in telework
        city = (item.get("province") or {}).get("value", "")

        jobs.append({
            "id": f"infojobs_{item.get('id', '')}",
            "title": item.get("title", ""),
            "company": (item.get("author") or {}).get("name", ""),
            "location": "Remote" if truly_remote else city,
            "remote": bool(telework),
            "description": item.get("description", "")[:600],
            "required_skills": [],
            "nice_to_have": [],
            "experience_min": 0,
            "experience_max": 20,
            "salary_range": salary,
            "contract_type": (item.get("contractType") or {}).get("value", "Full-time"),
            "posted_date": (item.get("published") or "")[:10],
            "url": item.get("link", ""),
            "source": "InfoJobs",
        })

    return jobs

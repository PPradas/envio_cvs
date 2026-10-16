import json
import os
import re
from pathlib import Path
from typing import Optional

from app.config import PROFILES_DIR

_SELECTED_FILE = os.path.join(PROFILES_DIR, ".selected")


def _slug(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name or "perfil"


def _profile_path(slug: str) -> str:
    return os.path.join(PROFILES_DIR, f"{slug}.json")


def save_profile(profile_data: dict) -> str:
    Path(PROFILES_DIR).mkdir(parents=True, exist_ok=True)
    slug = _slug(profile_data.get("name", "perfil"))
    # Avoid overwriting a different person's file
    base, i = slug, 1
    while os.path.exists(_profile_path(slug)):
        existing = load_profile(slug)
        if existing and existing.get("name") == profile_data.get("name"):
            break
        slug = f"{base}_{i}"
        i += 1
    with open(_profile_path(slug), "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)
    set_selected(slug)
    return slug


def load_profile(slug: str) -> Optional[dict]:
    path = _profile_path(slug)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_profiles() -> list[str]:
    Path(PROFILES_DIR).mkdir(parents=True, exist_ok=True)
    return [
        f[:-5]
        for f in os.listdir(PROFILES_DIR)
        if f.endswith(".json")
    ]


def get_selected() -> Optional[str]:
    if os.path.exists(_SELECTED_FILE):
        with open(_SELECTED_FILE, "r", encoding="utf-8") as f:
            slug = f.read().strip()
        if os.path.exists(_profile_path(slug)):
            return slug
    slugs = list_profiles()
    return slugs[0] if slugs else None


def set_selected(slug: str) -> None:
    Path(PROFILES_DIR).mkdir(parents=True, exist_ok=True)
    with open(_SELECTED_FILE, "w", encoding="utf-8") as f:
        f.write(slug)


def delete_profile(slug: str) -> None:
    path = _profile_path(slug)
    if os.path.exists(path):
        os.remove(path)
    if get_selected() == slug:
        remaining = list_profiles()
        if remaining:
            set_selected(remaining[0])
        elif os.path.exists(_SELECTED_FILE):
            os.remove(_SELECTED_FILE)

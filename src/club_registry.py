"""Versionierten Clubkatalog laden; keine automatische Alias-Vermutung."""
from __future__ import annotations

import json
from pathlib import Path

from src.domain import Club, ClubRegistry, ProviderRef


DEFAULT_CATALOG = Path(__file__).resolve().parent / "reference" / "clubs.json"


def load_club_registry(path: Path = DEFAULT_CATALOG) -> ClubRegistry:
    if not path.exists():
        return ClubRegistry(())
    payload = json.loads(path.read_text(encoding="utf-8"))
    clubs = []
    for row in payload.get("clubs", []):
        refs = tuple(ProviderRef(str(provider), str(provider_id))
                     for provider, provider_id in row.get("provider_ids", {}).items())
        clubs.append(Club(row["club_id"], row["canonical_name"],
                          tuple(row.get("aliases", [])), refs))
    return ClubRegistry(tuple(clubs))

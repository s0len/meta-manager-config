"""Shared helpers for parsing SportsDB responses."""

from __future__ import annotations

import ssl
from typing import Any, Callable, Dict, List, Optional

from sportsdb import SportsDBSettings

FetchJsonFn = Callable[
    [str, ssl.SSLContext, Optional[Any], int, float, Optional[Dict[str, str]]],
    dict,
]


def extract_events(payload: dict) -> List[dict]:
    """Return the list of fixtures regardless of the API key used."""
    for key in ("events", "schedule", "fixtures", "results"):
        events = payload.get(key)
        if isinstance(events, list):
            return events
    return []


def fetch_season_description_text(
    *,
    season: str,
    league_id: int,
    sportsdb: SportsDBSettings,
    fetch_json: FetchJsonFn,
    context: ssl.SSLContext,
    rate_limiter: Optional[Any],
    retries: int,
    retry_backoff: float,
) -> Optional[str]:
    """Return the English description for a season when available."""
    url = sportsdb.season_description_url(league_id)
    payload = fetch_json(
        url,
        context,
        rate_limiter,
        retries,
        retry_backoff,
        headers=sportsdb.auth_headers,
    )
    entries = (
        payload.get("seasons")
        or payload.get("list")
        or payload.get("results")
        or []
    )
    for entry in entries:
        if entry.get("strSeason") != season:
            continue
        description = entry.get("strDescriptionEN")
        if isinstance(description, str) and description.strip():
            return description.strip()
    return None


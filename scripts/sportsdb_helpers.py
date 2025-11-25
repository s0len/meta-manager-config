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


def join_location(city: Optional[str], country: Optional[str]) -> str:
    """Return 'City, Country' when both values exist."""
    parts: List[str] = []
    if city and city.strip():
        parts.append(city.strip())
    if country and country.strip():
        parts.append(country.strip())
    return ", ".join(parts)


def location_suffix(
    city: Optional[str],
    country: Optional[str],
    prefix: str = " (",
    suffix: str = ")",
) -> str:
    """Return a formatted suffix like ' (City, Country)' when available."""
    location = join_location(city, country)
    if not location:
        return ""
    return f"{prefix}{location}{suffix}"


__all__ = [
    "extract_events",
    "fetch_season_description_text",
    "join_location",
    "location_suffix",
]


"""Shared helpers for configuring TheSportsDB requests.

These utilities centralize how we read API credentials from ``.env``/environment
variables and how we build v1/v2 endpoint URLs plus authentication headers. The
goal is to let every SportsDB-backed script share the same behavior, especially
now that premium accounts can target the v2 API with header-based auth
(`TheSportsDB docs <https://www.thesportsdb.com/documentation>`_).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote, quote_plus

DEFAULT_SITE_ROOT = "https://www.thesportsdb.com"
ENV_FILE_NAME = ".env"


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Return key/value pairs from a .env style file."""
    if not path.exists():
        return {}
    values: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        # Strip inline comments when they are separated by at least one space.
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def normalize_api_version(value: Optional[str]) -> str:
    """Normalize API version strings to the ``v#`` format (defaults to ``v1``)."""
    if not value:
        return "v1"
    cleaned = value.strip().lower()
    if not cleaned:
        return "v1"
    if not cleaned.startswith("v"):
        cleaned = f"v{cleaned}"
    return cleaned


def default_request_interval(api_version: str) -> float:
    """Return a safe default delay between requests for the selected tier."""
    version = normalize_api_version(api_version)
    # Premium/v2 users can hit 100 req/min, so ~0.6s spacing. Free/v1 is 30 req/min.
    return 0.6 if version == "v2" else 2.1


@dataclass(frozen=True)
class SportsDBSettings:
    """Holds API credentials plus helper builders for URLs and headers."""

    api_key: str
    api_version: str
    site_root: str = DEFAULT_SITE_ROOT

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_key", (self.api_key or "").strip() or "123")
        object.__setattr__(
            self, "api_version", normalize_api_version(self.api_version or "v1")
        )
        object.__setattr__(
            self,
            "site_root",
            (self.site_root or DEFAULT_SITE_ROOT).rstrip("/") or DEFAULT_SITE_ROOT,
        )

    def with_overrides(
        self,
        *,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> "SportsDBSettings":
        """Return a copy with updated credentials."""
        return SportsDBSettings(
            api_key=api_key if api_key is not None else self.api_key,
            api_version=api_version if api_version is not None else self.api_version,
            site_root=self.site_root,
        )

    @property
    def base_url(self) -> str:
        """Base API URL including version segment."""
        return f"{self.site_root}/api/{self.api_version}/json"

    @property
    def is_v2(self) -> bool:
        return self.api_version == "v2"

    @property
    def auth_headers(self) -> Dict[str, str]:
        """Headers required for the current API tier."""
        if self.is_v2 and self.api_key:
            return {"X-API-KEY": self.api_key}
        return {}

    def season_url(self, league_id: int, season: str) -> str:
        """Return the correct season endpoint for the chosen API version."""
        if self.is_v2:
            encoded_season = quote(season, safe="")
            return f"{self.base_url}/schedule/league/{league_id}/{encoded_season}"
        encoded_season = quote_plus(season, safe="")
        return (
            f"{self.base_url}/{self.api_key}/eventsseason.php"
            f"?id={league_id}&s={encoded_season}"
        )

    def round_url(self, league_id: int, season: str, round_number: int) -> Optional[str]:
        """Return the v1-only round endpoint (v2 requires filtering)."""
        if self.is_v2:
            return None
        encoded_season = quote_plus(season, safe="")
        return (
            f"{self.base_url}/{self.api_key}/eventsround.php"
            f"?id={league_id}&r={round_number}&s={encoded_season}"
        )

    def season_description_url(self, league_id: int) -> str:
        """Return endpoint containing per-season descriptions."""
        if self.is_v2:
            return f"{self.base_url}/list/seasons/{league_id}"
        return f"{self.base_url}/{self.api_key}/all_seasons.php?id={league_id}"


def load_sportsdb_settings(env_path: Optional[Path] = None) -> SportsDBSettings:
    """Load SportsDB credentials from .env overrides plus the active environment."""
    repo_root = Path(__file__).resolve().parents[1]
    env_file = env_path or (repo_root / ENV_FILE_NAME)

    values = _parse_env_file(env_file)
    for key, value in os.environ.items():
        if key.startswith("SPORTSDB_") or key == "THESPORTSDB_API_KEY":
            values[key] = value

    api_key = (
        values.get("SPORTSDB_API_KEY")
        or values.get("THESPORTSDB_API_KEY")
        or "123"
    )
    api_version = values.get("SPORTSDB_API_VERSION", "v1")
    site_root = (
        values.get("SPORTSDB_SITE_ROOT")
        or values.get("SPORTSDB_BASE_URL")
        or DEFAULT_SITE_ROOT
    )
    return SportsDBSettings(api_key=api_key, api_version=api_version, site_root=site_root)


__all__ = [
    "SportsDBSettings",
    "default_request_interval",
    "load_sportsdb_settings",
    "normalize_api_version",
]


#!/usr/bin/env python3
"""Generate UEFA Champions League metadata YAML files for Sports Organizer.

This tool mirrors the structure used by the Premier League and NFL generators in
this repository. Matchdays are treated as seasons, and every fixture within the
matchday becomes an episode entry that includes venue and kickoff context.

Example usage:

    python3 scripts/generate_uefa_champions_league_metadata.py --season-year 2025

The script pulls the public match feed consumed by UEFA.com, groups fixtures by
matchday and emits a YAML document under ``metadata-files/``.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


BASE_URL = (
    "https://www.uefa.com/api/match-api/v1/competitions/{competition}/"
    "seasons/{season}/matches"
)

FALLBACK_URLS = [
    BASE_URL,
    "https://www.uefa.com/api/match-api/v2/competitions/{competition}/seasons/{season}/matches",
    "https://www.uefa.com/api/match-api/v3/competitions/{competition}/seasons/{season}/matches",
    "https://www.uefa.com/api/match-api/v6/competitions/{competition}/matches?season={season}",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.uefa.com/uefachampionsleague/fixtures-results/",
    "Origin": "https://www.uefa.com",
    "Connection": "keep-alive",
}


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def fetch_all_matches(
    competition: str,
    season_year: int,
    context: ssl.SSLContext,
    *,
    timeout: float,
    retries: int,
    retry_delay: float,
    base_url: Optional[str] = None,
) -> List[dict]:
    url_template = base_url or BASE_URL
    url = url_template.format(competition=competition, season=season_year)
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)

    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(request, context=context, timeout=timeout) as response:
                payload = json.load(response)
            break
        except (socket.timeout, TimeoutError, urllib.error.URLError) as exc:
            attempt += 1
            if attempt > retries:
                raise
            sleep_for = retry_delay * (2 ** (attempt - 1))
            print(
                f"Retrying UEFA feed fetch (attempt {attempt}/{retries}) after error: {exc}",
                file=sys.stderr,
            )
            time.sleep(sleep_for)

    if isinstance(payload, dict):
        matches = payload.get("matches")
        if matches is not None:
            return list(matches)
        # Some older variants return the list directly under "data".
        if "data" in payload and isinstance(payload["data"], dict):
            data_matches = payload["data"].get("matches")
            if isinstance(data_matches, list):
                return list(data_matches)
        if "data" in payload and isinstance(payload["data"], list):
            return list(payload["data"])

    if isinstance(payload, list):
        return list(payload)

    return []


def _wrap(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    return [f"{prefix}{line}" for line in wrapper.wrap(text)]


def _coalesce_name(value: Optional[dict], *fallback_keys: str) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, dict):
        for key in ("default", "en", "id", "shortName", "fullName"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

    for key in fallback_keys:
        if isinstance(value, dict):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def _team_name(team: Optional[dict]) -> Optional[str]:
    if not team:
        return None

    for branch in (team.get("club"), team.get("team"), team):
        if isinstance(branch, dict):
            name = _coalesce_name(
                branch.get("name") if isinstance(branch.get("name"), dict) else branch,
                "officialName",
                "displayName",
                "shortName",
                "name",
            )
            if name:
                return name

    return None


def _venue_details(match: dict) -> Tuple[str, str]:
    venue = match.get("venue") or {}
    stadium = venue.get("stadium") or {}
    city = venue.get("city") or {}
    country = venue.get("country") or city.get("country") or {}

    stadium_name = (
        _coalesce_name(stadium.get("name"), "fullName", "shortName")
        or _coalesce_name(venue.get("name"))
        or "TBD Venue"
    )

    city_name = _coalesce_name(city.get("name"), "fullName")
    country_name = _coalesce_name(country.get("name"), "fullName")

    parts = [part for part in (city_name, country_name) if part]
    location = ", ".join(parts)
    return stadium_name, location


def _parse_kickoff(match: dict) -> Tuple[Optional[datetime], Optional[str]]:
    kickoff = match.get("kickOffTime") or match.get("kickoff") or {}

    for key in ("utcDate", "date", "utc"):
        iso = kickoff.get(key) or match.get(key)
        if isinstance(iso, str) and iso.strip():
            iso_value = iso.strip()
            if iso_value.endswith("Z"):
                iso_value = iso_value.replace("Z", "+00:00")
            elif len(iso_value) == 10:
                iso_value += "T00:00:00+00:00"
            elif iso_value.endswith("+0000"):
                iso_value = iso_value[:-5] + "+00:00"
            try:
                kickoff_dt = datetime.fromisoformat(iso_value)
                if kickoff_dt.tzinfo is None:
                    kickoff_dt = kickoff_dt.replace(tzinfo=timezone.utc)
                return kickoff_dt.astimezone(timezone.utc), kickoff.get("label")
            except ValueError:
                continue

    millis = kickoff.get("millis")
    if millis is not None:
        try:
            kickoff_dt = datetime.fromtimestamp(float(millis) / 1000.0, tz=timezone.utc)
            return kickoff_dt, kickoff.get("label")
        except (ValueError, OSError):
            pass

    return None, kickoff.get("label")


def _matchday_identity(match: dict) -> Tuple[str, str, int]:
    matchday = match.get("matchday") or {}
    identifier = matchday.get("id") or matchday.get("number") or matchday.get("orderNumber")
    name = matchday.get("name") or matchday.get("phaseName") or matchday.get("label")

    if isinstance(name, dict):
        name = _coalesce_name(name)

    if name is None and identifier is not None:
        name = f"Matchday {identifier}"

    if name is None:
        stage = match.get("stage") or {}
        stage_name = stage.get("name")
        if isinstance(stage_name, dict):
            stage_name = _coalesce_name(stage_name)
        if stage_name:
            name = stage_name
        else:
            name = "Matchday"

    key = str(identifier) if identifier is not None else name

    sort_hint = matchday.get("orderNumber") or matchday.get("sequence") or matchday.get("sortOrder")
    if isinstance(sort_hint, str):
        try:
            sort_hint = int(sort_hint)
        except ValueError:
            sort_hint = None

    if sort_hint is None:
        try:
            sort_hint = int(str(identifier))
        except (TypeError, ValueError):
            sort_hint = 10_000

    return key, name, int(sort_hint)


def _format_date_range(dates: Iterable[date]) -> str:
    ordered = sorted(dates)
    if not ordered:
        return ""

    first, last = ordered[0], ordered[-1]
    if first == last:
        return f"{first.strftime('%B')} {first.day}, {first.year}"

    if first.year == last.year:
        if first.month == last.month:
            return f"{first.strftime('%B')} {first.day}-{last.day}, {first.year}"
        return (
            f"{first.strftime('%B')} {first.day} - {last.strftime('%B')} {last.day}, {first.year}"
        )

    return (
        f"{first.strftime('%B')} {first.day}, {first.year} - "
        f"{last.strftime('%B')} {last.day}, {last.year}"
    )


def group_by_matchday(
    matches: List[dict],
    requested_keys: Optional[Iterable[str]] = None,
) -> List[dict]:
    requested_set = {str(item) for item in requested_keys} if requested_keys else None

    grouped: Dict[str, dict] = {}

    for match in matches:
        key, name, sort_hint = _matchday_identity(match)
        if requested_set and key not in requested_set and name not in requested_set:
            continue

        container = grouped.setdefault(
            key,
            {
                "key": key,
                "name": name,
                "sort_hint": sort_hint,
                "matches": [],
                "dates": [],
            },
        )

        kickoff_dt, kickoff_label = _parse_kickoff(match)
        match_date = kickoff_dt.date() if kickoff_dt else date.today()

        home = _team_name(match.get("homeTeam")) or "Home Team"
        away = _team_name(match.get("awayTeam")) or "Away Team"
        stadium, location = _venue_details(match)

        summary_bits = [f"{name} fixture at {stadium}"]
        if location:
            summary_bits[-1] += f" ({location})"
        summary_bits[-1] += "."
        summary_bits.append(
            f"Scheduled date: {match_date.strftime('%B')} {match_date.day}, {match_date.year}."
        )
        if kickoff_label:
            summary_bits.append(f"Kickoff: {kickoff_label}.")

        container["matches"].append(
            {
                "home": home,
                "away": away,
                "date": match_date,
                "kickoff": kickoff_dt,
                "summary": " ".join(summary_bits),
            }
        )
        container["dates"].append(match_date)

    bundles = list(grouped.values())
    bundles.sort(
        key=lambda item: (
            item["sort_hint"],
            min(item["dates"]) if item["dates"] else date.max,
            item["name"],
        )
    )
    return bundles


def render_yaml(metadata: dict) -> str:
    lines = ["metadata:"]
    lines.append(f"  {metadata['show_id']}:")
    lines.append(f"    title: {metadata['title']}")
    lines.append(f"    sort_title: {metadata['sort_title']}")
    lines.append(f"    url_poster: {metadata['poster_url']}")
    lines.append(f"    url_background: {metadata['background_url']}")
    lines.append("    summary: >")
    lines.extend(_wrap("      ", metadata["summary"], 100))
    lines.append("    seasons:")

    for season in metadata["seasons"]:
        lines.append(f"      {season['number']}:")
        lines.append(f"        title: {season['title']}")
        lines.append(f"        sort_title: {season['sort_title']}")
        lines.append("        summary: >")
        lines.extend(_wrap("          ", season["summary"], 96))
        lines.append("        episodes:")
        if season["episodes"]:
            for episode in season["episodes"]:
                lines.append(f"          {episode['index']}:")
                lines.append(f"            title: {episode['title']}")
                lines.append(
                    f"            originally_available: {episode['originally_available']}"
                )
                lines.append("            summary: >")
                lines.extend(_wrap("              ", episode["summary"], 86))
        else:
            lines.append("          {}")

    return "\n".join(lines) + "\n"


def build_metadata(args: argparse.Namespace) -> dict:
    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)

    payload: Optional[dict] = None

    if args.source_json:
        source_path = Path(args.source_json).expanduser()
        data = source_path.read_text(encoding="utf-8")
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            snippet = data.strip()
            if snippet.startswith("<"):
                raise ValueError(
                    "The file loaded via --source-json appears to be HTML (likely an error "
                    "page). UEFA often requires browser-like headers. Try re-downloading "
                    "with the example curl command in scripts/README.md."
                ) from exc
            raise ValueError(
                "Unable to decode JSON from --source-json. Ensure the file contains the raw "
                "UEFA match feed payload."
            ) from exc

    if payload is None:
        url_candidates = [args.base_url] if args.base_url else FALLBACK_URLS

        last_exc: Optional[Exception] = None
        for template in url_candidates:
            if template is None:
                continue
            try:
                matches_raw = fetch_all_matches(
                    args.competition,
                    args.season_year,
                    context,
                    timeout=args.timeout,
                    retries=args.retries,
                    retry_delay=args.retry_delay,
                    base_url=template,
                )
                break
            except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                last_exc = exc
                continue
        else:
            if last_exc is not None:
                if verify_ssl:
                    verify_ssl = False
                    context = build_ssl_context(False)
                    for template in url_candidates:
                        if template is None:
                            continue
                        try:
                            matches_raw = fetch_all_matches(
                                args.competition,
                                args.season_year,
                                context,
                                timeout=args.timeout,
                                retries=args.retries,
                                retry_delay=args.retry_delay,
                                base_url=template,
                            )
                            print(
                                "Warning: SSL verification disabled due to fetch error:",
                                last_exc,
                                file=sys.stderr,
                            )
                            break
                        except (urllib.error.URLError, TimeoutError, socket.timeout):
                            continue
                    else:
                        raise last_exc
                else:
                    raise last_exc
            else:
                matches_raw = []

        if args.cache_json:
            cache_path = Path(args.cache_json).expanduser()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({"matches": matches_raw}, indent=2), encoding="utf-8")
        payload = {"matches": matches_raw}
    else:
        matches_raw = payload

    matches_list: List[dict]
    if isinstance(payload, dict) and "matches" in payload:
        value = payload["matches"]
        if isinstance(value, list):
            matches_list = value
        else:
            matches_list = []
    elif isinstance(payload, list):
        matches_list = payload
    else:
        matches_list = []

    grouped = group_by_matchday(matches_list, args.matchdays)

    seasons = []
    for idx, bundle in enumerate(grouped, start=1):
        events = sorted(
            bundle["matches"],
            key=lambda item: (
                item["date"],
                item["home"],
                item["away"],
            ),
        )

        span = _format_date_range(event["date"] for event in events) if events else None
        if span:
            summary = (
                f"{bundle['name']} covers {span} with {len(events)} scheduled fixtures."
            )
        else:
            summary = f"{bundle['name']} currently has no fixtures available."

        seasons.append(
            {
                "number": idx if args.renumber else bundle["key"],
                "title": bundle["name"],
                "sort_title": f"{idx:02d}_{bundle['name']}",
                "summary": summary,
                "episodes": [
                    {
                        "index": ep_idx,
                        "title": f"{event['home']} vs {event['away']}",
                        "originally_available": event["date"].isoformat(),
                        "summary": event["summary"],
                    }
                    for ep_idx, event in enumerate(events, start=1)
                ],
            }
        )

    show_id = args.show_id or f"UEFA Champions League {args.season_year}-{args.season_year + 1}"
    return {
        "show_id": show_id,
        "title": args.title or show_id,
        "sort_title": args.sort_title or show_id,
        "poster_url": args.poster_url,
        "background_url": args.background_url,
        "summary": args.summary,
        "seasons": seasons,
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a UEFA Champions League metadata YAML file for Sports Organizer.",
    )
    parser.add_argument(
        "--season-year",
        type=int,
        required=True,
        help="Season start year (e.g. 2025 for the 2025/26 campaign).",
    )
    parser.add_argument(
        "--competition",
        default="CL",
        help="UEFA competition code (defaults to 'CL' for Champions League).",
    )
    parser.add_argument(
        "--matchdays",
        nargs="*",
        help="Optional list of matchday identifiers to include (e.g. 1 2 3 or 'Matchday 1').",
    )
    parser.add_argument(
        "--title",
        help="Custom show title (default 'UEFA Champions League <year>-<year+1>').",
    )
    parser.add_argument(
        "--sort-title",
        help="Custom sort title (defaults to the show title).",
    )
    parser.add_argument(
        "--show-id",
        help="Identifier used in the YAML key (defaults to the show title).",
    )
    parser.add_argument(
        "--poster-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
        "uefa-champions-league-{year}-{year_next}/poster.jpg",
        help="Poster URL (supports {year} template).",
    )
    parser.add_argument(
        "--background-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
        "uefa-champions-league-{year}-{year_next}/background.jpg",
        help="Background URL (supports {year} template).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {year}-{year_next} UEFA Champions League campaign adopts UEFA's league phase "
            "format, grouping fixtures by matchday before the knockout rounds. Each matchday "
            "section in this metadata file lists every scheduled tie with venue and kickoff "
            "context so Sports Organizer can match and rename recordings accurately."
        ),
        help="Show summary text (supports {year} template).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML (default metadata-files/uefa-champions-league-<year>-<year+1>.yaml).",
    )
    parser.add_argument(
        "--renumber",
        action="store_true",
        help="Rewrite season numbers sequentially instead of using the raw matchday identifier.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL verification if the system trust store is incomplete.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=45.0,
        help="Timeout in seconds for the UEFA feed request (default 45).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Number of retry attempts if the UEFA feed request fails (default 5).",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=3.0,
        help="Base delay in seconds between retries; doubles on each retry (default 3).",
    )
    parser.add_argument(
        "--base-url",
        help=(
            "Override the matches endpoint template. Use {competition} and {season} placeholders."
        ),
    )
    parser.add_argument(
        "--source-json",
        help="Path to a local matches JSON payload (skips network fetch).",
    )
    parser.add_argument(
        "--cache-json",
        help="Path to write the downloaded matches payload for reuse/debugging.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    year_next = args.season_year + 1
    args.poster_url = args.poster_url.format(year=args.season_year, year_next=year_next)
    args.background_url = args.background_url.format(
        year=args.season_year, year_next=year_next
    )
    args.summary = args.summary.format(year=args.season_year, year_next=year_next)

    metadata = build_metadata(args)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        output_path = Path("metadata-files") / (
            f"uefa-champions-league-{args.season_year}-{year_next}.yaml"
        )
    else:
        output_path = output_path.expanduser()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Generated metadata written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())



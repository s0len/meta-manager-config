#!/usr/bin/env python3
"""Utility for generating NFL season metadata YAML files.

The script pulls the weekly scoreboard feed published by ESPN and emits a
metadata document compatible with the Sports Organizer configuration format
used in this repository.  By default it produces the entire regular season

for a given year (Weeks 1-18, season type 2) and writes the output to
`metadata-files/nfl-<year>-<year+1>.yaml`.

Example usage:

    python3 scripts/generate_nfl_metadata.py --year 2025

Additional options let you customise the show title, poster/background URLs
or output location.  Pass ``--help`` for the complete argument list.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Optional


BASE_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    "scoreboard?seasontype={season_type}&year={year}&week={week}"
)

MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    """Return an SSL context, optionally disabling certificate verification."""

    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def fetch_week_data(
    year: int,
    week: int,
    season_type: int,
    context: ssl.SSLContext,
) -> dict:
    """Download and decode the scoreboard JSON for a specific week."""

    url = BASE_URL.format(year=year, season_type=season_type, week=week)
    with urllib.request.urlopen(url, context=context) as response:
        return json.load(response)


def _parse_game_date(
    scheduled_detail: str,
    short_detail: str,
    start_dt: datetime,
) -> date:
    """Derive the calendar date for a game using ESPN's detail strings."""

    target_detail = scheduled_detail or short_detail
    month: Optional[int] = None
    day: Optional[int] = None

    if target_detail and " at " in target_detail:
        date_part = target_detail.split(" at ")[0]
        if ", " in date_part:
            _, month_day = date_part.split(", ", 1)
        else:
            month_day = date_part
        parts = month_day.split(" ")
        if len(parts) >= 2 and parts[0] in MONTH_MAP:
            month = MONTH_MAP[parts[0]]
            cleaned_day = parts[1].rstrip("stndrdth")
            if cleaned_day.isdigit():
                day = int(cleaned_day)

    if month is None or day is None:
        fallback = target_detail or short_detail
        if fallback:
            for token in fallback.replace("-", " ").split():
                if "/" in token:
                    numbers = token.split("/")
                    if len(numbers) == 2 and all(x.isdigit() for x in numbers):
                        month = int(numbers[0])
                        day = int(numbers[1])
                        break

    if month is None or day is None:
        return start_dt.date()

    year = start_dt.year
    if month < start_dt.month and start_dt.month >= 9 and month <= 4:
        year += 1

    return date(year, month, day)


def _normalise_kickoff(detail: str) -> Optional[str]:
    """Return a detail string if it conveys future scheduling information."""

    cleaned = (detail or "").strip()
    if not cleaned:
        return None

    lowered = cleaned.lower()
    if lowered.startswith("final"):
        return None
    if "tbd" in lowered and cleaned.upper() == "TBD":
        return None
    return cleaned


def _format_date_range(dates: Iterable[date]) -> str:
    """Present a human-readable span for the collection of game dates."""

    ordered: List[date] = sorted(dates)
    if not ordered:
        return ""

    first, last = ordered[0], ordered[-1]
    if first == last:
        return f"{first.strftime('%B')} {first.day}, {first.year}"

    if first.year == last.year:
        if first.month == last.month:
            return (
                f"{first.strftime('%B')} {first.day}-{last.day}, {first.year}"
            )
        return (
            f"{first.strftime('%B')} {first.day} - {last.strftime('%B')} {last.day},"
            f" {first.year}"
        )

    return (
        f"{first.strftime('%B')} {first.day}, {first.year} - "
        f"{last.strftime('%B')} {last.day}, {last.year}"
    )


def _wrap_lines(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    return [f"{prefix}{line}" for line in wrapper.wrap(text)]


def collect_week_events(
    payload: dict,
    week: int,
) -> List[dict]:
    """Extract the relevant details for every game in the week payload."""

    events: List[dict] = []
    for event in payload.get("events", []):
        competitions = event.get("competitions") or []
        if not competitions:
            continue

        comp = competitions[0]
        status = comp.get("status", {}).get("type", {})
        detail = status.get("detail") or ""
        short_detail = status.get("shortDetail") or ""
        start_iso = comp.get("date") or comp.get("startDate")
        if not start_iso:
            continue

        start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        game_date = _parse_game_date(detail, short_detail, start_dt)

        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue

        home_name = home.get("team", {}).get("displayName") or home.get("team", {}).get("name")
        away_name = away.get("team", {}).get("displayName") or away.get("team", {}).get("name")
        if not home_name or not away_name:
            continue

        venue = comp.get("venue") or {}
        venue_name = venue.get("fullName") or "TBD Venue"
        address = venue.get("address") or {}
        location_parts = [address.get("city"), address.get("state")]  # type: ignore[arg-type]
        country = address.get("country") or address.get("countryCode")
        if country and country not in ("USA", "United States"):
            location_parts.append(country)
        location = ", ".join(part for part in location_parts if part)

        kickoff_detail = _normalise_kickoff(detail or short_detail)

        summary_bits = [f"Week {week} matchup at {venue_name}"]
        if location:
            summary_bits[-1] += f" ({location})"
        summary_bits[-1] += "."
        summary_bits.append(
            f"Scheduled date: {game_date.strftime('%B')} {game_date.day}, {game_date.year}."
        )
        if kickoff_detail:
            summary_bits.append(f"Listed kickoff: {kickoff_detail}.")

        events.append(
            {
                "start": start_dt,
                "date": game_date,
                "home": home_name,
                "away": away_name,
                "summary": " ".join(summary_bits),
            }
        )

    events.sort(key=lambda item: item["start"])
    return events


def render_yaml(metadata: dict) -> str:
    """Convert the metadata dictionary to a YAML string without external deps."""

    lines: List[str] = ["metadata:"]
    lines.append(f"  {metadata['show_id']}:")
    lines.append(f"    title: {metadata['title']}")
    lines.append(f"    sort_title: {metadata['sort_title']}")
    lines.append(f"    url_poster: {metadata['poster_url']}")
    lines.append(f"    url_background: {metadata['background_url']}")
    lines.append("    summary: >")
    lines.extend(_wrap_lines("      ", metadata["summary"]))
    lines.append("    seasons:")

    for season in metadata["seasons"]:
        lines.append(f"      {season['number']}:")
        lines.append(f"        title: {season['title']}")
        lines.append(f"        sort_title: {season['sort_title']}")
        lines.append("        summary: >")
        lines.extend(_wrap_lines("          ", season["summary"]))
        lines.append("        episodes:")
        for episode in season["episodes"]:
            lines.append(f"          {episode['index']}:")
            lines.append(f"            title: {episode['title']}")
            lines.append(
                f"            originally_available: {episode['originally_available']}"
            )
            lines.append("            summary: >")
            lines.extend(_wrap_lines("              ", episode["summary"]))

    return "\n".join(lines) + "\n"


def build_metadata(args: argparse.Namespace) -> dict:
    """Assemble the complete metadata structure for the requested season."""

    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)

    seasons = []
    for week in args.weeks:
        try:
            payload = fetch_week_data(args.year, week, args.season_type, context)
        except urllib.error.URLError as exc:
            if verify_ssl:
                # Retry once with verification disabled and warn the user.
                verify_ssl = False
                context = build_ssl_context(False)
                payload = fetch_week_data(args.year, week, args.season_type, context)
                print(
                    "Warning: SSL verification disabled due to fetch error:",
                    exc,
                    file=sys.stderr,
                )
            else:
                raise

        events = collect_week_events(payload, week)
        dates = [event["date"] for event in events]
        span_text = _format_date_range(dates) if dates else None
        if span_text:
            summary = (
                f"Week {week} covers {span_text} with {len(events)} scheduled games across the league."
            )
        else:
            summary = f"Week {week} currently has no scheduled games listed."

        seasons.append(  # type: ignore[arg-type]
            {
                "number": week,
                "title": f"Week {week}",
                "sort_title": f"{week:02d}_Week {week}",
                "summary": summary,
                "episodes": [
                    {
                        "index": idx,
                        "title": f"{event['away']} vs {event['home']}",
                        "originally_available": event["date"].isoformat(),
                        "summary": event["summary"],
                    }
                    for idx, event in enumerate(events, start=1)
                ],
            }
        )

    next_year_suffix = f"{(args.year + 1) % 100:02d}"
    show_id = args.show_id or f"NFL {args.year}-{next_year_suffix}"
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
        description="Generate an NFL season metadata YAML file for Sports Organizer.",
    )
    parser.add_argument("--year", type=int, required=True, help="Season year (regular-season start).")
    parser.add_argument(
        "--season-type",
        type=int,
        default=2,
        help="ESPN seasonType value (1=preseason, 2=regular, 3=postseason).",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        nargs="*",
        default=list(range(1, 19)),
        help="Explicit list of week numbers to include (default 1-18).",
    )
    parser.add_argument(
        "--title",
        help="Custom show title. Defaults to 'NFL <year>-<year+1>'.",
    )
    parser.add_argument(
        "--sort-title",
        help="Custom sort title. Defaults to the chosen show title.",
    )
    parser.add_argument(
        "--show-id",
        help="Identifier used in the YAML key. Defaults to 'NFL <year>-<year+1>'.",
    )
    parser.add_argument(
        "--poster-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
        "nfl-{year}-{year_next}/poster.jpg",
        help="Poster image URL inserted into the metadata (supports {year} template).",
    )
    parser.add_argument(
        "--background-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
        "nfl-{year}-{year_next}/background.jpg",
        help="Background image URL inserted into the metadata (supports {year} template).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {year}-{year_next} National Football League regular season covers 18 weeks of action "
            "across the United States and international venues, with every contest captured here for "
            "Sports Organizer. Episodes are grouped by NFL week and include broadcast dates with venue "
            "context so recorded files can be matched and renamed reliably."
        ),
        help="Show summary text (supports {year} template).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML (defaults to metadata-files/nfl-<year>-<year+1>.yaml).",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification (useful if the system trust store is incomplete).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    year_next_suffix = f"{(args.year + 1) % 100:02d}"
    args.poster_url = args.poster_url.format(year=args.year, year_next=year_next_suffix)
    args.background_url = args.background_url.format(year=args.year, year_next=year_next_suffix)
    args.summary = args.summary.format(year=args.year, year_next=year_next_suffix)

    metadata = build_metadata(args)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        output_path = Path("metadata-files") / f"nfl-{args.year}-{year_next_suffix}.yaml"
    else:
        output_path = output_path.expanduser()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Generated metadata written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


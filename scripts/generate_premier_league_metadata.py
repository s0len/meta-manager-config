#!/usr/bin/env python3
"""Generate Premier League metadata YAML files for Sports Organizer.

This tool mirrors the behaviour of :mod:`generate_nfl_metadata`, but targets the
Premier League (competition id 1 on footballapi.pulselive.com). It iterates over
matchweeks, fetches fixtures for the requested season and renders a metadata
document containing seasons for each matchweek and an episode per fixture.

Example usage:

    python3 scripts/generate_premier_league_metadata.py --year 2025 --season-id 777

The season id can be retrieved from ``/football/competitions/1/compseasons`` on the
Pulse Live API (e.g. 777 corresponds to the 2025/26 campaign).
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


BASE_URL = (
    "https://footballapi.pulselive.com/football/fixtures?comps={competition}"
    "&compSeasons={season_id}&matchweek={matchweek}&page={page}&pageSize={page_size}"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

DEFAULT_PAGE_SIZE = 50


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def fetch_matchweek_page(
    competition: int,
    season_id: int,
    matchweek: int,
    page: int,
    page_size: int,
    context: ssl.SSLContext,
) -> dict:
    url = BASE_URL.format(
        competition=competition,
        season_id=season_id,
        matchweek=matchweek,
        page=page,
        page_size=page_size,
    )
    request = urllib.request.Request(
        url,
        headers=
        {
            "User-Agent": USER_AGENT,
            "Origin": "https://www.premierleague.com",
            "Referer": "https://www.premierleague.com/",
        },
    )
    with urllib.request.urlopen(request, context=context) as response:
        return json.load(response)


def fetch_matchweek_fixtures(
    competition: int,
    season_id: int,
    matchweek: int,
    context: ssl.SSLContext,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> List[dict]:
    fixtures: List[dict] = []
    page = 0

    while True:
        payload = fetch_matchweek_page(
            competition,
            season_id,
            matchweek,
            page,
            page_size,
            context,
        )

        for item in payload.get("content", []):
            gw = item.get("gameweek", {}).get("gameweek")
            if gw is not None and int(round(float(gw))) == matchweek:
                fixtures.append(item)

        page_info = payload.get("pageInfo", {})
        num_pages = int(page_info.get("numPages", 0))
        if page >= num_pages - 1:
            break
        page += 1

    return fixtures


def _wrap(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    return [f"{prefix}{line}" for line in wrapper.wrap(text)]


def _format_date_range(dates: Iterable[date]) -> str:
    ordered = sorted(dates)
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
            f"{first.strftime('%B')} {first.day} - {last.strftime('%B')} {last.day}, {first.year}"
        )

    return (
        f"{first.strftime('%B')} {first.day}, {first.year} - "
        f"{last.strftime('%B')} {last.day}, {last.year}"
    )


def _select_kickoff(fixture: dict) -> dict:
    kickoff = fixture.get("kickoff") or {}
    if kickoff.get("millis") is not None:
        return kickoff
    return fixture.get("provisionalKickoff") or kickoff


def parse_fixture(fixture: dict, matchweek: int) -> Optional[dict]:
    teams = fixture.get("teams", [])
    if len(teams) != 2:
        return None

    home_team = teams[0].get("team", {}).get("name")
    away_team = teams[1].get("team", {}).get("name")
    if not home_team or not away_team:
        return None

    ground = fixture.get("ground") or {}
    ground_name = ground.get("name") or "TBD Venue"
    location_parts = [ground.get("city")]
    location = ", ".join(part for part in location_parts if part)

    kickoff_info = _select_kickoff(fixture)
    millis = kickoff_info.get("millis")
    if millis is not None:
        kickoff_dt = datetime.fromtimestamp(float(millis) / 1000.0, tz=timezone.utc)
        game_date = kickoff_dt.date()
    else:
        game_date = date.today()

    kickoff_label = kickoff_info.get("label")

    summary_parts = [f"Matchweek {matchweek} fixture at {ground_name}"]
    if location:
        summary_parts[-1] += f" ({location})"
    summary_parts[-1] += "."
    summary_parts.append(
        f"Scheduled date: {game_date.strftime('%B')} {game_date.day}, {game_date.year}."
    )
    if kickoff_label:
        summary_parts.append(f"Kickoff: {kickoff_label}.")

    return {
        "home": home_team,
        "away": away_team,
        "date": game_date,
        "summary": " ".join(summary_parts),
    }


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
        for episode in season["episodes"]:
            lines.append(f"          {episode['index']}:")
            lines.append(f"            title: {episode['title']}")
            lines.append(
                f"            originally_available: {episode['originally_available']}"
            )
            lines.append("            summary: >")
            lines.extend(_wrap("              ", episode["summary"], 86))

    return "\n".join(lines) + "\n"


def build_metadata(args: argparse.Namespace) -> dict:
    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)

    seasons = []
    for matchweek in args.matchweeks:
        try:
            fixtures = fetch_matchweek_fixtures(
                args.competition,
                args.season_id,
                matchweek,
                context,
                page_size=args.page_size,
            )
        except urllib.error.URLError as exc:
            if verify_ssl:
                verify_ssl = False
                context = build_ssl_context(False)
                fixtures = fetch_matchweek_fixtures(
                    args.competition,
                    args.season_id,
                    matchweek,
                    context,
                    page_size=args.page_size,
                )
                print(
                    "Warning: SSL verification disabled due to fetch error:",
                    exc,
                    file=sys.stderr,
                )
            else:
                raise

        events: List[dict] = []
        for fixture in fixtures:
            parsed = parse_fixture(fixture, matchweek)
            if parsed is not None:
                events.append(parsed)

        events.sort(key=lambda item: (item["date"], item["home"], item["away"]))
        dates = [event["date"] for event in events]
        span = _format_date_range(dates) if dates else None
        if span:
            summary = (
                f"Matchweek {matchweek} covers {span} with {len(events)} scheduled fixtures."
            )
        else:
            summary = f"Matchweek {matchweek} currently has no fixtures available."

        seasons.append(
            {
                "number": matchweek,
                "title": f"Matchweek {matchweek}",
                "sort_title": f"{matchweek:02d}_Matchweek {matchweek}",
                "summary": summary,
                "episodes": [
                    {
                        "index": idx,
                        "title": f"{event['home']} vs {event['away']}",
                        "originally_available": event["date"].isoformat(),
                        "summary": event["summary"],
                    }
                    for idx, event in enumerate(events, start=1)
                ],
            }
        )

    show_id = args.show_id or f"Premier League {args.year}-{args.year + 1}"
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
        description="Generate a Premier League metadata YAML file for Sports Organizer.",
    )
    parser.add_argument("--year", type=int, required=True, help="Season start year (e.g. 2025).")
    parser.add_argument(
        "--season-id",
        type=int,
        required=True,
        help="Pulse Live compSeason identifier for the campaign (e.g. 777 for 2025/26).",
    )
    parser.add_argument(
        "--competition",
        type=int,
        default=1,
        help="Competition id (Premier League defaults to 1).",
    )
    parser.add_argument(
        "--matchweeks",
        type=int,
        nargs="*",
        default=list(range(1, 39)),
        help="Explicit list of matchweeks to include (default 1-38).",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Fixtures page size when calling the API (default 50).",
    )
    parser.add_argument(
        "--title",
        help="Custom show title (default 'Premier League <year>-<year+1>').",
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
        "premier-league-{year}-{year_next}/poster.jpg",
        help="Poster URL (supports {year} template).",
    )
    parser.add_argument(
        "--background-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
        "premier-league-{year}-{year_next}/background.jpg",
        help="Background URL (supports {year} template).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {year}-{year_next} Premier League campaign spans 38 matchweeks, bringing top-flight "
            "fixtures from across England and Wales. This metadata groups each matchweek with its "
            "scheduled fixtures, including kickoff notes and venue details so Sports Organizer can "
            "match and rename recordings accurately."
        ),
        help="Show summary text (supports {year} template).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML (default metadata-files/premier-league-<year>-<year+1>.yaml).",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL verification if the system trust store is incomplete.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    year_next = args.year + 1
    args.poster_url = args.poster_url.format(year=args.year, year_next=year_next)
    args.background_url = args.background_url.format(year=args.year, year_next=year_next)
    args.summary = args.summary.format(year=args.year, year_next=year_next)

    metadata = build_metadata(args)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        output_path = Path("metadata-files") / f"premier-league-{args.year}-{year_next}.yaml"
    else:
        output_path = output_path.expanduser()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Generated metadata written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


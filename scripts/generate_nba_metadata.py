#!/usr/bin/env python3
"""Generate NBA metadata YAML files for Sports Organizer.

This script mirrors the behaviour of the NFL and Premier League helpers but
targets the National Basketball Association. It downloads the season schedule
from the public NBA CDN, groups fixtures by NBA "weekNumber" and emits a YAML
document whose seasons correspond to those league weeks.

Example usage:

    python3 scripts/generate_nba_metadata.py --year 2025

By default only regular-season games are included. Pass ``--phase`` multiple
times to add other competition phases such as preseason or the Emirates NBA Cup.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import textwrap
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_SOURCE_URL = (
    "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

PHASE_LABELS: Dict[str, str] = {
    "regular": "",
    "preseason": "Preseason",
    "cup": "Emirates NBA Cup",
}

PHASE_SUMMARY_NAMES: Dict[str, str] = {
    "regular": "Regular Season",
    "preseason": "Preseason",
    "cup": "Emirates NBA Cup",
}


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    """Return an SSL context, optionally disabling certificate verification."""

    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def fetch_schedule(source_url: str, context: ssl.SSLContext) -> dict:
    """Download and decode the NBA schedule JSON document."""

    request = urllib.request.Request(source_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context) as response:
        return json.load(response)


def _parse_week_dates(games: Sequence[dict]) -> List[date]:
    dates: List[date] = []
    for game in games:
        when = game.get("gameDateTimeUTC") or game.get("gameDateUTC")
        if not when:
            continue
        dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
        dates.append(dt.date())
    return dates


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
            f"{first.strftime('%B')} {first.day} - "
            f"{last.strftime('%B')} {last.day}, {first.year}"
        )

    return (
        f"{first.strftime('%B')} {first.day}, {first.year} - "
        f"{last.strftime('%B')} {last.day}, {last.year}"
    )


def _wrap(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    return [f"{prefix}{line}" for line in wrapper.wrap(text)]


def _format_location(arena_city: str, arena_state: str) -> str:
    parts = [arena_city.strip() if arena_city else "", arena_state.strip() if arena_state else ""]
    return ", ".join(part for part in parts if part)


def _build_game_summary(week: int, game: dict, phase_label: str) -> Tuple[date, str]:
    when = game.get("gameDateTimeUTC") or game.get("gameDateUTC")
    dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
    game_date = dt.date()

    arena = game.get("arenaName") or "TBD Arena"
    location = _format_location(game.get("arenaCity", ""), game.get("arenaState", ""))

    summary_parts = [f"Week {week} matchup at {arena}"]
    if location:
        summary_parts[-1] += f" ({location})"
    summary_parts[-1] += "."
    summary_parts.append(
        f"Scheduled date: {game_date.strftime('%B')} {game_date.day}, {game_date.year}."
    )
    if phase_label:
        summary_parts.append(f"Competition: {phase_label}.")
    if game.get("isNeutral"):
        summary_parts.append("Neutral site game.")

    return game_date, " ".join(summary_parts)


def _phase_for_game(game: dict) -> str:
    label = game.get("gameLabel") or ""
    if label == "":
        return "regular"
    if label == "Preseason":
        return "preseason"
    if label == "Emirates NBA Cup":
        return "cup"
    return label.lower()


def collect_weeks(games: Iterable[dict], phases: Sequence[str]) -> Dict[int, List[dict]]:
    allowed_labels = {PHASE_LABELS[phase] for phase in phases if phase in PHASE_LABELS}

    weeks: Dict[int, List[dict]] = defaultdict(list)
    for game in games:
        game_label = game.get("gameLabel") or ""
        if game_label not in allowed_labels:
            continue
        week_number = game.get("weekNumber")
        if week_number is None:
            continue
        try:
            week = int(week_number)
        except (TypeError, ValueError):
            continue
        weeks[week].append(game)
    return weeks


def build_metadata(args: argparse.Namespace) -> dict:
    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)

    try:
        payload = fetch_schedule(args.source_url, context)
    except urllib.error.URLError as exc:
        if verify_ssl:
            verify_ssl = False
            context = build_ssl_context(False)
            payload = fetch_schedule(args.source_url, context)
            print(
                "Warning: SSL verification disabled due to fetch error:",
                exc,
                file=sys.stderr,
            )
        else:
            raise

    schedule = payload.get("leagueSchedule") or {}
    season_year = schedule.get("seasonYear")
    expected_season = f"{args.year}-{(args.year + 1) % 100:02d}"
    if season_year and season_year != expected_season:
        raise ValueError(
            f"Fetched schedule season '{season_year}' does not match expected '{expected_season}'."
        )

    all_games = [
        game
        for game_date in schedule.get("gameDates", [])
        for game in game_date.get("games", [])
    ]

    week_map = collect_weeks(all_games, args.phases)
    if not week_map:
        raise ValueError(
            "No games found for the requested phases; "
            "consider adding additional --phase arguments."
        )

    seasons = []
    for week in sorted(week_map):
        week_games = sorted(
            week_map[week],
            key=lambda g: (g.get("gameDateTimeUTC") or g.get("gameDateUTC"), g.get("gameSequence", 0)),
        )

        week_dates = _parse_week_dates(week_games)
        span_text = _format_date_range(week_dates) if week_dates else None
        phase_names = {_phase_for_game(game) for game in week_games}
        human_phase = ", ".join(
            sorted({PHASE_SUMMARY_NAMES.get(phase, phase.title()) for phase in phase_names})
        )
        game_count = len(week_games)

        if span_text:
            summary = (
                f"Week {week} covers {span_text} with {game_count} scheduled games"
            )
            if human_phase:
                summary += f" ({human_phase})."
            else:
                summary += "."
        else:
            summary = f"Week {week} currently has no scheduled games."

        episodes = []
        for index, game in enumerate(week_games, start=1):
            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})
            home_name = home.get("teamName") or home.get("teamTricode") or "Home Team"
            away_name = away.get("teamName") or away.get("teamTricode") or "Away Team"

            game_date, summary_text = _build_game_summary(
                week, game, game.get("gameLabel") or ""
            )

            episodes.append(
                {
                    "index": index,
                    "title": f"{away_name} at {home_name}",
                    "originally_available": game_date.isoformat(),
                    "summary": summary_text,
                }
            )

        seasons.append(
            {
                "number": week,
                "title": f"Week {week}",
                "sort_title": f"{week:02d}_Week {week}",
                "summary": summary,
                "episodes": episodes,
            }
        )

    year_next = args.year + 1
    season_slug = f"{args.year}-{year_next % 100:02d}"
    year_next_short = year_next % 100

    show_id = args.show_id or f"NBA {season_slug}"
    title = args.title or show_id
    sort_title = args.sort_title or title

    poster_url = args.poster_url.format(
        year=args.year,
        year_next=year_next,
        year_next_short=year_next_short,
        season=season_slug,
    )
    background_url = args.background_url.format(
        year=args.year,
        year_next=year_next,
        year_next_short=year_next_short,
        season=season_slug,
    )
    summary_text = args.summary.format(
        year=args.year,
        year_next=year_next,
        year_next_short=year_next_short,
        season=season_slug,
    )

    return {
        "show_id": show_id,
        "title": title,
        "sort_title": sort_title,
        "poster_url": poster_url,
        "background_url": background_url,
        "summary": summary_text,
        "seasons": seasons,
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


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an NBA season metadata YAML file for Sports Organizer.",
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Season start year (e.g. 2025 for the 2025-26 campaign).",
    )
    parser.add_argument(
        "--phase",
        dest="phases",
        choices=sorted(PHASE_LABELS.keys()),
        action="append",
        default=None,
        help=(
            "Competition phase to include (default: regular). "
            "Specify multiple times to include extras like preseason or cup."
        ),
    )
    parser.add_argument(
        "--title",
        help="Custom show title (defaults to 'NBA <year>-<year+1>').",
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
        default=(
            "https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
            "nba-{season}/poster.jpg"
        ),
        help="Poster URL template (supports {year}, {year_next}, {season}).",
    )
    parser.add_argument(
        "--background-url",
        default=(
            "https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/"
            "nba-{season}/background.jpg"
        ),
        help="Background URL template (supports {year}, {year_next}, {season}).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {season} NBA season spans league weeks packed with matchups "
            "across North America and international venues. This metadata groups games "
            "by NBA week so Sports Organizer can match and rename recordings reliably."
        ),
        help="Show summary text (supports {year}, {year_next}, {season}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Destination path for the generated YAML (defaults to "
            "metadata-files/nba-<year>-<year+1>.yaml)."
        ),
    )
    parser.add_argument(
        "--source-url",
        default=DEFAULT_SOURCE_URL,
        help="Override the NBA schedule JSON endpoint if needed.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if not args.phases:
        args.phases = ["regular"]

    metadata = build_metadata(args)
    yaml_text = render_yaml(metadata)

    year_next = args.year + 1
    season_slug = f"{args.year}-{year_next % 100:02d}"
    output_path = args.output
    if output_path is None:
        output_path = Path("metadata-files") / f"nba-{season_slug}.yaml"
    else:
        output_path = output_path.expanduser()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Generated metadata written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())



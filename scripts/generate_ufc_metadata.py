#!/usr/bin/env python3
"""Generate UFC metadata YAML files using TheSportsDB rounds feed.

This script mirrors the other generators in this repository. Each SportsDB
round becomes a season entry under the ``UFC <season>`` show, with episodes
representing the early prelims/prelims/main card blocks referenced in the API
payload. Fight Night cards default to two episodes (Prelims + Main Card) while
numbered PPVs include Early Prelims as a third episode.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


API_URL = (
    "https://www.thesportsdb.com/api/v1/json/{api_key}/eventsseason.php"
    "?id={league_id}&s={season}"
)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

CARD_LAYOUTS = {
    "ppv": ["early", "prelim", "main"],
    "fight_night": ["prelim", "main"],
}

CARD_LABELS = {
    "early": "Early Prelims",
    "prelim": "Prelims",
    "main": "Main Card",
}


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def fetch_season_events(
    season: str,
    league_id: int,
    api_key: str,
    context: ssl.SSLContext,
) -> List[dict]:
    url = API_URL.format(api_key=api_key, league_id=league_id, season=season)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context) as response:
        payload = json.load(response)

    events = payload.get("events")
    if not events:
        raise RuntimeError(
            f"No events returned for league {league_id} season {season} "
            f"(API key {api_key})."
        )
    return events


def _to_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _date_from_event(event: dict) -> date:
    if event.get("dateEvent"):
        parsed = _to_date(event["dateEvent"])
        if parsed:
            return parsed
    if event.get("dateEventLocal"):
        parsed = _to_date(event["dateEventLocal"])
        if parsed:
            return parsed
    timestamp = event.get("strTimestamp")
    if timestamp:
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date()
        except ValueError:
            pass
    # Fallback to today if the feed is missing dates.
    return datetime.utcnow().date()  # type: ignore[arg-type]


def classify_event(str_event: str) -> str:
    lowered = (str_event or "").lower()
    fight_night_tokens = [
        "fight night",
        "ufc on espn",
        "ufc on abc",
        "ufc on fox",
        "ufc on fuel",
        "ufc on fx",
    ]
    if any(token in lowered for token in fight_night_tokens):
        return "fight_night"
    return "ppv"


def extract_event_number(str_event: str) -> Optional[str]:
    match = re.search(r"\b(\d{3,})\b", str_event or "")
    if match:
        return match.group(1)
    return None


def parse_result_sections(result_text: Optional[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {"early": [], "prelim": [], "main": []}
    if not result_text:
        return sections

    normalized = result_text.replace("\r\n", "\n")
    current_lines: List[str] = []
    current_key = "main"

    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if "\t" not in line and line.lower().count("weight class") == 0:
            # Treat this as a section header.
            lower = line.lower()
            if "early" in lower:
                current_key = "early"
            elif "prelim" in lower:
                current_key = "prelim"
            elif "main" in lower or "fight card" in lower:
                current_key = "main"
            else:
                current_key = "main"
            current_lines = sections[current_key]
            continue

        if not sections.get(current_key):
            sections.setdefault(current_key, [])
        sections[current_key].append(line)

    return sections


def summarise_fights(lines: Sequence[str], limit: int = 3) -> str:
    if not lines:
        return ""

    blurbs = []
    for raw in lines:
        columns = [col for col in raw.split("\t") if col]
        if not columns:
            continue
        weight = columns[0]
        if len(columns) >= 4 and columns[2].lower().startswith("def"):
            winner = columns[1]
            loser = columns[3]
            detail_bits = []
            if len(columns) >= 5:
                detail_bits.append(columns[4])
            if len(columns) >= 6:
                detail_bits.append(f"R{columns[5]}")
            if len(columns) >= 7:
                detail_bits.append(columns[6])
            detail = ", ".join(bit for bit in detail_bits if bit)
            if detail:
                blurbs.append(f"{weight}: {winner} def. {loser} ({detail})")
            else:
                blurbs.append(f"{weight}: {winner} def. {loser}")
        else:
            blurbs.append(f"{weight}: {' '.join(columns[1:])}")
        if len(blurbs) >= limit:
            break

    if not blurbs:
        return ""
    return "Notable bouts: " + "; ".join(blurbs) + "."


def _wrap_lines(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    wrapped = wrapper.wrap(text) or [""]
    return [f"{prefix}{line}" for line in wrapped]


def build_metadata(args: argparse.Namespace) -> dict:
    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)
    try:
        events = fetch_season_events(args.season, args.league_id, args.api_key, context)
    except urllib.error.URLError as exc:
        if verify_ssl:
            print(
                "SSL verification failed, retrying without verification...",
                file=sys.stderr,
            )
            context = build_ssl_context(False)
            events = fetch_season_events(args.season, args.league_id, args.api_key, context)
        else:
            raise RuntimeError(f"Failed to fetch season data: {exc}") from exc

    events_by_round: Dict[int, dict] = {}
    for event in events:
        try:
            round_number = int(event.get("intRound") or 0)
        except ValueError:
            continue
        if round_number == 0:
            continue
        events_by_round[round_number] = event

    seasons = []
    for round_number in sorted(events_by_round):
        event = events_by_round[round_number]
        event_title = event.get("strEvent") or f"Round {round_number}"
        event_type = classify_event(event_title)
        card_layout = CARD_LAYOUTS[event_type]
        card_sections = parse_result_sections(event.get("strResult"))
        event_date = _date_from_event(event)
        event_date_str = event_date.isoformat()
        venue = event.get("strVenue") or "TBD Venue"
        location = ", ".join(
            bit
            for bit in [
                event.get("strCity"),
                event.get("strCountry"),
            ]
            if bit
        )
        description = (event.get("strDescriptionEN") or "").strip()
        if not description:
            description = (
                f"{event_title} is scheduled for {event_date.strftime('%B %d, %Y')} "
                f"at {venue}{f' in {location}' if location else ''}."
            )

        season_poster = None
        event_token = extract_event_number(event_title)
        if event_token and args.season_poster_template:
            season_poster = args.season_poster_template.format(event_token=event_token)
        elif args.season_poster_fallback:
            season_poster = args.season_poster_fallback

        episodes = []
        for index, card_key in enumerate(card_layout, start=1):
            card_lines = card_sections.get(card_key, [])
            fights_summary = summarise_fights(card_lines)
            episode_title = CARD_LABELS[card_key]
            episode_summary_parts = [
                f"{episode_title} for {event_title} hosted at {venue}"
                f"{f' ({location})' if location else ''} on "
                f"{event_date.strftime('%B %d, %Y')}."
            ]
            if fights_summary:
                episode_summary_parts.append(fights_summary)
            else:
                episode_summary_parts.append(
                    "Detailed bout listings are pending in the SportsDB feed."
                )
            episodes.append(
                {
                    "index": index,
                    "title": f"{episode_title}",
                    "originally_available": event_date_str,
                    "summary": " ".join(episode_summary_parts),
                }
            )

        seasons.append(
            {
                "number": round_number,
                "title": event_title,
                "sort_title": f"{round_number:03d}_{event_title}",
                "url_poster": season_poster,
                "summary": description,
                "episodes": episodes,
            }
        )

    show_id = args.show_id or args.title
    metadata = {
        "show_id": show_id,
        "title": args.title,
        "sort_title": args.sort_title or args.title,
        "poster_url": args.poster_url,
        "background_url": args.background_url,
        "summary": args.summary,
        "seasons": seasons,
    }
    return metadata


def render_yaml(metadata: dict) -> str:
    lines = ["metadata:"]
    lines.append(f"  {metadata['show_id']}:")
    lines.append(f"    title: {metadata['title']}")
    lines.append(f"    sort_title: {metadata['sort_title']}")
    if metadata.get("poster_url"):
        lines.append(f"    url_poster: {metadata['poster_url']}")
    if metadata.get("background_url"):
        lines.append(f"    url_background: {metadata['background_url']}")
    lines.append("    summary: >")
    lines.extend(_wrap_lines("      ", metadata["summary"]))
    lines.append("    seasons:")

    for season in metadata["seasons"]:
        lines.append(f"      {season['number']}:")
        lines.append(f"        title: {season['title']}")
        lines.append(f"        sort_title: {season['sort_title']}")
        if season.get("url_poster"):
            lines.append(f"        url_poster: {season['url_poster']}")
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


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate UFC metadata YAML using TheSportsDB rounds API.",
    )
    parser.add_argument(
        "--season",
        default="2025",
        help="Season identifier passed to TheSportsDB (e.g. 2025).",
    )
    parser.add_argument(
        "--league-id",
        type=int,
        default=4443,
        help="TheSportsDB league/competition ID for UFC.",
    )
    parser.add_argument(
        "--api-key",
        default="123",
        help="TheSportsDB API key (free-tier default is 123).",
    )
    parser.add_argument(
        "--title",
        default="UFC 2025",
        help="Show title used in the metadata tree.",
    )
    parser.add_argument(
        "--sort-title",
        default=None,
        help="Optional sort title for the show (defaults to title).",
    )
    parser.add_argument(
        "--show-id",
        default="UFC 2025",
        help="Metadata key used under the top-level 'metadata:' block.",
    )
    parser.add_argument(
        "--poster-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/ufc/poster.jpg",
        help="Show-level poster URL.",
    )
    parser.add_argument(
        "--background-url",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/ufc/background.jpg",
        help="Show-level background URL.",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The 2025 UFC calendar spans numbered pay-per-view spectacles and weekly "
            "Fight Night cards around the globe. Each SportsDB round is grouped here "
            "so recordings for Early Prelims, Prelims and Main Card blocks can be "
            "matched and renamed automatically."
        ),
        help="Overall show summary text.",
    )
    parser.add_argument(
        "--season-poster-template",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/ufc/{event_token}/poster.jpg",
        help=(
            "Format string for season posters; {event_token} is replaced with the "
            "numeric UFC event extracted from the title. Leave empty to skip."
        ),
    )
    parser.add_argument(
        "--season-poster-fallback",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/ufc/poster.jpg",
        help="Fallback poster URL when an event number is unavailable.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML "
        "(defaults to metadata-files/ufc-<season>.yaml).",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    metadata = build_metadata(args)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        output_path = Path("metadata-files") / f"ufc-{args.season}.yaml"
    output_path = output_path.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote UFC metadata to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


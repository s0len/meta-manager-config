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
import time
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sportsdb import SportsDBSettings, load_sportsdb_settings
from sportsdb_helpers import extract_events, fetch_season_description_text


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

SPORTSDB_DEFAULTS = load_sportsdb_settings()
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _build_headers(sportsdb: SportsDBSettings) -> Dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    headers.update(sportsdb.auth_headers)
    return headers


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def _fetch_json(
    url: str,
    context: ssl.SSLContext,
    rate_limiter: Optional[object],
    retries: int,
    retry_backoff: float,
    headers: Optional[Dict[str, str]] = None,
) -> dict:
    attempt = 0
    while True:
        request_headers = {"User-Agent": USER_AGENT}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(url, headers=request_headers)
        try:
            with urllib.request.urlopen(request, context=context) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in RETRYABLE_STATUS_CODES and attempt < retries:
                delay = retry_backoff * (2**attempt)
                time.sleep(delay)
                attempt += 1
                continue
            raise


def fetch_event_detail(
    event_id: Optional[str],
    sportsdb: SportsDBSettings,
    context: ssl.SSLContext,
) -> Optional[dict]:
    if not event_id:
        return None
    url = sportsdb.event_detail_url(event_id)
    try:
        payload = _fetch_json(
            url,
            context,
            rate_limiter=None,
            retries=0,
            retry_backoff=0.0,
            headers=_build_headers(sportsdb),
        )
    except urllib.error.URLError as exc:
        print(f"Warning: failed to fetch details for event {event_id}: {exc}", file=sys.stderr)
        return None
    entries = (
        payload.get("events")
        or payload.get("event")
        or payload.get("results")
        or []
    )
    return entries[0] if entries else None


def fetch_season_events(
    season: str,
    league_id: int,
    sportsdb: SportsDBSettings,
    context: ssl.SSLContext,
) -> List[dict]:
    url = sportsdb.season_url(league_id, season)
    payload = _fetch_json(
        url,
        context,
        rate_limiter=None,
        retries=0,
        retry_backoff=0.0,
        headers=_build_headers(sportsdb),
    )

    events = extract_events(payload)
    if not events:
        raise RuntimeError(
            f"No events returned for league {league_id} season {season} "
            f"(API {sportsdb.api_version})."
        )
    return events


def fetch_round_event(
    season: str,
    league_id: int,
    round_number: int,
    sportsdb: SportsDBSettings,
    context: ssl.SSLContext,
) -> Optional[dict]:
    round_url = sportsdb.round_url(league_id, season, round_number)
    target_url = round_url or sportsdb.season_url(league_id, season)
    payload = _fetch_json(
        target_url,
        context,
        rate_limiter=None,
        retries=0,
        retry_backoff=0.0,
        headers=_build_headers(sportsdb),
    )
    events = extract_events(payload)
    if round_url:
        return events[0] if events else None
    for event in events:
        number = _round_number_from_event(event)
        if number == round_number:
            return event
    return None


def _round_number_from_event(event: dict) -> Optional[int]:
    for key in ("intRound", "strRound"):
        value = event.get(key)
        if value in (None, "", "0"):
            continue
        try:
            return int(value)
        except ValueError:
            continue
    return None


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


def _event_type_label(event_type: str) -> str:
    return "numbered pay-per-view" if event_type == "ppv" else "Fight Night"


def _fallback_round_summary(
    *,
    event_title: str,
    event_date: date,
    venue: str,
    location: str,
    event_type: str,
    card_sections: Dict[str, List[str]],
) -> str:
    date_text = event_date.strftime("%B %d, %Y")
    venue_text = f"{venue}{f' ({location})' if location else ''}"
    summary_parts = [
        f"{event_title} anchors the UFC {_event_type_label(event_type)} slate on {date_text} at {venue_text}."
    ]
    broadcast_blocks = [
        label
        for key, label in (
            ("early", "Early Prelims"),
            ("prelim", "Prelims"),
            ("main", "Main Card"),
        )
        if card_sections.get(key)
    ]
    if broadcast_blocks:
        summary_parts.append(
            "Broadcast blocks tracked for automation: "
            + ", ".join(broadcast_blocks)
            + "."
        )
    headline = (
        summarise_fights(card_sections.get("main") or [], limit=3)
        or summarise_fights(card_sections.get("prelim") or [], limit=3)
        or summarise_fights(card_sections.get("early") or [], limit=3)
    )
    if headline:
        summary_parts.append(headline)
    return " ".join(summary_parts)


DETAIL_COPY_FIELDS = [
    "strDescriptionEN",
    "strResult",
    "strVenue",
    "strCity",
    "strCountry",
    "strPoster",
    "strThumb",
    "strEvent",
    "strTVStation",
]


def _merge_event_details(base: dict, detail: dict) -> None:
    for field in DETAIL_COPY_FIELDS:
        if not base.get(field) and detail.get(field):
            base[field] = detail[field]
    # Always prefer precise date if provided.
    if detail.get("dateEvent"):
        base["dateEvent"] = detail["dateEvent"]
    if detail.get("strTimeLocal"):
        base["strTimeLocal"] = detail["strTimeLocal"]


def _wrap_lines(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    wrapped = wrapper.wrap(text) or [""]
    return [f"{prefix}{line}" for line in wrapped]


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", value)
    cleaned = cleaned.strip().lower()
    cleaned = re.sub(r"[\s_-]+", "-", cleaned)
    return cleaned or "episode"


def build_asset_url(base: str, relative_path: str) -> str:
    base_clean = base.rstrip("/")
    rel_clean = relative_path.lstrip("/")
    if not base_clean:
        return rel_clean
    return f"{base_clean}/{rel_clean}"


def ensure_asset_download(
    source_url: Optional[str],
    dest_path: Path,
    context: ssl.SSLContext,
) -> bool:
    if not source_url:
        return False
    if dest_path.exists():
        return True
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(source_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, context=context) as response:
            dest_path.write_bytes(response.read())
        return True
    except urllib.error.URLError as exc:
        print(f"Warning: failed to download asset {source_url}: {exc}", file=sys.stderr)
        return False


def build_metadata(args: argparse.Namespace, sportsdb: SportsDBSettings) -> dict:
    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)
    try:
        events = fetch_season_events(args.season, args.league_id, sportsdb, context)
    except urllib.error.URLError as exc:
        if verify_ssl:
            print(
                "SSL verification failed, retrying without verification...",
                file=sys.stderr,
            )
            context = build_ssl_context(False)
            events = fetch_season_events(args.season, args.league_id, sportsdb, context)
        else:
            raise RuntimeError(f"Failed to fetch season data: {exc}") from exc

    season_summary: Optional[str] = None
    if not args.skip_season_description_fetch:
        try:
            season_summary = fetch_season_description_text(
                season=args.season,
                league_id=args.league_id,
                sportsdb=sportsdb,
                fetch_json=_fetch_json,
                context=context,
                rate_limiter=None,
                retries=0,
                retry_backoff=0.0,
            )
        except urllib.error.URLError as exc:
            if verify_ssl:
                print(
                    "Season description fetch failed with SSL error, retrying insecure...",
                    file=sys.stderr,
                )
                context = build_ssl_context(False)
                season_summary = fetch_season_description_text(
                    season=args.season,
                    league_id=args.league_id,
                    sportsdb=sportsdb,
                    fetch_json=_fetch_json,
                    context=context,
                    rate_limiter=None,
                    retries=0,
                    retry_backoff=0.0,
                )
            else:
                print(
                    f"Warning: failed to fetch season description: {exc}",
                    file=sys.stderr,
                )

    events_by_round: Dict[int, dict] = {}
    for event in events:
        try:
            round_number = int(event.get("intRound") or 0)
        except ValueError:
            continue
        if round_number == 0:
            continue
        events_by_round[round_number] = event

    if not args.skip_round_fill and args.round_stop >= args.round_start:
        for round_number in range(args.round_start, args.round_stop + 1):
            if round_number in events_by_round:
                continue
            try:
                round_event = fetch_round_event(
                    args.season,
                    args.league_id,
                    round_number,
                    sportsdb,
                    context,
                )
            except urllib.error.URLError as exc:
                if verify_ssl:
                    print(
                        f"Round fetch failed with SSL error, retrying insecure for round {round_number}...",
                        file=sys.stderr,
                    )
                    context = build_ssl_context(False)
                    round_event = fetch_round_event(
                        args.season,
                        args.league_id,
                        round_number,
                        sportsdb,
                        context,
                    )
                else:
                    raise RuntimeError(
                        f"Failed to fetch round {round_number}: {exc}"
                    ) from exc

            if round_event:
                events_by_round[round_number] = round_event
            if args.round_delay > 0 and round_number < args.round_stop:
                time.sleep(args.round_delay)

    if not args.skip_event_detail_fetch:
        for round_number, event in events_by_round.items():
            detail = fetch_event_detail(event.get("idEvent"), sportsdb, context)
            if detail:
                _merge_event_details(event, detail)

    assets_root = args.assets_root
    download_assets = not args.skip_asset_download

    first_round = min(events_by_round) if events_by_round else None
    first_event = events_by_round[first_round] if first_round else None

    if download_assets and first_event and args.poster_rel:
        ensure_asset_download(
            first_event.get("strPoster"),
            assets_root / args.poster_rel,
            context,
        )
    if download_assets and first_event and args.background_rel:
        ensure_asset_download(
            first_event.get("strFanart"),
            assets_root / args.background_rel,
            context,
        )

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
            description = _fallback_round_summary(
                event_title=event_title,
                event_date=event_date,
                venue=venue,
                location=location,
                event_type=event_type,
                card_sections=card_sections,
            )

        event_token = extract_event_number(event_title)
        round_token = event_token or f"{round_number:03d}"
        season_number = round_number
        season_poster = None
        if args.season_poster_template:
            season_poster_rel = args.season_poster_template.format(
                season=args.season,
                round=round_token,
                event_token=round_token,
                season_number=season_number,
            )
            season_poster_path = assets_root / season_poster_rel
            if download_assets:
                ensure_asset_download(event.get("strPoster"), season_poster_path, context)
            season_poster = build_asset_url(args.asset_url_base, season_poster_rel)
        elif args.season_poster_fallback:
            fallback_rel = args.season_poster_fallback.format(
                season=args.season,
                round=round_token,
                event_token=round_token,
                season_number=season_number,
            )
            season_poster = build_asset_url(args.asset_url_base, fallback_rel)

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
            title_slug = slugify(episode_title)
            episode_poster_url = None
            if args.episode_poster_template:
                episode_poster_rel = args.episode_poster_template.format(
                    season=args.season,
                    round=round_token,
                    event_token=round_token,
                    season_number=season_number,
                    episode_title=title_slug,
                )
                episode_poster_path = assets_root / episode_poster_rel
                episode_poster_url = build_asset_url(
                    args.asset_url_base, episode_poster_rel
                )

                if download_assets and card_key == "main":
                    ensure_asset_download(
                        event.get("strThumb"), episode_poster_path, context
                    )

            episodes.append(
                {
                    "index": index,
                    "title": f"{episode_title}",
                    "originally_available": event_date_str,
                    "summary": " ".join(episode_summary_parts),
                    "url_poster": episode_poster_url,
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
    show_summary = args.summary
    if season_summary:
        if args.season_description_mode == "replace":
            show_summary = season_summary
        else:
            show_summary = f"{args.summary}\n\n{season_summary}"
    metadata = {
        "show_id": show_id,
        "title": args.title,
        "sort_title": args.sort_title or args.title,
        "poster_url": args.poster_url,
        "background_url": args.background_url,
        "summary": show_summary,
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
            if episode.get("url_poster"):
                lines.append(f"            url_poster: {episode['url_poster']}")
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
        default=SPORTSDB_DEFAULTS.api_key,
        help=(
            "TheSportsDB API key (defaults to SPORTSDB_API_KEY from .env or 123 "
            "when unset)."
        ),
    )
    parser.add_argument(
        "--api-version",
        default=SPORTSDB_DEFAULTS.api_version,
        help="TheSportsDB API version to target (e.g. v1 or v2).",
    )
    parser.add_argument(
        "--title",
        default="UFC {season}",
        help="Show title used in the metadata tree.",
    )
    parser.add_argument(
        "--sort-title",
        default=None,
        help="Optional sort title for the show (defaults to title).",
    )
    parser.add_argument(
        "--show-id",
        default="UFC {season}",
        help="Metadata key used under the top-level 'metadata:' block.",
    )
    parser.add_argument(
        "--poster-url",
        default="posters/ufc/{season}/poster.jpg",
        help="Show-level poster path or URL (supports {season}).",
    )
    parser.add_argument(
        "--background-url",
        default="posters/ufc/{season}/background.jpg",
        help="Show-level background path or URL (supports {season}).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {season} UFC calendar spans numbered pay-per-view spectacles and weekly "
            "Fight Night cards around the globe. Each SportsDB round is grouped here "
            "so recordings for Early Prelims, Prelims and Main Card blocks can be "
            "matched and renamed automatically."
        ),
        help="Overall show summary text (supports {season}).",
    )
    parser.add_argument(
        "--asset-url-base",
        default="https://raw.githubusercontent.com/s0len/meta-manager-config/main",
        help="Base URL prepended to relative poster paths.",
    )
    parser.add_argument(
        "--assets-root",
        default=".",
        help="Local root directory where poster assets are stored/downloaded.",
    )
    parser.add_argument(
        "--season-poster-template",
        default="posters/ufc/{season}/s{season_number}/poster.jpg",
        help=(
            "Relative path template for season posters; {season_number} matches the "
            "season entry (1..n). Leave empty to skip."
        ),
    )
    parser.add_argument(
        "--season-poster-fallback",
        default="",
        help="Fallback relative poster path when SportsDB lacks artwork.",
    )
    parser.add_argument(
        "--episode-poster-template",
        default="posters/ufc/{season}/s{season_number}/{episode_title}.jpg",
        help=(
            "Relative path template for per-episode posters. Supports {season}, "
            "{season_number} and {episode_title} (slug). Leave empty to skip."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML "
        "(defaults to metadata/ufc/{season}.yaml).",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification.",
    )
    parser.add_argument(
        "--round-start",
        type=int,
        default=1,
        help="First round number to try when filling missing events (default: 1).",
    )
    parser.add_argument(
        "--round-stop",
        type=int,
        default=60,
        help="Last round number to try when filling missing events (default: 60).",
    )
    parser.add_argument(
        "--round-delay",
        type=float,
        default=2.0,
        help="Seconds to wait between round fetches (helps avoid API rate limits).",
    )
    parser.add_argument(
        "--skip-round-fill",
        action="store_true",
        help="Disable per-round fetches (use only eventsseason.php).",
    )
    parser.add_argument(
        "--skip-season-description-fetch",
        action="store_true",
        help="Disable fetching show-level summaries from TheSportsDB season descriptions.",
    )
    parser.add_argument(
        "--season-description-mode",
        choices=("append", "replace"),
        default="replace",
        help=(
            "When SportsDB season descriptions are available, either append them after "
            "the CLI summary (append) or replace the CLI summary entirely (replace)."
        ),
    )
    parser.add_argument(
        "--skip-event-detail-fetch",
        action="store_true",
        help="Skip per-event detail lookups (useful if TheSportsDB data already includes rich descriptions).",
    )
    parser.add_argument(
        "--skip-asset-download",
        action="store_true",
        help="Skip downloading SportsDB artwork for seasons/episodes.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    sportsdb = SPORTSDB_DEFAULTS.with_overrides(
        api_key=args.api_key, api_version=args.api_version
    )
    args.assets_root = Path(args.assets_root).expanduser()

    def resolve_asset(value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not value:
            return None, None
        formatted = value.format(season=args.season)
        if formatted.lower().startswith(("http://", "https://")):
            return formatted, None
        return build_asset_url(args.asset_url_base, formatted), formatted

    args.poster_url, args.poster_rel = resolve_asset(args.poster_url)
    args.background_url, args.background_rel = resolve_asset(args.background_url)

    if args.summary:
        args.summary = args.summary.format(season=args.season)
    if args.title:
        args.title = args.title.format(season=args.season)
    if args.sort_title:
        args.sort_title = args.sort_title.format(season=args.season)
    if args.show_id:
        args.show_id = args.show_id.format(season=args.season)
    metadata = build_metadata(args, sportsdb)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        output_path = Path("metadata") / f"ufc/{args.season}.yaml"
    output_path = output_path.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote UFC metadata to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


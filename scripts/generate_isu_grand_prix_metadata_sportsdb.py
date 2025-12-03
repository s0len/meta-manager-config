#!/usr/bin/env python3
"""Generate ISU Grand Prix metadata YAML using TheSportsDB rounds feed.

This script mirrors :mod:`generate_ufc_metadata` but targets the ISU Grand Prix
figure skating circuit (``league_id 5753``). Each SportsDB ``intRound`` becomes
a Grand Prix stop (season entry) and every listed broadcast block is emitted as
an episode with venue/date context for automation.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import textwrap
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sportsdb import (
    SportsDBSettings,
    default_request_interval,
    load_sportsdb_settings,
)
from sportsdb_helpers import join_location, location_suffix
from sportsdb_helpers import extract_events, fetch_season_description_text

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

DEFAULT_MATCHWEEK_START = 1
DEFAULT_MATCHWEEK_STOP = 12
DEFAULT_ROUND_LABEL = "Grand Prix stop"
DEFAULT_ROUND_TITLE_TEMPLATE = "{event_base}"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

SPORTSDB_DEFAULTS = load_sportsdb_settings()


class RateLimiter:
    def __init__(self, interval: float) -> None:
        self.interval = max(0.0, interval)
        self._next_time = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        now = time.monotonic()
        if now < self._next_time:
            time.sleep(self._next_time - now)
        self._next_time = time.monotonic() + self.interval


def _fetch_json(
    url: str,
    context: ssl.SSLContext,
    rate_limiter: Optional[RateLimiter],
    retries: int,
    retry_backoff: float,
    headers: Optional[Dict[str, str]] = None,
) -> dict:
    attempt = 0
    while True:
        if rate_limiter:
            rate_limiter.wait()
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


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", value)
    cleaned = cleaned.strip().lower()
    cleaned = re.sub(r"[\s_-]+", "-", cleaned)
    return cleaned or "session"


SESSION_DESCRIPTOR_SEQUENCES = [
    ("pairs",),
    ("women",),
    ("men",),
    ("ice", "dance"),
    ("rhythm", "dance"),
    ("free", "dance"),
    ("free", "skating"),
    ("short", "program"),
    ("exhibition",),
    ("gala",),
    ("practice",),
    ("warm",),
    ("opening",),
    ("closing",),
    ("awards",),
    ("ceremony",),
]


def _tokenize_title(value: str) -> List[str]:
    return [token for token in re.split(r"\s+", value.strip()) if token]


def _find_descriptor_index(tokens: Sequence[str]) -> Optional[int]:
    lowered = [token.lower() for token in tokens]
    for index in range(len(tokens)):
        for sequence in SESSION_DESCRIPTOR_SEQUENCES:
            if len(sequence) + index > len(tokens):
                continue
            if lowered[index : index + len(sequence)] == list(sequence):
                return index
    return None


def _strip_session_descriptor(title: str) -> str:
    tokens = _tokenize_title(title)
    if not tokens:
        return ""
    descriptor_index = _find_descriptor_index(tokens)
    if descriptor_index is None or descriptor_index == 0:
        return ""
    return " ".join(tokens[:descriptor_index]).strip()


def _longest_common_word_prefix(titles: Sequence[str]) -> str:
    if not titles:
        return ""
    tokenized = [_tokenize_title(title) for title in titles if title.strip()]
    if not tokenized:
        return ""
    min_length = min(len(tokens) for tokens in tokenized)
    prefix: List[str] = []
    for idx in range(min_length):
        candidate = tokenized[0][idx]
        if all(tokens[idx].lower() == candidate.lower() for tokens in tokenized):
            prefix.append(tokenized[0][idx])
        else:
            break
    return " ".join(prefix).strip()


def _longest_common_word_suffix(titles: Sequence[str]) -> str:
    if not titles:
        return ""
    tokenized = [_tokenize_title(title) for title in titles if title.strip()]
    if not tokenized:
        return ""
    reversed_tokens = [list(reversed(tokens)) for tokens in tokenized]
    min_length = min(len(tokens) for tokens in reversed_tokens)
    suffix_reversed: List[str] = []
    for idx in range(min_length):
        candidate = reversed_tokens[0][idx]
        if all(tokens[idx].lower() == candidate.lower() for tokens in reversed_tokens):
            suffix_reversed.append(reversed_tokens[0][idx])
        else:
            break
    return " ".join(reversed(suffix_reversed)).strip()


def _session_title_from_event(event: dict, fallback_index: int) -> str:
    for field in ("strEvent", "strEventAlternate", "strFilename"):
        value = event.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"Session {fallback_index}"


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
    rate_limiter: Optional[RateLimiter],
    retries: int,
    retry_backoff: float,
) -> bool:
    if not source_url:
        return False
    if dest_path.exists():
        return True
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    attempt = 0
    while True:
        if rate_limiter:
            rate_limiter.wait()
        request = urllib.request.Request(source_url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, context=context) as response:
                dest_path.write_bytes(response.read())
            return True
        except urllib.error.HTTPError as exc:
            if exc.code in RETRYABLE_STATUS_CODES and attempt < retries:
                delay = retry_backoff * (2**attempt)
                time.sleep(delay)
                attempt += 1
                continue
            print(f"Warning: failed to download asset {source_url}: {exc}", file=sys.stderr)
            return False
        except urllib.error.URLError as exc:
            print(f"Warning: failed to download asset {source_url}: {exc}", file=sys.stderr)
            return False


def build_ssl_context(verify: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


def fetch_season_events(
    season: str,
    league_id: int,
    sportsdb: SportsDBSettings,
    context: ssl.SSLContext,
    rate_limiter: Optional[RateLimiter],
    retries: int,
    retry_backoff: float,
) -> List[dict]:
    url = sportsdb.season_url(league_id, season)
    payload = _fetch_json(
        url,
        context,
        rate_limiter,
        retries,
        retry_backoff,
        headers=sportsdb.auth_headers,
    )

    events = extract_events(payload)
    if not events:
        message = payload.get("Message") or payload.get("message")
        raise RuntimeError(
            f"No events returned for league {league_id} season {season} "
            f"(API {sportsdb.api_version})."
            f"{f' Details: {message}' if message else ''}"
        )
    return events


def fetch_round_events(
    season: str,
    league_id: int,
    round_number: int,
    sportsdb: SportsDBSettings,
    context: ssl.SSLContext,
    rate_limiter: Optional[RateLimiter],
    retries: int,
    retry_backoff: float,
) -> List[dict]:
    round_url = sportsdb.round_url(league_id, season, round_number)
    target_url = round_url or sportsdb.season_url(league_id, season)
    payload = _fetch_json(
        target_url,
        context,
        rate_limiter,
        retries,
        retry_backoff,
        headers=sportsdb.auth_headers,
    )
    events = extract_events(payload)
    if round_url:
        return events
    return [
        event
        for event in events
        if _round_number_from_event(event) == round_number
    ]


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
    return datetime.utcnow().date()  # type: ignore[arg-type]


def _wrap_lines(prefix: str, text: str, width: int = 100) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    wrapped = wrapper.wrap(text) or [""]
    return [f"{prefix}{line}" for line in wrapped]


def _round_number_from_event(event: dict) -> Optional[int]:
    candidates = [event.get("intRound"), event.get("strRound")]
    for value in candidates:
        if value in (None, "", "0"):
            continue
        try:
            return int(value)
        except ValueError:
            continue
    return None


def _format_date_range(dates: Iterable[date]) -> Optional[str]:
    ordered = sorted(dates)
    if not ordered:
        return None
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


def _session_sort_key(event: dict) -> Tuple[date, str]:
    event_date = _date_from_event(event)
    name = (
        event.get("strEvent")
        or event.get("strEventAlternate")
        or event.get("strFilename")
        or ""
    ).lower()
    return (event_date, name)


def _extract_event_base(event: dict) -> str:
    fields = ("strEvent", "strEventAlternate", "strFilename")
    for field in fields:
        raw = event.get(field)
        if not raw:
            continue
        for separator in (" - ", " – ", ":"):
            if separator in raw:
                return raw.split(separator)[0].strip()
        return raw.strip()
    return ""


def _derive_round_title(
    fixtures: Sequence[dict],
    *,
    session_titles: Sequence[str],
    round_number: int,
    round_label: str,
    round_title_template: Optional[str],
    season: str,
) -> str:
    first = fixtures[0] if fixtures else {}
    base_name = ""
    if session_titles:
        trimmed_counts: Counter[str] = Counter()
        for title in session_titles:
            stripped = _strip_session_descriptor(title)
            if stripped:
                trimmed_counts[stripped] += 1
        if trimmed_counts:
            base_name = max(
                trimmed_counts.items(), key=lambda item: (item[1], len(item[0]))
            )[0]
        if not base_name:
            base_name = _longest_common_word_prefix(session_titles)
        if not base_name:
            base_name = _longest_common_word_suffix(session_titles)
        if not base_name and session_titles[0].strip():
            base_name = session_titles[0].strip()
    if base_name:
        base_name = base_name.strip().strip("-–—,: ")
    if not base_name:
        base_name = _extract_event_base(first)
    venue = first.get("strVenue") or ""
    city = first.get("strCity") or ""
    country = first.get("strCountry") or ""
    location = join_location(city, country)

    template = round_title_template or ""
    if template:
        rendered = template.format(
            round_number=round_number,
            round_label=round_label,
            event_base=base_name or "",
            venue=venue,
            city=city,
            country=country,
            location=location,
            season=season,
        ).strip()
        if rendered:
            return rendered

    if base_name:
        return base_name
    if location:
        return f"{round_label} {round_number} – {location}"
    return f"{round_label} {round_number}"


def _build_round_summary(
    fixtures: Sequence[dict],
    *,
    round_title: str,
    season: str,
) -> str:
    if not fixtures:
        return (
            f"{round_title} currently has no published sessions in the TheSportsDB feed "
            f"for the {season} ISU Grand Prix season."
        )

    dates = [_date_from_event(event) for event in fixtures]
    date_span = _format_date_range(dates)
    reference = fixtures[0]
    venue = reference.get("strVenue") or "TBD venue"
    location = join_location(reference.get("strCity"), reference.get("strCountry"))
    venue_text = venue
    if location:
        venue_text = f"{venue} ({location})" if venue else location

    summary_parts = []
    if date_span:
        summary_parts.append(f"{round_title} spans {date_span} at {venue_text}.")
    else:
        summary_parts.append(f"{round_title} is scheduled at {venue_text}.")
    summary_parts.append(
        f"TheSportsDB currently lists {len(fixtures)} broadcast blocks for automation."
    )
    return " ".join(summary_parts)


def _build_session_summary(event: dict, round_title: str) -> str:
    session_title = (
        event.get("strEvent")
        or event.get("strEventAlternate")
        or event.get("strFilename")
        or "Session"
    )
    venue = event.get("strVenue") or "TBD venue"
    event_date = _date_from_event(event)
    summary_parts = [
        f"{session_title} coverage for {round_title} at {venue}"
        f"{location_suffix(event.get('strCity'), event.get('strCountry'))}."
    ]
    summary_parts.append(f"Scheduled date: {event_date.strftime('%B %d, %Y')}.")
    if event.get("strTimeLocal"):
        summary_parts.append(f"Local start: {event['strTimeLocal']}.")
    elif event.get("strTime"):
        summary_parts.append(f"Listed start: {event['strTime']} (UTC).")
    tv = event.get("strTVStation")
    if tv:
        summary_parts.append(f"Broadcast: {tv}.")
    description = event.get("strDescriptionEN")
    if description and description.strip():
        summary_parts.append(description.strip())
    return " ".join(summary_parts)


def _pick_poster_source(event: dict) -> Optional[str]:
    fields = [
        "strPoster",
        "strThumb",
        "strEventThumb",
        "strBanner",
    ]
    for field in fields:
        url = event.get(field)
        if url:
            return url
    return None


def _pick_background_source(event: dict) -> Optional[str]:
    fields = [
        "strFanart",
        "strFanart1",
        "strFanart2",
        "strFanart3",
    ]
    for field in fields:
        url = event.get(field)
        if url:
            return url
    return None


def _pick_episode_thumb(event: dict) -> Optional[str]:
    fields = [
        "strThumb",
        "strEventThumb",
        "strBanner",
        "strPoster",
    ]
    for field in fields:
        url = event.get(field)
        if url:
            return url
    return None


def build_metadata(args: argparse.Namespace, sportsdb: SportsDBSettings) -> dict:
    verify_ssl = not args.insecure
    context = build_ssl_context(verify_ssl)
    rate_limiter = RateLimiter(args.request_interval)
    assets_root = args.assets_root
    download_assets = not args.skip_asset_download
    try:
        events = fetch_season_events(
            args.season,
            args.league_id,
            sportsdb,
            context,
            rate_limiter,
            args.max_retries,
            args.retry_backoff,
        )
    except urllib.error.URLError as exc:
        if verify_ssl:
            print(
                "SSL verification failed, retrying without verification...",
                file=sys.stderr,
            )
            context = build_ssl_context(False)
            events = fetch_season_events(
                args.season,
                args.league_id,
                sportsdb,
                context,
                rate_limiter,
                args.max_retries,
                args.retry_backoff,
            )
        else:
            raise RuntimeError(f"Failed to fetch season data: {exc}") from exc

    season_summary: Optional[str] = None
    try:
        season_summary = fetch_season_description_text(
            season=args.season,
            league_id=args.league_id,
            sportsdb=sportsdb,
            fetch_json=_fetch_json,
            context=context,
            rate_limiter=rate_limiter,
            retries=args.max_retries,
            retry_backoff=args.retry_backoff,
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
                rate_limiter=rate_limiter,
                retries=args.max_retries,
                retry_backoff=args.retry_backoff,
            )
        else:
            print(
                f"Warning: failed to fetch season description: {exc}",
                file=sys.stderr,
            )

    events_by_round: Dict[int, List[dict]] = {}
    for event in events:
        round_number = _round_number_from_event(event)
        if round_number is None:
            continue
        if round_number < args.matchweek_start or round_number > args.matchweek_stop:
            continue
        events_by_round.setdefault(round_number, []).append(event)

    if (
        not args.skip_matchweek_fill
        and args.matchweek_stop >= args.matchweek_start
    ):
        for round_number in range(args.matchweek_start, args.matchweek_stop + 1):
            if events_by_round.get(round_number):
                continue
            try:
                round_events = fetch_round_events(
                    args.season,
                    args.league_id,
                    round_number,
                    sportsdb,
                    context,
                    rate_limiter,
                    args.max_retries,
                    args.retry_backoff,
                )
            except urllib.error.URLError as exc:
                if verify_ssl:
                    print(
                        "Round fetch failed with SSL error, retrying insecure "
                        f"for {args.round_label.lower()} {round_number}...",
                        file=sys.stderr,
                    )
                    context = build_ssl_context(False)
                    round_events = fetch_round_events(
                        args.season,
                        args.league_id,
                        round_number,
                        sportsdb,
                        context,
                        rate_limiter,
                        args.max_retries,
                        args.retry_backoff,
                    )
                else:
                    raise RuntimeError(
                        f"Failed to fetch {args.round_label.lower()} {round_number}: {exc}"
                    ) from exc

            if round_events:
                events_by_round[round_number] = round_events
            if args.matchweek_delay > 0 and round_number < args.matchweek_stop:
                time.sleep(args.matchweek_delay)

    first_round = min(events_by_round) if events_by_round else None
    first_session = events_by_round[first_round][0] if first_round else None
    if download_assets and first_session:
        if args.poster_rel:
            ensure_asset_download(
                _pick_poster_source(first_session),
                assets_root / args.poster_rel,
                context,
                rate_limiter,
                args.max_retries,
                args.retry_backoff,
            )
        if args.background_rel:
            ensure_asset_download(
                _pick_background_source(first_session),
                assets_root / args.background_rel,
                context,
                rate_limiter,
                args.max_retries,
                args.retry_backoff,
            )

    seasons = []
    for round_number in sorted(events_by_round):
        fixtures = events_by_round[round_number]
        fixtures.sort(key=_session_sort_key)

        session_titles = [
            _session_title_from_event(event, idx + 1)
            for idx, event in enumerate(fixtures)
        ]
        round_title = _derive_round_title(
            fixtures,
            session_titles=session_titles,
            round_number=round_number,
            round_label=args.round_label,
            round_title_template=args.round_title_template,
            season=args.season,
        )
        episodes = []
        matchweek_token = f"{round_number:02d}"
        season_poster = None
        season_poster_rel = None
        artwork_event = fixtures[0] if fixtures else None
        if args.matchweek_poster_template:
            season_poster_rel = args.matchweek_poster_template.format(
                season=args.season,
                matchweek=round_number,
                matchweek_token=matchweek_token,
            )
            season_poster_path = assets_root / season_poster_rel
            if download_assets and artwork_event:
                ensure_asset_download(
                    _pick_poster_source(artwork_event),
                    season_poster_path,
                    context,
                    rate_limiter,
                    args.max_retries,
                    args.retry_backoff,
                )
            season_poster = build_asset_url(args.asset_url_base, season_poster_rel)
        elif args.matchweek_poster_fallback:
            fallback_rel = args.matchweek_poster_fallback.format(
                season=args.season,
                matchweek=round_number,
                matchweek_token=matchweek_token,
            )
            season_poster = build_asset_url(args.asset_url_base, fallback_rel)

        for index, (event, session_title) in enumerate(
            zip(fixtures, session_titles), start=1
        ):
            event_date = _date_from_event(event)
            session_slug = slugify(session_title)
            episode_poster_url = None
            if args.fixture_poster_template:
                episode_poster_rel = args.fixture_poster_template.format(
                    season=args.season,
                    matchweek=round_number,
                    matchweek_token=matchweek_token,
                    session_slug=session_slug,
                    episode_index=index,
                )
                episode_poster_path = assets_root / episode_poster_rel
                episode_poster_url = build_asset_url(
                    args.asset_url_base, episode_poster_rel
                )
                if download_assets:
                    ensure_asset_download(
                        _pick_episode_thumb(event),
                        episode_poster_path,
                        context,
                        rate_limiter,
                        args.max_retries,
                        args.retry_backoff,
                    )
            episodes.append(
                {
                    "index": index,
                    "title": session_title,
                    "originally_available": event_date.isoformat(),
                    "summary": _build_session_summary(event, round_title),
                    "url_poster": episode_poster_url,
                }
            )

        summary = _build_round_summary(
            fixtures,
            round_title=round_title,
            season=args.season,
        )
        seasons.append(
            {
                "number": round_number,
                "title": round_title,
                "sort_title": f"{round_number:02d}_{round_title}",
                "summary": summary,
                "url_poster": season_poster,
                "episodes": episodes,
            }
        )

    show_id = args.show_id or args.title
    show_summary = season_summary or args.summary
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
        description="Generate ISU Grand Prix metadata YAML using TheSportsDB.",
    )
    parser.add_argument(
        "--season",
        default="2025",
        help="Season identifier passed to TheSportsDB (e.g. 2025).",
    )
    parser.add_argument(
        "--league-id",
        type=int,
        default=5753,
        help="TheSportsDB league/competition ID for the ISU Grand Prix.",
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
        default="Figure Skating Grand Prix {season}",
        help="Show title used in the metadata tree.",
    )
    parser.add_argument(
        "--sort-title",
        default=None,
        help="Optional sort title for the show (defaults to title).",
    )
    parser.add_argument(
        "--show-id",
        default="Figure Skating Grand Prix {season}",
        help="Metadata key used under the top-level 'metadata:' block.",
    )
    parser.add_argument(
        "--poster-url",
        default="posters/figure-skating-grand-prix/{season}/poster.jpg",
        help="Show-level poster path or URL (supports {season}).",
    )
    parser.add_argument(
        "--background-url",
        default="posters/figure-skating-grand-prix/{season}/background.jpg",
        help="Show-level background path or URL (supports {season}).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {season} ISU Grand Prix season spans the global figure skating circuit "
            "from the opening stop through the Grand Prix Final. Each SportsDB round is "
            "grouped here so short programs, free skates, rhythm dances and gala "
            "broadcasts can be matched automatically."
        ),
        help="Overall show summary text (supports {season}).",
    )
    parser.add_argument(
        "--round-label",
        default=DEFAULT_ROUND_LABEL,
        help="Label used when referencing each SportsDB round (e.g. 'Grand Prix stop').",
    )
    parser.add_argument(
        "--round-title-template",
        default=DEFAULT_ROUND_TITLE_TEMPLATE,
        help=(
            "Optional template for season titles. Supports {season}, {round_label}, "
            "{round_number}, {event_base}, {venue}, {city}, {country}, {location}. "
            "Leave blank to fall back to SportsDB event names."
        ),
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
        "--matchweek-poster-template",
        default="posters/figure-skating-grand-prix/{season}/s{matchweek_token}/poster.jpg",
        help=(
            "Relative path template for stop (season-level) posters. Supports "
            "{season}, {matchweek}, {matchweek_token}."
        ),
    )
    parser.add_argument(
        "--matchweek-poster-fallback",
        default="",
        help="Fallback relative path when SportsDB lacks art (same tokens as template).",
    )
    parser.add_argument(
        "--fixture-poster-template",
        default="posters/figure-skating-grand-prix/{season}/s{matchweek_token}/e{episode_index}.jpg",
        help=(
            "Relative path template for per-session posters. Supports {season}, "
            "{matchweek}, {matchweek_token}, {session_slug}, {episode_index}."
        ),
    )
    parser.add_argument(
        "--skip-asset-download",
        action="store_true",
        help="Skip downloading SportsDB artwork for seasons/episodes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML "
        "(defaults to metadata/figure-skating-grand-prix/{season}.yaml).",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification.",
    )
    parser.add_argument(
        "--matchweek-start",
        type=int,
        default=DEFAULT_MATCHWEEK_START,
        help="First SportsDB round number to include (default: 1).",
    )
    parser.add_argument(
        "--matchweek-stop",
        type=int,
        default=DEFAULT_MATCHWEEK_STOP,
        help="Last SportsDB round number to include (default: 12).",
    )
    parser.add_argument(
        "--matchweek-delay",
        type=float,
        default=0.0,
        help="Extra seconds to wait between round fetches (added after each request).",
    )
    parser.add_argument(
        "--skip-matchweek-fill",
        action="store_true",
        help="Disable per-round fetches (use only eventsseason.php).",
    )
    parser.add_argument(
        "--request-interval",
        type=float,
        default=None,
        help=(
            "Minimum seconds between SportsDB API calls "
            "(defaults to 2.1s for v1 or 0.6s for v2 when omitted)."
        ),
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries for HTTP 429/5xx responses.",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=3.0,
        help="Base seconds for exponential backoff when retrying.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    sportsdb = SPORTSDB_DEFAULTS.with_overrides(
        api_key=args.api_key,
        api_version=args.api_version,
    )
    if args.request_interval is None:
        args.request_interval = default_request_interval(sportsdb.api_version)
    args.assets_root = Path(args.assets_root).expanduser()

    def resolve_asset(value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not value:
            return None, None
        formatted = value.format(season=args.season)
        if formatted.lower().startswith(("http://", "https://")):
            return formatted, None
        asset_url = f"{args.asset_url_base.rstrip('/')}/{formatted.lstrip('/')}"
        return asset_url, formatted

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
    if args.round_label:
        args.round_label = args.round_label.format(season=args.season)

    metadata = build_metadata(args, sportsdb)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        safe_season = args.season.replace("/", "-")
        output_path = Path("metadata") / f"figure-skating-grand-prix/{safe_season}.yaml"
    output_path = output_path.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote ISU Grand Prix metadata to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())



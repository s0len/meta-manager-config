#!/usr/bin/env python3
"""Generate Formula 1 metadata YAML using TheSportsDB rounds feed.

This script mirrors :mod:`generate_ufc_metadata` but targets Formula 1
(``league_id 4370``). It groups SportsDB fixtures by round, emits a season
entry per round, and renders the full broadcast stack (press conferences,
practice, sprint, qualifying, pre/post shows and race) as episodes.
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
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sportsdb import (
    SportsDBSettings,
    default_request_interval,
    load_sportsdb_settings,
)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

DEFAULT_MATCHWEEK_START = 1
DEFAULT_MATCHWEEK_STOP = 30
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

SPORTSDB_DEFAULTS = load_sportsdb_settings()
SESSION_SUFFIX_RE = re.compile(
    r"[\s\-–—,:]*(?:"
    r"free\s+practice\s*\d+|"
    r"practice\s*\d+|"
    r"fp\d+|"
    r"drivers?\s+press\s+conference|"
    r"weekend\s+warm\s*-?\s*up|"
    r"sprint\s+qualifying|"
    r"sprint|"
    r"qualifying|"
    r"pre\s+qualifying\s+show|"
    r"post\s+qualifying\s+show|"
    r"pre\s+race\s+show|"
    r"post\s+race\s+show"
    r")$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SessionSlot:
    slug: str
    title: str
    keywords: Tuple[str, ...]
    summary_hint: str
    day_offset: int
    fallback_slugs: Tuple[str, ...] = ()


STANDARD_WEEKEND_SESSIONS: Tuple[SessionSlot, ...] = (
    SessionSlot(
        slug="drivers-press-conference",
        title="Drivers Press Conference",
        keywords=("press conference", "drivers press", "media day"),
        summary_hint=(
            "Selected drivers brief the media on car updates and expectations for the weekend."
        ),
        day_offset=-2,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="weekend-warm-up",
        title="Weekend Warm Up",
        keywords=("weekend warm", "warmup", "warm-up"),
        summary_hint=(
            "Preview show covering track walks, tyre choices and evolving weather conditions."
        ),
        day_offset=-2,
        fallback_slugs=("drivers-press-conference", "race"),
    ),
    SessionSlot(
        slug="free-practice-1",
        title="Free Practice 1",
        keywords=("practice 1", "free practice 1", "fp1"),
        summary_hint="Opening practice hour focused on systems checks and baseline setup work.",
        day_offset=-2,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="free-practice-2",
        title="Free Practice 2",
        keywords=("practice 2", "free practice 2", "fp2"),
        summary_hint="Second practice mirrors race conditions for long-run and tyre evaluation.",
        day_offset=-2,
        fallback_slugs=("free-practice-1", "race"),
    ),
    SessionSlot(
        slug="free-practice-3",
        title="Free Practice 3",
        keywords=("practice 3", "free practice 3", "fp3"),
        summary_hint="Final tune-up where teams chase qualifying simulations and outright pace.",
        day_offset=-1,
        fallback_slugs=("free-practice-2", "race"),
    ),
    SessionSlot(
        slug="pre-qualifying-show",
        title="Pre Qualifying Show",
        keywords=("pre qualifying", "pre-qualifying"),
        summary_hint="Build-up show that recaps practice data before knockout qualifying begins.",
        day_offset=-1,
        fallback_slugs=("qualifying", "race"),
    ),
    SessionSlot(
        slug="qualifying",
        title="Qualifying",
        keywords=("qualifying", "qualy", "qualification"),
        summary_hint="Three-stage knockout session that sets Sunday's grid for the Grand Prix.",
        day_offset=-1,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="post-qualifying-show",
        title="Post Qualifying Show",
        keywords=("post qualifying", "post-qualifying"),
        summary_hint="Immediate reaction, interviews and technical analysis after qualifying.",
        day_offset=-1,
        fallback_slugs=("qualifying", "race"),
    ),
    SessionSlot(
        slug="pre-race-show",
        title="Pre Race Show",
        keywords=("pre race", "pre-race"),
        summary_hint="Grid walk coverage with final strategy talk before lights out.",
        day_offset=0,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="race",
        title="Race",
        keywords=("race", "grand prix"),
        summary_hint="Full Grand Prix distance deciding the championship points haul.",
        day_offset=0,
        fallback_slugs=("qualifying",),
    ),
    SessionSlot(
        slug="post-race-show",
        title="Post Race Show",
        keywords=("post race", "post-race"),
        summary_hint="Podium ceremonies, driver interviews and parc fermé debriefs.",
        day_offset=0,
        fallback_slugs=("race",),
    ),
)

SPRINT_WEEKEND_SESSIONS: Tuple[SessionSlot, ...] = (
    SessionSlot(
        slug="drivers-press-conference",
        title="Drivers Press Conference",
        keywords=("press conference", "drivers press", "media day"),
        summary_hint=(
            "Selected drivers brief the media on car updates and expectations for the weekend."
        ),
        day_offset=-2,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="weekend-warm-up",
        title="Weekend Warm Up",
        keywords=("weekend warm", "warmup", "warm-up"),
        summary_hint=(
            "Preview show covering track walks, tyre choices and evolving weather conditions."
        ),
        day_offset=-2,
        fallback_slugs=("drivers-press-conference", "race"),
    ),
    SessionSlot(
        slug="free-practice-1",
        title="Free Practice 1",
        keywords=("practice 1", "free practice 1", "fp1"),
        summary_hint="Only practice session before the sprint shootout, vital for rapid setup work.",
        day_offset=-2,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="sprint-qualifying",
        title="Sprint Qualifying",
        keywords=("sprint qualifying", "sprint shootout"),
        summary_hint="Short sprint shootout that sets the grid for Saturday's sprint race.",
        day_offset=-1,
        fallback_slugs=("free-practice-1", "race"),
    ),
    SessionSlot(
        slug="pre-sprint-show",
        title="Pre Sprint Show",
        keywords=("pre sprint", "pre-sprint"),
        summary_hint="Studio build-up covering sprint strategies, tyre allocations and weather.",
        day_offset=-1,
        fallback_slugs=("sprint", "sprint-qualifying"),
    ),
    SessionSlot(
        slug="sprint",
        title="Sprint",
        keywords=("sprint", "sprint race"),
        summary_hint="100km dash awarding points to the top eight and shaping the weekend narrative.",
        day_offset=-1,
        fallback_slugs=("sprint-qualifying", "qualifying", "race"),
    ),
    SessionSlot(
        slug="post-sprint-show",
        title="Post Sprint Show",
        keywords=("post sprint", "post-sprint"),
        summary_hint="Analysis and driver interviews immediately after the sprint finish.",
        day_offset=-1,
        fallback_slugs=("sprint", "qualifying"),
    ),
    SessionSlot(
        slug="pre-qualifying-show",
        title="Pre Qualifying Show",
        keywords=("pre qualifying", "pre-qualifying"),
        summary_hint="Reset before traditional qualifying that locks in the Grand Prix grid.",
        day_offset=-2,
        fallback_slugs=("qualifying", "sprint"),
    ),
    SessionSlot(
        slug="qualifying",
        title="Qualifying",
        keywords=("qualifying", "qualy", "qualification"),
        summary_hint="Knockout qualifying held after the sprint to define Sunday's start order.",
        day_offset=-2,
        fallback_slugs=("sprint", "race"),
    ),
    SessionSlot(
        slug="post-qualifying-show",
        title="Post Qualifying Show",
        keywords=("post qualifying", "post-qualifying"),
        summary_hint="Reactions and technical analysis once the Grand Prix grid is finalised.",
        day_offset=-2,
        fallback_slugs=("qualifying", "race"),
    ),
    SessionSlot(
        slug="pre-race-show",
        title="Pre Race Show",
        keywords=("pre race", "pre-race"),
        summary_hint="Grid walk coverage with final strategy talk before lights out.",
        day_offset=0,
        fallback_slugs=("race",),
    ),
    SessionSlot(
        slug="race",
        title="Race",
        keywords=("race", "grand prix"),
        summary_hint="Full Grand Prix distance deciding the championship points haul.",
        day_offset=0,
        fallback_slugs=("qualifying",),
    ),
    SessionSlot(
        slug="post-race-show",
        title="Post Race Show",
        keywords=("post race", "post-race"),
        summary_hint="Podium ceremonies, driver interviews and parc fermé debriefs.",
        day_offset=0,
        fallback_slugs=("race",),
    ),
)


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
    return cleaned or "round"


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

    events = payload.get("events")
    if not events:
        raise RuntimeError(
            f"No events returned for league {league_id} season {season} "
            f"(API {sportsdb.api_version})."
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
    events = payload.get("events") or []
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


def _fixture_sort_key(event: dict) -> Tuple[date, str]:
    event_date = _date_from_event(event)
    event_name = (event.get("strEvent") or "").lower()
    return (event_date, event_name)


def _match_session_event(
    events: Sequence[dict],
    keywords: Sequence[str],
) -> Optional[dict]:
    lowered_keywords = tuple(token.lower() for token in keywords)
    for event in events:
        haystacks = [
            event.get("strEvent") or "",
            event.get("strEventAlternate") or "",
            event.get("strFilename") or "",
        ]
        combined = " ".join(haystacks).lower()
        if any(token in combined for token in lowered_keywords):
            return event
    return None


def _is_sprint_weekend(events: Sequence[dict]) -> bool:
    for event in events:
        haystack = " ".join(
            [
                event.get("strEvent") or "",
                event.get("strEventAlternate") or "",
                event.get("strDescriptionEN") or "",
            ]
        ).lower()
        if "sprint" in haystack:
            return True
    return False


def _select_primary_event(events: Sequence[dict]) -> Optional[dict]:
    if not events:
        return None

    def priority(event: dict) -> Tuple[int, date]:
        title = (event.get("strEvent") or "").lower()
        is_practice = "practice" in title or re.search(r"\bfp\d\b", title)
        is_qualifying = "qualifying" in title and "sprint" not in title
        is_sprint = "sprint" in title
        is_race = "race" in title or (
            "grand prix" in title and not (is_practice or is_qualifying or is_sprint)
        )
        if is_race:
            rank = 0
        elif is_qualifying:
            rank = 1
        elif is_sprint:
            rank = 2
        elif is_practice:
            rank = 3
        else:
            rank = 4
        return rank, _date_from_event(event)

    return min(events, key=priority)


def _clean_round_title(raw_title: Optional[str], fallback: str) -> str:
    if not raw_title:
        return fallback
    title = raw_title.strip()
    sprint_suffix = re.compile(
        r"[\s\-–—,:]*(?:sprint(?:\s*race)?|gp\s*sprint|sprint\s*gp)\s*$",
        re.IGNORECASE,
    )
    title = sprint_suffix.sub("", title).strip(" -–—,:")
    while True:
        stripped = SESSION_SUFFIX_RE.sub("", title).strip(" -–—,:")
        if stripped == title:
            break
        title = stripped
    return title or fallback


def _format_date_range(dates: Iterable[date]) -> Optional[str]:
    ordered = sorted(dates)
    if not ordered:
        return None
    first, last = ordered[0], ordered[-1]
    if first == last:
        return f"{first.strftime('%B')} {first.day}, {first.year}"
    if first.year == last.year:
        if first.month == last.month:
            return f"{first.strftime('%B')} {first.day}-{last.day}, {first.year}"
        return (
            f"{first.strftime('%B')} {first.day} - "
            f"{last.strftime('%B')} {last.day}, {first.year}"
        )
    return (
        f"{first.strftime('%B')} {first.day}, {first.year} - "
        f"{last.strftime('%B')} {last.day}, {last.year}"
    )


def _pick_poster_source(event: dict) -> Optional[str]:
    fields = [
        "strPoster",
        "strEventPoster",
        "strBanner",
        "strThumb",
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
        "strPoster",
        "strBanner",
    ]
    for field in fields:
        url = event.get(field)
        if url:
            return url
    return None


def _event_location(event: dict) -> str:
    bits = [
        event.get("strCircuit"),
        event.get("strCity"),
        event.get("strCountry"),
    ]
    compacted = [bit for bit in bits if bit]
    return ", ".join(compacted)


def _season_summary(
    round_label: str,
    round_number: int,
    session_count: int,
    date_span: Optional[str],
    event_name: str,
) -> str:
    if session_count and date_span:
        return (
            f"{round_label} {round_number} ({event_name}) spans {date_span} "
            f"with {session_count} curated broadcast session"
            f"{'' if session_count == 1 else 's'} mapped from TheSportsDB "
            "for this Formula 1 weekend."
        )
    if session_count:
        return (
            f"{round_label} {round_number} ({event_name}) currently lists "
            f"{session_count} broadcast session"
            f"{'' if session_count == 1 else 's'} for the weekend."
        )
    return (
        f"{round_label} {round_number} ({event_name}) does not yet have "
        "Formula 1 sessions available in TheSportsDB."
    )


def _session_summary(
    slot: SessionSlot,
    event: Optional[dict],
    weekend_title: str,
    default_venue: str,
    default_location: str,
) -> str:
    event = event or {}
    event_name = event.get("strEvent") or weekend_title
    venue = event.get("strVenue") or default_venue or "TBD Circuit"
    location = _event_location(event) or default_location
    event_date = _date_from_event(event)
    description = (event.get("strDescriptionEN") or "").strip()
    summary_parts = [
        f"{slot.title} for {weekend_title} takes place at {venue}"
        f"{f' ({location})' if location else ''} on "
        f"{event_date.strftime('%B %d, %Y')}."
    ]
    if event.get("strTimeLocal"):
        summary_parts.append(f"Local start: {event['strTimeLocal']}.")
    elif event.get("strTime"):
        summary_parts.append(f"Listed start: {event['strTime']} (UTC).")
    if description:
        summary_parts.append(description)
    elif slot.summary_hint:
        summary_parts.append(slot.summary_hint)
    else:
        summary_parts.append(
            "Additional broadcast details will be filled once TheSportsDB updates "
            "the Formula 1 round feed."
        )
    return " ".join(summary_parts)


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

    events_by_round: Dict[int, List[dict]] = {}
    for event in events:
        try:
            round_number = int(event.get("intRound") or 0)
        except ValueError:
            continue
        if round_number == 0:
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
                        f"for round {round_number}...",
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
                        f"Failed to fetch round {round_number}: {exc}"
                    ) from exc

            if round_events:
                events_by_round[round_number] = round_events
            if args.matchweek_delay > 0 and round_number < args.matchweek_stop:
                time.sleep(args.matchweek_delay)

    first_round = min(events_by_round) if events_by_round else None
    first_event = events_by_round[first_round][0] if first_round else None
    if download_assets and first_event:
        if args.poster_rel:
            ensure_asset_download(
                _pick_poster_source(first_event),
                assets_root / args.poster_rel,
                context,
                rate_limiter,
                args.max_retries,
                args.retry_backoff,
            )
        if args.background_rel:
            ensure_asset_download(
                _pick_background_source(first_event),
                assets_root / args.background_rel,
                context,
                rate_limiter,
                args.max_retries,
                args.retry_backoff,
            )

    seasons = []
    for round_number in sorted(events_by_round):
        fixtures = events_by_round[round_number]
        fixtures.sort(key=_fixture_sort_key)
        matchweek_token = f"{round_number:02d}"
        primary_event = _select_primary_event(fixtures)
        artwork_event = primary_event or (fixtures[0] if fixtures else None)
        raw_event_name = artwork_event.get("strEvent") if artwork_event else None
        event_name = _clean_round_title(
            raw_event_name,
            f"{args.round_label} {round_number}",
        )
        season_poster_url = None

        if args.matchweek_poster_template:
            season_poster_rel = args.matchweek_poster_template.format(
                season=args.season,
                matchweek=round_number,
                matchweek_token=matchweek_token,
                round=round_number,
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
            season_poster_url = build_asset_url(args.asset_url_base, season_poster_rel)
        elif args.matchweek_poster_fallback:
            fallback_rel = args.matchweek_poster_fallback.format(
                season=args.season,
                matchweek=round_number,
                matchweek_token=matchweek_token,
                round=round_number,
            )
            season_poster_url = build_asset_url(args.asset_url_base, fallback_rel)

        episodes = []
        dates: List[date] = []
        for fixture_event in fixtures:
            dates.append(_date_from_event(fixture_event))
        round_slug = slugify(event_name)
        is_sprint = _is_sprint_weekend(fixtures)
        session_plan = (
            SPRINT_WEEKEND_SESSIONS if is_sprint else STANDARD_WEEKEND_SESSIONS
        )
        matched_events: Dict[str, dict] = {}
        for slot in session_plan:
            match = _match_session_event(fixtures, slot.keywords)
            if match:
                matched_events.setdefault(slot.slug, match)
        context_event = primary_event or artwork_event or {}
        default_venue = (context_event.get("strVenue") or "TBD Circuit")
        default_location = _event_location(context_event)
        race_date = max(dates) if dates else _date_from_event(context_event)

        for index, slot in enumerate(session_plan, start=1):
            source_event: Optional[dict] = matched_events.get(slot.slug)
            if source_event is None:
                for fallback_slug in slot.fallback_slugs:
                    source_event = matched_events.get(fallback_slug)
                    if source_event:
                        break
            if source_event is None:
                source_event = primary_event or artwork_event or {}
            event_date = race_date + timedelta(days=slot.day_offset)
            session_slug = slugify(slot.slug)
            episode_poster_url = None
            if args.fixture_poster_template:
                episode_poster_rel = args.fixture_poster_template.format(
                    season=args.season,
                    matchweek=round_number,
                    matchweek_token=matchweek_token,
                    round=round_number,
                    event_slug=round_slug,
                    session_slug=session_slug,
                    episode_index=index,
                )
                episode_poster_path = assets_root / episode_poster_rel
                episode_poster_url = build_asset_url(
                    args.asset_url_base, episode_poster_rel
                )
                if download_assets:
                    ensure_asset_download(
                        _pick_episode_thumb(source_event),
                        episode_poster_path,
                        context,
                        rate_limiter,
                        args.max_retries,
                        args.retry_backoff,
                    )
            episodes.append(
                {
                    "index": index,
                    "title": slot.title,
                    "originally_available": event_date.isoformat(),
                    "summary": _session_summary(
                        slot,
                        source_event,
                        event_name,
                        default_venue,
                        default_location,
                    ),
                    "url_poster": episode_poster_url,
                }
            )

        summary = _season_summary(
            args.round_label,
            round_number,
            len(session_plan),
            _format_date_range(dates),
            event_name,
        )

        seasons.append(
            {
                "number": round_number,
                "title": event_name,
                "sort_title": f"{round_number:02d}_{event_name}",
                "summary": summary,
                "url_poster": season_poster_url,
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
            if episode.get("url_poster"):
                lines.append(f"            url_poster: {episode['url_poster']}")
            lines.append("            summary: >")
            lines.extend(_wrap_lines("              ", episode["summary"]))
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Formula 1 metadata YAML using TheSportsDB rounds feed.",
    )
    parser.add_argument(
        "--season",
        default="2025",
        help="Season identifier passed to TheSportsDB (e.g. 2025).",
    )
    parser.add_argument(
        "--league-id",
        type=int,
        default=4370,
        help="TheSportsDB league/competition ID for Formula 1.",
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
        default="Formula 1 {season}",
        help="Show title used in the metadata tree.",
    )
    parser.add_argument(
        "--sort-title",
        default=None,
        help="Optional sort title for the show (defaults to title).",
    )
    parser.add_argument(
        "--show-id",
        default="Formula 1 {season}",
        help="Metadata key used under the top-level 'metadata:' block.",
    )
    parser.add_argument(
        "--poster-url",
        default="posters/formula1/{season}/poster.jpg",
        help="Show-level poster path or URL (supports {season}).",
    )
    parser.add_argument(
        "--background-url",
        default="posters/formula1/{season}/background.jpg",
        help="Show-level background path or URL (supports {season}).",
    )
    parser.add_argument(
        "--summary",
        default=(
            "The {season} FIA Formula One World Championship spans every Grand Prix "
            "weekend across the calendar. Each SportsDB round is grouped here so "
            "press conferences, practice, sprint, qualifying and race recordings can "
            "be organised automatically."
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
        "--matchweek-poster-template",
        default="posters/formula1/{season}/s{matchweek}/poster.jpg",
        help=(
            "Relative path template for round posters. Supports {season}, "
            "{matchweek}, {matchweek_token}, {round}."
        ),
    )
    parser.add_argument(
        "--matchweek-poster-fallback",
        default="",
        help="Fallback relative path when SportsDB lacks art (same tokens as template).",
    )
    parser.add_argument(
        "--fixture-poster-template",
        default="posters/formula1/{season}/s{matchweek}/e{episode_index}.jpg",
        help=(
            "Relative path template for per-session posters. Supports {season}, "
            "{matchweek}, {matchweek_token}, {round}, {event_slug}, {session_slug}, "
            "{episode_index}."
        ),
    )
    parser.add_argument(
        "--skip-asset-download",
        action="store_true",
        help="Skip downloading SportsDB artwork for rounds and episodes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination path for the generated YAML "
        "(defaults to metadata/formula1/{season}.yaml).",
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
        help="First round number to include (default: 1).",
    )
    parser.add_argument(
        "--matchweek-stop",
        type=int,
        default=DEFAULT_MATCHWEEK_STOP,
        help=f"Last round number to include (default: {DEFAULT_MATCHWEEK_STOP}).",
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
    parser.add_argument(
        "--round-label",
        default="Round",
        help="Label used when describing each Formula 1 round (e.g. Round, Grand Prix).",
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

    metadata = build_metadata(args, sportsdb)
    yaml_text = render_yaml(metadata)

    output_path = args.output
    if output_path is None:
        safe_season = args.season.replace("/", "-")
        output_path = Path("metadata") / f"formula1/{safe_season}.yaml"
    output_path = output_path.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote Formula 1 metadata to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())



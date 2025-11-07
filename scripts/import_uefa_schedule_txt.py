#!/usr/bin/env python3
"""Convert the scraped Champions League schedule text file into YAML metadata."""

from __future__ import annotations

import argparse
import re
import textwrap
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List, Optional


SKIP_PREFIXES = (
    "Första kvalomgången",
    "Andra kvalomgången",
    "Tredje kvalomgången",
    "Slutspel",
    "Sammanlagt resultat",
    "Omgång 0",
)


def clean_line(raw: str) -> str:
    line = raw.replace("\u00a0", " ").strip()
    if not line:
        return ""
    line = re.sub(r"Röda kort.*", "", line, flags=re.IGNORECASE).strip()
    line = re.sub(r"Del \d+ av \d+", "", line, flags=re.IGNORECASE).strip()
    line = line.replace("fot (P)", "FT")
    if line.lower().startswith("fot"):
        line = "FT"
    return line.strip()


def collapse_lines(lines: List[str]) -> List[str]:
    cleaned: List[str] = []
    previous = ""
    for raw in lines:
        line = clean_line(raw)
        if not line:
            continue
        if any(line.startswith(prefix) for prefix in SKIP_PREFIXES):
            continue
        if line == previous:
            continue
        cleaned.append(line)
        previous = line
    return cleaned


def is_date(token: str) -> bool:
    return bool(re.match(r"^(?:[A-Za-zÅÄÖåäö]{3}\s+)?\d{1,2}/\d{1,2}$", token))


def is_time(token: str) -> bool:
    return bool(re.match(r"^\d{1,2}:\d{2}$", token))


def is_score(token: str) -> bool:
    return bool(re.match(r"^\d+(?:\s*\(\d+\))?$", token))


def parse_score(token: str) -> Dict[str, Optional[int]]:
    match = re.match(r"^(\d+)(?:\s*\((\d+)\))?$", token)
    if not match:
        raise ValueError(f"Unexpected score token: {token}")
    score = int(match.group(1))
    penalties = int(match.group(2)) if match.group(2) else None
    return {"score": score, "penalties": penalties}


def parse_date(token: str) -> date:
    token = token.strip()
    if " " in token:
        token = token.split(" ", 1)[1]
    day_str, month_str = token.split("/")
    day = int(day_str)
    month = int(month_str)
    year = 2025 if month >= 7 else 2026
    return date(year, month, day)


def parse_schedule(path: Path) -> Dict[int, List[dict]]:
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    lines = collapse_lines(raw_lines)

    matchdays: Dict[int, List[dict]] = {n: [] for n in range(1, 9)}
    i = 0
    current_round: Optional[int] = None

    while i < len(lines):
        token = lines[i]

        round_match = re.match(r"^Omgång\s+(\d+)\s+av\s+8$", token)
        if round_match:
            current_round = int(round_match.group(1))
            i += 1
            continue

        if current_round is None or current_round not in matchdays:
            i += 1
            continue

        if token == "FT":
            status = "final"
            i += 1
            if i >= len(lines):
                break
            date_token = lines[i]
            if not is_date(date_token):
                raise ValueError(f"Expected date after FT, got '{date_token}'")
            match_date = parse_date(date_token)
            i += 1

            match_time: Optional[str] = None
            if i < len(lines) and is_time(lines[i]):
                match_time = lines[i]
                i += 1

            if i + 3 >= len(lines):
                break

            home_team = lines[i]
            i += 1
            home_score_tok = lines[i]
            i += 1
            away_team = lines[i]
            i += 1
            away_score_tok = lines[i]
            i += 1

            if not is_score(home_score_tok) or not is_score(away_score_tok):
                raise ValueError(
                    f"Expected numeric scores for matchday {current_round} on {match_date}."
                )

            home_score = parse_score(home_score_tok)
            away_score = parse_score(away_score_tok)

            matchdays[current_round].append(
                {
                    "date": match_date,
                    "time": match_time,
                    "home": home_team,
                    "away": away_team,
                    "status": status,
                    "home_score": home_score["score"],
                    "away_score": away_score["score"],
                    "home_pen": home_score["penalties"],
                    "away_pen": away_score["penalties"],
                }
            )
            continue

        if is_date(token):
            match_date = parse_date(token)
            i += 1

            match_time: Optional[str] = None
            if i < len(lines) and is_time(lines[i]):
                match_time = lines[i]
                i += 1

            if i + 1 >= len(lines):
                break

            home_team = lines[i]
            i += 1
            away_team = lines[i]
            i += 1

            matchdays[current_round].append(
                {
                    "date": match_date,
                    "time": match_time,
                    "home": home_team,
                    "away": away_team,
                    "status": "scheduled",
                    "home_score": None,
                    "away_score": None,
                    "home_pen": None,
                    "away_pen": None,
                }
            )
            continue

        i += 1

    return matchdays


def format_date_range(dates: List[date]) -> str:
    ordered = sorted(dates)
    if not ordered:
        return ""
    first, last = ordered[0], ordered[-1]
    if first == last:
        return first.strftime("%B %d, %Y")
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


def wrap(prefix: str, text: str, width: int = 96) -> List[str]:
    wrapper = textwrap.TextWrapper(width=width)
    return [f"{prefix}{line}" for line in wrapper.wrap(text)]


def build_metadata(matchdays: Dict[int, List[dict]]) -> str:
    lines: List[str] = ["metadata:"]
    show_id = "UEFA Champions League 2025-26"
    lines.append(f"  {show_id}:")
    lines.append("    title: UEFA Champions League 2025-26")
    lines.append("    sort_title: UEFA Champions League 2025-26")
    lines.append(
        "    url_poster: https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/uefa-champions-league-2025-2026/poster.jpg"
    )
    lines.append(
        "    url_background: https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/uefa-champions-league-2025-2026/background.jpg"
    )
    summary = (
        "The 2025-2026 UEFA Champions League campaign adopts UEFA's new league phase "
        "structure across eight matchdays before the knockout rounds. This metadata "
        "file groups fixtures by matchday so Sports Organizer can match and rename "
        "recordings as the competition progresses."
    )
    lines.append("    summary: >")
    lines.extend(wrap("      ", summary, 100))
    lines.append("    seasons:")

    for round_num in sorted(matchdays.keys()):
        matches = sorted(
            matchdays[round_num],
            key=lambda item: (
                item["date"],
                item["time"] or "00:00",
                item["home"],
                item["away"],
            ),
        )

        season_title = f"Matchday {round_num}"
        lines.append(f"      {round_num}:")
        lines.append(f"        title: {season_title}")
        lines.append(f"        sort_title: {round_num:02d}_{season_title}")

        dates = [match["date"] for match in matches if match["date"]]
        if dates:
            range_text = format_date_range(dates)
            summary_text = (
                f"{season_title} covers {range_text} with {len(matches)} scheduled fixtures."
            )
        else:
            summary_text = f"{season_title} currently has no fixtures available."

        lines.append("        summary: >")
        lines.extend(wrap("          ", summary_text))
        lines.append("        episodes:")

        for index, match in enumerate(matches, start=1):
            lines.append(f"          {index}:")
            lines.append(f"            title: {match['home']} vs {match['away']}")
            lines.append(
                f"            originally_available: {match['date'].isoformat()}"
            )

            if match["status"] == "final":
                result = (
                    f"Result: {match['home']} {match['home_score']} - {match['away_score']} {match['away']}"
                )
                if match["home_pen"] is not None and match["away_pen"] is not None:
                    result += f" (pens {match['home_pen']}-{match['away_pen']})."
                else:
                    result += "."
                summary_lines = [
                    f"Matchday {round_num} fixture played on {match['date'].strftime('%B %d, %Y')}.",
                    result,
                ]
                if match["time"]:
                    summary_lines.insert(
                        1, f"Listed kickoff: {match['time']} (local time)."
                    )
            else:
                summary_lines = [
                    f"Matchday {round_num} fixture scheduled for {match['date'].strftime('%B %d, %Y')}.",
                ]
                if match["time"]:
                    summary_lines.append(
                        f"Kickoff: {match['time']} (local time)."
                    )
                else:
                    summary_lines.append("Kickoff time to be confirmed.")

            lines.append("            summary: >")
            for line in summary_lines:
                lines.extend(wrap("              ", line, 86))

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build UEFA Champions League metadata from the scraped schedule text."
    )
    parser.add_argument("--schedule", type=Path, required=True, help="Path to schedule text file.")
    parser.add_argument("--output", type=Path, required=True, help="Destination YAML path.")
    args = parser.parse_args()

    matchdays = parse_schedule(args.schedule)
    yaml_text = build_metadata(matchdays)

    output_path = args.output.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"Metadata written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



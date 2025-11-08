# Scripts

Utilities that help regenerate or extend metadata files for Sports Organizer live here.

## `generate_nfl_metadata.py`

Pulls the weekly NFL scoreboard feed from ESPN and writes a metadata YAML file that
matches this repository's structure (weeks as seasons, games as episodes).

```shell
python3 scripts/generate_nfl_metadata.py --year 2025
```

The command above creates `metadata-files/nfl-2025-2026.yaml` by default.  You can
override the output path or customise the show title, summary and artwork URLs. Run
`--help` to see all options, including the ability to target specific weeks or to
disable SSL verification if your platform lacks the required CA bundle.

> Tip: rerun the script once the league finalises flexible kickoff windows (Weeks 17
> and 18) to refresh the TBD entries.

## `generate_nba_metadata.py`

Fetches the live NBA schedule JSON from the league CDN and groups fixtures into seasons
using the league-provided `weekNumber`. Each entry in a week becomes an episode with
summary details that cover the venue, city and scheduled date.

```shell
python3 scripts/generate_nba_metadata.py --year 2025
```

By default only regular-season games are written to `metadata-files/nba-2025-26.yaml`.
Include additional phases such as preseason or the Emirates NBA Cup by repeating the
`--phase` flag (for example `--phase preseason --phase cup`). Artwork URLs, summaries
and output paths mirror the knobs provided by the other generators, so use `--help` to
review every option. Re-run the script whenever the NBA updates the feed to keep dates
and neutral-site markers fresh.

## `generate_premier_league_metadata.py`

Generates Premier League metadata using Pulse Live's fixtures endpoint. Matchweeks are
treated as seasons, with each fixture producing an episode entry that includes venue
and kickoff details.

```shell
python3 scripts/generate_premier_league_metadata.py --year 2025 --season-id 777
```

Find the `season-id` with `https://footballapi.pulselive.com/football/competitions/1/compseasons`
(`777` corresponds to 2025/26). Additional flags let you tweak artwork URLs, show
titles or limit the matchweek range. Use `--help` for the complete option list.

## `generate_uefa_champions_league_metadata.py`

Builds UEFA Champions League metadata from the public match feed used by UEFA.com.
Matchdays are emitted as seasons, each containing every scheduled tie with kickoff
and venue context.

```shell
python3 scripts/generate_uefa_champions_league_metadata.py --season-year 2025
```

Re-run the script whenever UEFA updates fixture details (draws, kickoff changes or
knockout assignments). Flags mirror the other generators so you can customise the
show title, artwork URLs or restrict the matchday range. If UEFA's API is slow, use
`--timeout`, `--retries` or `--retry-delay` to tune the request behaviour. You can
also supply `--cache-json <path>` to store the raw feed for troubleshooting or
`--source-json <path>` to re-render from a JSON file you saved manually. If you need
to capture the payload yourself, copy this curl example (headers help avoid the 404
HTML page):

```shell
curl 'https://www.uefa.com/api/match-api/v1/competitions/CL/seasons/2025/matches' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://www.uefa.com' \
  -H 'Referer: https://www.uefa.com/uefachampionsleague/fixtures-results/' \
  --compressed -o /tmp/ucl-2025.json
```

## `import_uefa_schedule_txt.py`

Parses a text export of the Champions League schedule (as copied from UEFA.com) and
converts it into the repository's YAML metadata format. Use this if the public API
is unreachable but you can paste the full fixture list into `scripts/`. The parser
expects the "Omgång" headings present in the Swedish-language schedule page.

```shell
python3 scripts/import_uefa_schedule_txt.py \
  --schedule scripts/uefa-champions-league-schedule.txt \
  --output metadata-files/uefa-champions-league-2025-26.yaml
```


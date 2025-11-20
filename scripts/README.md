# Scripts

Utilities that help regenerate or extend metadata files for Sports Organizer live here.

## `generate_nfl_metadata.py`

Pulls the weekly NFL scoreboard feed from ESPN and writes a metadata YAML file that
matches this repository's structure (weeks as seasons, games as episodes).

```shell
python3 scripts/generate_nfl_metadata.py --year 2025
```

The command above creates `metadata/nfl-2025-2026.yaml` by default.  You can
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

By default only regular-season games are written to `metadata/nba-2025-26.yaml`.
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

## `generate_premier_league_metadata_sportsdb.py`

Builds the same matchweek structure as the Pulse Live script but sources fixtures
directly from TheSportsDB (league id `4328`). Every SportsDB `intRound` becomes a
season and each event is emitted as an episode with venue, city and kickoff details.

```shell
python3 scripts/generate_premier_league_metadata_sportsdb.py --season 2024-2025
```

Key flags mirror `generate_ufc_metadata`:

- `--season` / `--league-id` / `--api-key` to select the SportsDB feed
- `--matchweek-start/--matchweek-stop` plus `--matchweek-delay` / `--request-interval`
  / `--max-retries` to respect SportsDB rate limits (default 2.1s spacing ≈28 req/min)
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--fixture-poster-template` and
  `--skip-asset-download` to mirror the UFC poster workflow
- `--summary`, `--show-id`, `--sort-title` customise the library metadata, `--insecure`
  switches off SSL verification when needed

Season posters default to `posters/premier-league/<season>/sX/poster.jpg` and episodes
to `posters/premier-league/<season>/sX/eY.jpg` (X = matchweek, Y = episode index). The
script attempts to download SportsDB art (poster/fanart/thumb) into those paths when
available so Plex/Jellyfin can reference the GitHub URLs straight away.

By default the YAML is written to `metadata/premier-league/<season>.yaml`. Run
the generator again whenever fixtures shift so kickoff dates stay aligned.

## `generate_uefa_champions_league_metadata_sportsdb.py`

Builds UEFA Champions League matchday metadata directly from TheSportsDB league feed
(`league_id 4480`). Each SportsDB `intRound` becomes a season labelled as a matchday
and every fixture is emitted as an episode with venue, city and kickoff context,
mirroring the UFC-style CLI.

```shell
python3 scripts/generate_uefa_champions_league_metadata_sportsdb.py \
  --season 2025-2026 --api-key "$TSD_KEY"
```

Key flags:
- `--season` / `--league-id` / `--api-key` / `--round-label` select the SportsDB feed
  and matchday naming
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s rate limiter,
  exponential backoff for 429/5xx and the optional SSL bypass path
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` manage the artwork workflow
- `--summary`, `--show-id`, `--sort-title`, `--output` mirror the UFC metadata
  overrides

Season posters default to `posters/uefa-champions-league/<season>/sX/poster.jpg` and
episodes to `posters/uefa-champions-league/<season>/sX/eY.jpg` (X = matchday,
Y = episode index). Artwork downloads reuse the shared throttled downloader and the
YAML still emits `url_poster` values even when SportsDB provides no art. The output
path defaults to `metadata/uefa-champions-league/<season>.yaml`.

## `generate_motogp_metadata_sportsdb.py`

Targets TheSportsDB MotoGP feed (`league_id 4407`) so every SportsDB round is emitted
as a season and each listed event for that weekend becomes an episode. The generator
mirrors the UFC-style CLI but adds a `--round-label` flag so you can rename rounds as
“Grand Prix”, “Round”, etc.

Each round always outputs six episodes — Practice One, Practice Two, Qualifying One,
Qualifying Two, Sprint and Race — even when TheSportsDB omits specific sessions, so
library structure stays consistent across the calendar.

```shell
python3 scripts/generate_motogp_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Key flags:

- `--season` / `--league-id` / `--api-key` select the SportsDB payload for MotoGP
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s throttle,
  exponential backoff for 429/5xx and the optional SSL bypass path
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` manage the artwork workflow
  (season posters default to `posters/motogp/<season>/sX/poster.jpg`, episodes to
  `posters/motogp/<season>/sX/eY.jpg`; fixture templates can also use `{session_slug}`
  to distinguish Practice/Qualifying/Sprint/Race assets)
- `--round-label`, `--title`, `--summary`, `--sort-title`, `--show-id`, `--output`
  mirror the UFC overrides so you can tailor the library metadata and target path

Artwork downloads reuse the shared throttled downloader, pulling season art from the
SportsDB poster/fanart fields and episodes from the thumb feed. The script still emits
`url_poster` entries even when downloads fail so Plex/Jellyfin can serve assets from
`--asset-url-base`. By default the YAML is written to
`metadata/motogp/<season>.yaml`.

## `generate_formula1_metadata_sportsdb.py`

Targets TheSportsDB Formula 1 feed (`league_id 4370`) so every SportsDB round is
rendered as a Grand Prix weekend. The generator mirrors the UFC-style CLI and
adds the missing broadcast blocks for each event: standard weekends output eleven
episodes (Drivers Press Conference through Post Race Show) while sprint weekends
expand to thirteen entries that include sprint qualifying, the sprint race and
their respective studio shows.

```shell
python3 scripts/generate_formula1_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Key flags:

- `--season` / `--league-id` / `--api-key` select the SportsDB Formula 1 payload
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s throttle,
  exponential backoff for 429/5xx and the optional SSL bypass path
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` power the artwork workflow
  (season posters default to `posters/formula1/<season>/sX/poster.jpg`, episodes
  to `posters/formula1/<season>/sX/eY.jpg`; fixture templates can also use
  `{event_slug}`/`{session_slug}`)
- `--round-label`, `--title`, `--summary`, `--sort-title`, `--show-id`, `--output`
  mirror the UFC-style overrides so you can tailor the metadata tree and target path

Artwork downloads reuse the shared throttled downloader, pulling season art from
poster/fanart endpoints and episode art from the thumb fields. `url_poster`
entries are still emitted even when downloads fail so Plex/Jellyfin can read
assets via `--asset-url-base`. By default the YAML is written to
`metadata/formula1/<season>.yaml`.

## `generate_formula2_metadata_sportsdb.py`

Targets TheSportsDB Formula 2 feed (`league_id 4486`) so every SportsDB `intRound`
becomes a Formula 2 weekend with the four required sessions: Free Practice,
Qualifying, Sprint Race and Feature Race. Free Practice and Qualifying are added
manually because SportsDB only exposes the sprint and feature payloads—this keeps
episode numbering consistent for every Grand Prix.

```shell
python3 scripts/generate_formula2_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Key flags mirror the other SportsDB generators:

- `--season` / `--league-id` / `--api-key` select the Formula 2 payload, while
  `--round-label` controls how each season title references the location (e.g.
  “Round”, “Grand Prix”). Season titles automatically strip “Sprint Race” so only
  the venue/location remains.
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s throttle, exponential
  backoff for 429/5xx responses and the optional SSL bypass. The script replays
  the matchweek fill loop against `eventsround.php` unless you pass
  `--skip-matchweek-fill`.
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` drive the artwork
  workflow. Defaults place round art under `posters/formula2/<season>/sX/poster.jpg`
  and episodes under `posters/formula2/<season>/sX/eY.jpg` (X = round, Y = session
  index). The YAML still emits `url_poster` entries even if downloads fail.
- `--summary`, `--title`, `--sort-title`, `--show-id`, `--output` mirror the
  UFC-style overrides so you can tailor the show metadata and destination path.

Season art pulls from the SportsDB poster/fanart fields and episode thumbs reuse
the throttled downloader, saving into the template paths before GitHub URLs are
emitted. By default the YAML is written to `metadata/formula2/<season>.yaml`.

## `generate_formula3_metadata_sportsdb.py`

Targets TheSportsDB Formula 3 feed (`league_id 4487`). Each SportsDB `intRound`
becomes a Formula 3 weekend and every session returned by the feed is emitted as
an episode—no extra placeholders are injected, so the YAML mirrors SportsDB
exactly.

```shell
python3 scripts/generate_formula3_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Key flags mirror the other SportsDB generators:

- `--season` / `--league-id` / `--api-key` select the Formula 3 payload, while
  `--round-label` controls how season titles reference the location.
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` keep the shared 2.1 s throttle, exponential
  backoff and SSL bypass path.
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` power the artwork
  workflow (defaults land in `posters/formula3/<season>/sX/poster.jpg` for
  seasons and `.../eY.jpg` for episodes). Episode posters are only requested
  when SportsDB provides thumb art, so posterless sessions stay empty.
- `--summary`, `--title`, `--sort-title`, `--show-id`, `--output` mirror the
  UFC-style overrides so you can tailor the show metadata and destination path.

Season art pulls from the SportsDB poster/fanart endpoints and episode thumbs
reuse the throttled downloader. The YAML is written to
`metadata/formula3/<season>.yaml` by default.

## `generate_formula_e_metadata_sportsdb.py`

Targets TheSportsDB Formula E feed (`league_id 4371`) so every SportsDB `intRound`
becomes an E-Prix season entry with the standard four-session stack (Free Practice 1,
Free Practice 2, Qualifying, Race) even when SportsDB lacks those session rows.
Summaries highlight the ABB FIA calendar stops and the YAML always includes
`url_poster` values even when downloads fail.

```shell
python3 scripts/generate_formula_e_metadata_sportsdb.py --season 2024-2025 --api-key "$TSD_KEY"
```

Key flags:

- `--season` / `--league-id` / `--api-key` select the SportsDB feed, while
  `--round-label` controls how each E-Prix season title is phrased.
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s throttle,
  exponential backoff for 429/5xx responses and the optional SSL bypass path.
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` drive the artwork workflow.
  Defaults save season art to `posters/formula-e/<season>/sX/poster.jpg` and episode
  art to `.../eY.jpg` before emitting URLs.
- `--summary`, `--title`, `--sort-title`, `--show-id`, `--output` mirror the UFC
  overrides so you can tailor the metadata tree and destination path.

Artwork downloads reuse the shared throttled downloader, pulling round posters from
SportsDB poster/fanart fields and episode art from the thumb endpoints. The output
path defaults to `metadata/formula-e/<season>.yaml`.

## `generate_moto2_metadata_sportsdb.py`

Targets TheSportsDB Moto2 feed (`league_id 4436`) so each SportsDB `intRound` becomes
a Moto2 race weekend (season entry) and every listed session is rendered as an episode
with venue, city and timing context.

```shell
python3 scripts/generate_moto2_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Key flags mirror the other SportsDB generators:

- `--season` / `--league-id` / `--api-key` select the Moto2 payload
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s rate limiter,
  exponential backoff for 429/5xx and the optional SSL bypass path
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` drive the artwork workflow
  (season posters default to `posters/moto2/<season>/sX/poster.jpg`, episodes to
  `posters/moto2/<season>/sX/eY.jpg`)
- `--round-label`, `--title`, `--sort-title`, `--show-id`, `--summary`, `--output`
  match the UFC-style CLI overrides

Artwork downloads reuse the throttled downloader, pulling season art from SportsDB
poster/fanart fields and episode art from thumb endpoints. The YAML always emits
`url_poster` values even when downloads fail, so Plex/Jellyfin can reference
`--asset-url-base`. By default the script writes to
`metadata/moto2/<season>.yaml`.

## `generate_moto3_metadata_sportsdb.py`

Targets TheSportsDB Moto3 feed (`league_id 4437`) so every SportsDB round is rendered
as a Moto3 weekend (season entry) and each listed session produces an episode with
venue, city and timing context.

```shell
python3 scripts/generate_moto3_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Each round always outputs five episodes — Practice One, Practice Two, Qualifying One,
Qualifying Two and Race — so the library keeps a consistent structure even when
SportsDB omits specific session payloads.

Key flags mirror the UFC/Premier League tooling:

- `--season` / `--league-id` / `--api-key` select the Moto3 payload (default season
  `2025`)
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff`, `--insecure` preserve the shared 2.1 s limiter, exponential
  backoff for 429/5xx and the optional SSL bypass path
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` power the artwork workflow
  (season posters default to `posters/moto3/<season>/sX/poster.jpg`, episodes to
  `posters/moto3/<season>/sX/eY.jpg`; fixture templates can also use `{session_slug}`
  if you prefer deterministic filenames such as `practice-one.jpg`)
- `--round-label`, `--title`, `--sort-title`, `--show-id`, `--summary`, `--output`
  mirror the UFC-style overrides so you can tailor metadata fields

Art downloads reuse the throttled downloader: season assets pull from the SportsDB
poster/fanart endpoints, while episode art comes from the various thumb fields. The
YAML always emits `url_poster` entries— even when downloads fail — so Plex/Jellyfin
can still resolve assets via `--asset-url-base`. By default, output lands in
`metadata/moto3/<season>.yaml`.

## `generate_nba_metadata_sportsdb.py`

Mirrors the UFC/Premier League SportsDB generators but targets the NBA feed
(`league_id 4387`, seasons like `2025-2026`). Each SportsDB `intRound` becomes an
NBA week season and every game is emitted as an episode with venue, city and
scheduled date context.

```shell
python3 scripts/generate_nba_metadata_sportsdb.py --season 2025-2026 --api-key "$TSD_KEY"
```

Key flags:

- `--season` / `--league-id` / `--api-key` select the SportsDB payload
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--skip-matchweek-fill`, `--request-interval`, `--max-retries`,
  `--retry-backoff` maintain the shared 2.1 s throttle plus exponential backoff
  for 429/5xx responses (including the optional `--insecure` retry path)
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--matchweek-poster-fallback`,
  `--fixture-poster-template`, `--skip-asset-download` control the artwork workflow
- `--summary`, `--show-id`, `--sort-title`, `--output` mirror the UFC CLI surface

Season posters default to `posters/nba/<season>/sX/poster.jpg` and episodes to
`posters/nba/<season>/sX/eY.jpg` (X = NBA week, Y = episode index). Art downloads
use the same throttled downloader as the UFC/PL scripts and still emit
`url_poster` entries even when SportsDB lacks artwork. The YAML is written to
`metadata/nba/<season>.yaml` by default.

## `generate_nfl_metadata_sportsdb.py`

Targets TheSportsDB NFL feed (league `4391`) so each SportsDB `intRound`
(regular-season week or postseason round) becomes a season and every scheduled
game becomes an episode entry with venue, city and kickoff notes.

```shell
python3 scripts/generate_nfl_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
```

Key flags mirror the UFC/Premier League generators:

- `--season` / `--league-id` / `--api-key` select the SportsDB payload
- `--matchweek-start`, `--matchweek-stop`, `--matchweek-delay`,
  `--request-interval`, `--max-retries`, `--retry-backoff` respect the shared
  2.1 s rate limiter plus exponential backoff for 429/5xx
- `--poster-url`, `--background-url`, `--asset-url-base`, `--assets-root`,
  `--matchweek-poster-template`, `--fixture-poster-template`,
  `--skip-asset-download` control the artwork flow (defaults write to
  `posters/nfl/<season>/sX/poster.jpg` and `/eY.jpg`)
- `--summary`, `--show-id`, `--sort-title`, `--insecure`,
  `--skip-matchweek-fill` mirror the UFC surface for metadata overrides and SSL
  fallbacks

By default the YAML is written to `metadata/nfl/<season>.yaml`. Re-run the
script whenever the NFL flexes kickoffs or updates postseason matchups so dates
remain current.

## `generate_ufc_metadata.py`

Builds the yearly UFC metadata file directly from TheSportsDB rounds feed. Each
SportsDB `intRound` is emitted as a season (e.g. `UFC 2025` → Season 1 = Fight Night
249, Season 2 = UFC 311, etc.), with episodes representing the Early Prelims,
Prelims and Main Card blocks depending on whether the event is a PPV or Fight Night.

```shell
python3 scripts/generate_ufc_metadata.py --season 2025
```

Key flags:

- `--season` – SportsDB season string (`2025`, `2026`, etc.)
- `--api-key` – SportsDB API key (defaults to `123`)
- `--asset-url-base`/`--assets-root` – control where posters are stored locally and
  which URL base the metadata references (defaults match this repo)
- `--season-poster-template` – relative path for event posters (`{round}`, `{season}`)
- `--episode-poster-template` – relative path for Early Prelims/Prelims/Main Card
  assets (`{round}`, `{episode_title}` slug)
- `--round-start/--round-stop` – numeric range of SportsDB rounds to fetch (default 1-60)
- `--round-delay` – wait time between round fetches (default 2s to stay under the free 30 req/min limit)
- `--skip-asset-download` – disable pulling SportsDB artwork (defaults to enabled, only
  pulls missing files)
- `--insecure` – disable SSL verification if your environment lacks the CA bundle

Re-run the script whenever bouts are rescheduled so the event summaries and block
details stay current. By default the YAML is written to `metadata/ufc-<season>.yaml`.

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
  --output metadata/uefa-champions-league-2025-26.yaml
```

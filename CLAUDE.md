# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

Curated [Kometa](https://kometa.wiki) (formerly Plex Meta Manager) configurations for sports, movies, and TV libraries. There is no build system, test suite, or application code — the deliverables are hand-crafted/generated YAML metadata files plus the artwork they reference. Users consume everything via raw GitHub URLs (`https://raw.githubusercontent.com/s0len/meta-manager-config/main/...`), so **file paths are public API**: renaming or moving a metadata file, poster, or overlay PNG breaks downstream Plex setups.

## Layout

- `metadata/<sport>/<season>.yaml` — one show per sport-season; SportsDB rounds map to Plex **seasons**, sessions/games/fight-blocks map to **episodes**. Older files live flat as `metadata/<league>-<season>.yaml`.
- `posters/<sport>/<season>/sX/poster.jpg` and `.../sX/eY.jpg` — artwork the metadata's `url_poster` entries point to (X = round/matchweek, Y = episode index). Filenames must match metadata references exactly.
- `scripts/` — Python generators that build metadata YAML from APIs (stdlib-only) plus overlay generators (`generate_network_overlay.py`, `generate_resolution_overlay.py`; need pillow+numpy) that recreate the house overlay styles without Photoshop. See `scripts/README.md` for per-script docs.
- `overlays/`, `collection_files/`, `templates.yml` — Kometa overlay PNGs/configs and drop-in collections for movie/TV libraries.
- `docs/` — per-sport setup guides; copy `docs/SportDocTemplate.md` for a new sport and link it in the README table.
- `templates/` — Photoshop source files for posters/title cards.

## Regenerating Metadata

Most generators pull from TheSportsDB and share a common CLI (built on `scripts/sportsdb.py` + `scripts/sportsdb_helpers.py`):

```shell
python3 scripts/generate_formula1_metadata_sportsdb.py --season 2025 --api-key "$TSD_KEY"
python3 scripts/generate_ufc_metadata.py --season 2025
python3 scripts/generate_premier_league_metadata_sportsdb.py --season 2025-2026
```

- Credentials come from a repo-level `.env` (gitignored): `SPORTSDB_API_KEY` and `SPORTSDB_API_VERSION` (`v1` free tier, `v2` premium). `--api-key`/`--api-version` override.
- The API version sets the shared rate limiter: 2.1 s between requests on v1, 0.6 s on v2. Don't tighten these.
- Scripts write to `metadata/<sport>/<season>.yaml` by default and download SportsDB artwork into `posters/<sport>/<season>/...` (skip with `--skip-asset-download`). `url_poster` entries are emitted even when downloads fail.
- Shared flags across generators: `--matchweek-start/--stop`, `--request-interval`, `--max-retries`, `--retry-backoff`, `--insecure` (SSL bypass), `--output`, `--summary`, `--sort-title`, `--show-id`. Run any script with `--help`.
- Some generators inject fixed session lists per round (e.g. MotoGP always emits 6 episodes, Formula E 4, Moto3 5; F1 emits 11 or 13 for sprint weekends) even when SportsDB omits sessions, to keep episode numbering stable. Preserve that behavior when editing them.
- Re-run generators when fixtures shift (kickoff changes, NFL flex scheduling, UFC rescheduling) and commit the resulting YAML diff.

## Conventions

- YAML: 2-space indent, double quotes only when needed. Every episode should carry `title`, `originally_available` (or `original_air_date`), `summary`, and `url_poster`. Keep entries chronological with zero-padded sort titles (`01_...`).
- Season `sort_title` uses the `NN_Title` pattern so rounds order correctly in Plex.
- Posters export as JPG at 1000x1500; title cards 1920x1080; overlays as transparent PNG. Lowercase-dash filenames.
- Hand edits to generated YAML (e.g. corrected local kickoff times) are normal and committed directly — but note they will be overwritten if the generator is re-run, so significant fixes belong in the script.
- New files use `.yaml`; existing `.yml` files must keep their names (raw URLs are live in other people's configs).
- `python3 scripts/validate_yaml.py` validates YAML syntax and internal asset references; CI (`.github/workflows/validate.yaml`) runs it on every PR. Broken refs in README/docs/exampleConfig/overlays are errors; missing posters referenced from metadata are warnings (generators emit `url_poster` optimistically).
- Changes to this repo go through pull requests (branch protection on main).

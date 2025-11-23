# Kometa Configs

Curated Plex Meta Manager configurations for sports, movies, and TV. Each YAML file ships with matching posters/title cards plus optional overlays so you can build polished libraries without hunting down artwork.

---

## Quick Start
1. Install [Kometa](https://kometa.wiki/en/latest/).
2. Point your Plex library at one or more metadata files:

```yaml
libraries:
  Sport:
    metadata_files:
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata/formula1/2025.yaml
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata/motogp/2025.yaml
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata/indycar-series/2025.yaml
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata/wrc-2024.yaml
```

3. Enable `assets_for_all: true` so Kometa fetches posters/backgrounds automatically.
4. Review the sport-specific guide (linked below) for folder naming and troubleshooting.

---

## Repository Map
| Path | Description |
| --- | --- |
| `metadata/` | Hand-crafted YAML per sport, league, or tournament. |
| `scripts/` | Python generators that assemble new seasons from APIs/spreadsheets. |
| `posters/` & `images/` | Published artwork plus documentation screenshots. |
| `overlays/` | Ribbon + badge overlays for Plex libraries. |
| `collection_files/` | Drop-in collections such as “New Releases”. |
| `templates/` | Photoshop starting points for posters/title cards/overlays. |
| `docs/` | Setup guides and contribution docs (see template at `docs/SportDocTemplate.md`). |

---

## Supported Sports
| Sport | Seasons Covered | Assets | Guide |
| --- | --- | --- | --- |
| Formula 1 | 2025 (24 rounds) | Metadata, posters, title cards | [Docs](docs/Formula1.md) |
| MotoGP | 2025 (22 rounds) | Metadata, posters, title cards | [Docs](docs/MotoGP.md) |
| IndyCar | 2025 | Metadata, posters, title cards | Coming soon |
| Formula E | 2024-2026 | Metadata, posters, title cards | Coming soon |
| Formula 2 | 2025 | Metadata, posters, title cards | Coming soon |
| WorldSBK | 2023-2025 | Metadata, posters, title cards | Coming soon |
| World Supersport | 2023-2025 | Metadata, posters, title cards | Coming soon |
| World Supersport 300 | 2024-2025 | Metadata, posters, title cards | Coming soon |
| World Rally Championship | 2024 | Metadata, posters, stage cards | Coming soon |
| European Rally Championship | 2024 | Metadata, posters, stage cards | Coming soon |
| Isle of Man TT | Latest events | Metadata, posters, race cards | Coming soon |
| NBA | 2025-2026 | Metadata, posters, title cards | Coming soon |
| NFL | 2025-2026 | Metadata, posters, title cards | Coming soon |
| Premier League | 2025-2026 | Metadata, posters, match cards | Coming soon |
| UEFA Champions League | 2025-2026 | Metadata, posters, match cards | Coming soon |
| Women’s UEFA Euro | 2025 | Metadata, posters, match cards | Coming soon |
| UFC | 2024-2025 | Metadata, posters, title cards | [Docs](docs/UFC.md) |

Need another sport? Duplicate the template at `docs/SportDocTemplate.md`, add your metadata under `metadata/`, and link it in the table via PR.

---

## Sport Guides
- `docs/Formula1.md` – Folder layout, Kometa config, and preview shots for the full 2025 grid.
- `docs/MotoGP.md` – Library settings, naming rules, and troubleshooting for 22-round seasons.
- `docs/UFC.md` – Event numbering, metadata structure, and recommended Plex agents.
- `docs/SportDocTemplate.md` – Copy this structure when documenting a new sport.

Screenshots now live in the individual guides to keep this README scannable.

---

## Movies & TV Enhancements
This repository also ships battle-tested overlays and collections for standard Plex libraries.

### Movies – Replacement Collections
Swap out Plex’s defaults with smarter “New Releases” and “Old Movies Just Added” collections:

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/collection_files/better_new_and_old_movie_releases.yml
```

![new movie releases and old movies just added](https://github.com/s0len/meta-manager-config/blob/main/images/new-movie-releases-and-old-movies-just-added.png)

### Movies – Common Sense Collections

```yaml
- default: content_rating_cs
  template_variables:
    use_separator: false
    collection_mode: hide
    url_poster: https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/commonsense/<<key>>.jpg
```

![Common Sense collection](https://github.com/s0len/meta-manager-config/blob/main/images/commonsense-collection.jpg)

### Movies – Ribbon Background
Run this once before stacking resolution/audio/studio overlays:

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
```

### Movies – Resolution & Audio (Horizontal)

```yaml
- default: resolution
  template_variables:
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/resolution-top-left-horizontal/<<overlay_name>>.png
    horizontal_align: left
    horizontal_offset: 0
    vertical_align: top
    vertical_offset: 0
    final_horizontal_offset: 0
    final_vertical_offset: 0
    back_width: 1000
    back_height: 1500
    back_color: 00
- default: audio_codec
  template_variables:
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/audio-top-left/<<key>>.png
    horizontal_align: left
    horizontal_offset: 0
    vertical_align: top
    vertical_offset: 0
    back_width: 1000
    back_height: 1500
    back_color: 00
```

![movies_resolution_audio_codec_horizontal](https://github.com/s0len/meta-manager-config/assets/35483234/55b9f52c-e057-4a47-939a-4819b50ba4d0)

### Movies – Resolution & Audio (45°)

```yaml
- default: resolution
  template_variables:
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/resolution-top-left-45deg/<<overlay_name>>.png
    horizontal_align: left
    horizontal_offset: 0
    vertical_align: top
    vertical_offset: 0
    final_horizontal_offset: 0
    final_vertical_offset: 0
    back_width: 1000
    back_height: 1500
    back_color: 00
- default: audio_codec
  template_variables:
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/audio-top-left-45deg/<<key>>.png
    horizontal_align: left
    horizontal_offset: 0
    vertical_align: top
    vertical_offset: 0
    back_width: 1000
    back_height: 1500
    back_color: 00
```

![movies_resolution_audio_codec_45degree](https://github.com/s0len/meta-manager-config/assets/35483234/bbb9469c-8190-441d-a23f-9405af21ab7c)

### Movies – Studio & Ribbon Badges

```yaml
- default: studio
  template_variables:
    horizontal_align: left
    horizontal_offset: 0
    vertical_align: top
    vertical_offset: 0
    back_width: 1000
    back_height: 1500
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/studio-top-left/<<key>>.png
    back_color: 00
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_awards.yml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_trending.yml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_imdb.yml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_rotten.yml
```

![studio overlay movies](https://github.com/s0len/meta-manager-config/assets/35483234/467d2aa1-afc7-4d7e-b038-425492e1c880)
![movies_awards](https://github.com/s0len/meta-manager-config/assets/35483234/24b8f0c2-74aa-4395-8265-ca0c6820a38b)
![movies_imdb](https://github.com/s0len/meta-manager-config/assets/35483234/6dfa41b0-568c-4a20-846c-753792f34929)
![movies_rotten](https://github.com/s0len/meta-manager-config/assets/35483234/6b0a7070-e5e3-4e13-aed5-73e1ab2cc8bf)

### TV – Replacement Collections

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/collection_files/better_new_and_old_tv_shows_releases.yml
```

![new tv show releases and old TV Shows just added](https://github.com/s0len/meta-manager-config/blob/main/images/new-movie-releases-and-old-tv-shows-just-added.png)

### TV – Status + Network Overlays

```yaml
- default: status
  template_variables:
    text_airing: .
    url_airing: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status-top-left/airing.png
    text_returning: .
    url_returning: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status-top-left/continuing.png
    text_canceled: .
    url_canceled: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status-top-left/cancelled.png
    text_ended: .
    url_ended: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status-top-left/ended.png
    horizontal_align: left
    horizontal_offset: 25
    vertical_align: top
    vertical_offset: 0
    font_size: 1
    font_color: '#00000000'
    back_color: '#00000000'
    back_width: 1000
    back_height: 1500
    back_padding: 0
    back_line_width: 1000
    final_horizontal_offset: 0
    final_vertical_offset: 0
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/network_fallback.yml
- default: network
  template_variables:
    horizontal_align: left
    horizontal_offset: 0
    vertical_offset: 0
    vertical_align: top
    back_width: 1000
    back_height: 1500
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/network-top-left/<<key>>.png
    back_color: 00
```

![series_status_network_overlay](https://github.com/s0len/meta-manager-config/assets/35483234/f3a64377-b16b-46bc-9a77-4852f3695db4)

### TV – Studio & Streaming Overlays

```yaml
- default: studio
  template_variables:
    horizontal_align: left
    horizontal_offset: 0
    vertical_align: top
    vertical_offset: 0
    back_width: 1000
    back_height: 1500
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/studio-top-left/<<key>>.png
    back_color: 00
- default: streaming
  template_variables:
    horizontal_align: left
    horizontal_offset: 0
    vertical_offset: 0
    vertical_align: top
    back_width: 1000
    back_height: 1500
    url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/streaming-top-left/<<key>>.png
    back_color: 00
```

![studio overlay shows](https://github.com/s0len/meta-manager-config/assets/35483234/c5763240-abdd-4810-860c-5d78eef07521)

### TV – Award/Trending/Rating Ribbons

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_awards.yml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_trending.yml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_imdb.yml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_rotten.yml
```

---

## Automation & Scripts
- `scripts/generate_nba_metadata.py` – Builds the full NBA season (games, rounds, key art) directly from league schedules.
- `scripts/generate_motogp_metadata_sportsdb.py` – Pulls TheSportsDB data to assemble MotoGP weekends plus session posters.
- Additional scripts follow the same pattern (collect data ➜ normalize ➜ emit YAML). Run them before major season updates and commit the resulting metadata changes.

Document your workflow in the relevant sport guide so others can regenerate new seasons confidently.

---

## Contributing
Read `docs/contributing.md` for the full workflow, naming rules, and submission checklist. Highlights:
- Fork → branch → PR with screenshots where helpful.
- Validate YAML (lint) and double-check that asset filenames match metadata references.
- Follow the sport doc template when adding documentation for a new league.

### Available Photoshop Templates
- `templates/formula1_posters.psd`
- `templates/formula1_title_card.psd`
- `templates/uefa-euro-2024-titlecards.psd`
- `templates/WSBK-poster.psd`
- `templates/poster_overlay_network.psd`
- `templates/poster_overlay_streaming_service.psd`

---

## Support
Questions? Open an issue or reach out on Discord (`@s0len`).  
If these configs save you time, consider supporting the work:

<a href="https://www.buymeacoffee.com/solen" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>

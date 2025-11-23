# Contributing Guide

## How to Work on This Repo
1. **Fork & clone** `https://github.com/s0len/meta-manager-config`.
2. Create a feature branch named `feature/<short-description>`.
3. Make your changes (metadata, scripts, assets, docs).
4. Run validations (YAML lint, script dry-runs, spellcheck if available).
5. Commit with a descriptive message and open a Pull Request.

PRs should describe:
- What sport or overlay you touched.
- Assets that were added or updated (include sample filenames).
- Any scripts or docs that need re-running after merge.

## Repository Expectations
- Keep YAML formatted with 2 spaces, double quotes only when needed.
- Prefer ASCII characters in filenames unless the source name requires accents.
- Place new metadata under `metadata/<sport>/` or `metadata/<league-season>.yaml` following existing patterns.
- Store posters/backgrounds/title cards in `posters/<sport>/<season>/` or `images/` for documentation shots.

## Adding Posters & Title Cards
1. Start from the Photoshop templates inside `templates/`.
2. Export posters as JPG (max quality) at 1000x1500; export overlays/title cards as transparent PNG.
3. Name files `sport-season-event_variant.ext` using lowercase and dashes (e.g., `f1-2025-round-03-race.jpg`).
4. Run `scripts/validate_assets.py` (coming soon) or spot-check dimensions before committing.
5. Update corresponding metadata YAML `url_poster` / `url_background` entries.

### Submission Checklist
- [ ] Asset dimensions follow the template (posters 1000x1500, title cards 1920x1080 unless noted).
- [ ] No watermarks or licensed imagery you cannot share.
- [ ] File names match metadata references exactly.
- [ ] Preview screenshot added to `images/` if showcasing UI changes.

## Creating or Updating Metadata
- Use the generator scripts in `scripts/` when available; otherwise, copy an existing YAML and adjust fields.
- Include `original_air_date`, `summary`, and `url_poster` for every entry.
- Keep episodes/events ordered chronologically and use zero-padded numbering (`01`, `02`, …).
- After editing, run `python scripts/validate_yaml.py <path>` (TBD) or a YAML linter to catch syntax errors.

## Docs & Communication
- Follow the `docs/SportDocTemplate.md` structure when documenting a sport.
- Link new docs from the README Supported Sports table.
- For questions, open a GitHub issue or ping @s0len on Discord.

## Licensing
All contributions are MIT licensed once merged. Only submit assets you created or have rights to redistribute.


# Contributing Guide

## How to Work on This Repo
1. **Fork & clone** `https://github.com/s0len/meta-manager-config`.
2. Create a feature branch named `feature/<short-description>`.
3. Make your changes (metadata, scripts, assets, docs).
4. Run `python3 scripts/validate_yaml.py` — it checks YAML syntax and that
   every internal asset reference resolves. CI runs the same check on your PR.
5. Commit with a descriptive message and open a Pull Request.

PRs should describe:
- What sport or overlay you touched.
- Assets that were added or updated (include sample filenames).
- Any scripts or docs that need re-running after merge.

## Repository Expectations
- Keep YAML formatted with 2 spaces, double quotes only when needed. Name new files `.yaml`; existing `.yml` files keep their names because their raw URLs are referenced by other people's configs.
- Prefer ASCII characters in filenames unless the source name requires accents.
- Place new metadata under `metadata/<sport>/` or `metadata/<league-season>.yaml` following existing patterns.
- Store posters/backgrounds/title cards in `posters/<sport>/<season>/` or `images/` for documentation shots.

## Adding Posters & Title Cards
1. Start from the Photoshop templates inside `templates/`.
2. Export posters as JPG (max quality) at 1000x1500; export overlays/title cards as transparent PNG.
3. Name files `sport-season-event_variant.ext` using lowercase and dashes (e.g., `f1-2025-round-03-race.jpg`).
4. Run `python3 scripts/validate_yaml.py` to confirm your asset filenames match the metadata references, and spot-check dimensions before committing.
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
- After editing, run `python3 scripts/validate_yaml.py` to catch syntax errors and broken asset references (CI runs it on every PR).

## Adding Series Title Cards

`metadata/series/title_cards.yaml` is a community-maintained file mapping TVDB
ids to MediUX artwork — this is what powers the
[TV – Title Cards](README.md#tv--title-cards-community-maintained) section of
the README. To add or update a show:

1. Go to [mediux.pro](https://mediux.pro) and search for the show.
2. Open the set you want — pick one that actually has **title cards** (episode
   artwork), not just a poster set.
3. Use the set's **copy YAML** button to grab the Kometa block.
4. Open `metadata/series/title_cards.yaml` and search for the show (by name in
   the credit comments, or by its TVDB id):
   - **Already there?** Replace the existing block with the new one — don't
     leave two entries for the same id, the later one silently wins.
   - **Not there?** Add it as a new entry under `metadata:`.
5. Fix up the pasted YAML before committing — MediUX doesn't always emit a
   complete block, and a missing key means the whole file fails to parse for
   *everyone* consuming the URL:
   - The block **must** be keyed by the show's **TVDB id** (not the show name,
     not a TMDb id).
   - Every season **must** have its own numbered key under `seasons:`; episodes
     hang off `episodes:` inside it. Episode entries with no season above them
     are a parse error.
   - Indentation is 2 spaces, and the whole entry sits one level under
     `metadata:`.
6. Keep the credit comment on the id line so the set creator is credited:
   `# TVDB id for <Show>. Set by <creator> on MediUX. <link to set>`
7. Run `python3 scripts/validate_yaml.py` and open a PR.

The expected shape:

```yaml
metadata:
  436198: # TVDB id for Common Side Effects. Set by willtong93 on MediUX. https://mediux.pro/sets/31255
    url_poster: https://api.mediux.pro/assets/f3c7ce8f-e165-4617-9118-6ffaab592697
    url_background: https://api.mediux.pro/assets/97644f6e-d06a-4d76-855f-f5de9f6c67e1
    seasons:
      1:
        url_poster: https://api.mediux.pro/assets/54613457-78a1-4290-a3ba-38ba25c8cc83
        episodes:
          1:
            url_poster: https://api.mediux.pro/assets/a39ae3eb-764b-4a03-83b4-0162018c8aa7
          2:
            url_poster: https://api.mediux.pro/assets/eed3b585-faa8-4974-b402-95a8677afbf7
```

## Docs & Communication
- Follow the `docs/SportDocTemplate.md` structure when documenting a sport.
- Link new docs from the README Supported Sports table.
- For questions, open a GitHub issue or ping @s0len on Discord.

## Licensing
All contributions are MIT licensed once merged. Only submit assets you created or have rights to redistribute.


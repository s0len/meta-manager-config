# Sport Guide Template

Use this template when creating or updating `docs/<Sport>.md`. Each section keeps terminology consistent across guides and makes it easy for contributors to find the information they need.

1. **Title & Summary**
   - `# <Sport> Metadata Guide`
   - One or two sentences about coverage (years, events) and assets (metadata, posters, title cards).

2. **At a Glance**
   - Bullet list of seasons covered, YAML path(s), asset folders, automation scripts.
   - Optional status badges (✅ complete, ⚙️ in-progress).

3. **Library Requirements**
   - Recommended Plex/Kometa library type, scanner, agent, sort order, and any naming prerequisites.

4. **Folder & Naming Structure**
   - Tree diagram showing top-level season/event folders and SxxExx naming. Note deviations (e.g., UFC event numbering).

5. **Kometa Configuration**
   - Ready-to-copy YAML snippet pointing to the correct metadata file(s) plus `operations` flags.
   - Mention environment variables or API keys if scripts require them.

6. **What the Metadata Provides**
   - Table or bullets describing season, event, and session fields plus included posters/title cards.

7. **Assets**
   - Paths to posters/backgrounds/title cards, resolution guidelines, and preview images.

8. **Updating for a New Season**
   - Step-by-step workflow for running generator scripts, validating YAML, uploading assets, and updating docs.

9. **Troubleshooting & FAQ**
   - Common issues (missing metadata, asset download failures) and quick fixes.

10. **Change Log (Optional)**
   - Brief bullets noting last updated season or major additions.

Keep tone instructional, reuse existing screenshots via `images/`, and include relative links (`../metadata/...`). When adding a new sport, duplicate this template, fill out each section, and link the new guide from the README Supported Sports table.


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


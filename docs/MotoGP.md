# MotoGP Metadata Guide

This guide explains how to set up and organize your MotoGP content in Plex with proper metadata using the YAML configuration.

## File Structure

For MotoGP to display correctly in Plex with metadata, organize your files in this structure:

```txt
media/motorsport/
└── MotoGP 2025/                        # Main season folder (matches title in YAML)
    ├── 01 Thailand/                    # Race weekend folder (numbered sequentially)
    │   ├── 01x01 Practice One.mkv      # Session files (SXXEXX format)
    │   ├── 01x02 Practice Two.mkv
    │   ├── 01x03 Qualifying One.mkv
    │   ├── 01x04 Qualifying Two.mkv
    │   ├── 01x05 Sprint.mkv
    │   └── 01x06 Race.mkv
    ├── 02 Argentina/                   # Next race weekend
    │   └── [similar session files]
    └── [remaining race folders]
```

**Important naming conventions:**
- Main folder should match the title from YAML (`MotoGP 2025`)
- Race folders should be numbered sequentially (e.g., `01 Thailand`, `02 Argentina`)
- Session files should follow the SxxExx format (`01x01`, `01x02`, etc.)
- Session filenames should match episode titles in the YAML

## Example for 2025 Season

Based on the `motogp_2025.yaml` file, the correct folder structure for the first few races would be:

```txt
MotoGP 2025/
├── 01 Thailand/                    # Round 01 PT Grand Prix of Thailand
│   ├── 01x01 Practice One.mkv
│   ├── 01x02 Practice Two.mkv
│   ├── 01x03 Qualifying One.mkv
│   ├── 01x04 Qualifying Two.mkv
│   ├── 01x05 Sprint.mkv
│   └── 01x06 Race.mkv
├── 02 Argentina/                   # Round 02 Gran Premio de la República Argentina
├── 03 USA/                         # Round 03 Red Bull Grand Prix of The Americas
├── 04 Qatar/                       # Round 04 Qatar Airways Grand Prix of Qatar
├── 05 Spain/                       # Round 05 Gran Premio Estrella Galicia 0,0 de España
```

Continue this pattern for all 22 races in the 2025 season. The folder names should be simple (e.g., "01 Thailand") while the detailed race titles will come from the YAML metadata.

<think>The image shows a Plex library settings screen for a library named "Motorsport". I'll analyze the key settings shown that would be relevant for setting up MotoGP content properly:

1. **Scanner**: Set to "Plex Series Scanner" - This is correct for TV-style content like MotoGP where each race weekend is like a season and each session is like an episode.

2. **Agent**: Set to "Personal Media Shows" - This appears to be the agent selected for metadata matching.

3. **Visibility**: Set to "Include in home screen and global search" - This makes the MotoGP content visible on the main Plex interface.

4. **Episode sorting**: Set to "Oldest first" - This ensures race weekends and sessions appear in chronological order (race 1 first, then race 2, etc.)

5. **Enable video preview thumbnails**: This is checked, which will generate preview thumbnails for the MotoGP content.

These settings align with what would be needed for properly organizing MotoGP content as described in the MotoGP.md document. I should explain why these settings are appropriate and if any additional settings might be needed for optimal operation with the metadata files.</think># Required Plex Settings for MotoGP Metadata

Based on the screenshot, here are the recommended settings for your Motorsport library to work correctly with the MotoGP metadata:

## Essential Settings for Plex Library

- **Scanner**: "Plex Series Scanner" ✓
  This scanner correctly interprets the SxxExx format used for MotoGP sessions.

- **Agent**: "Personal Media Shows" ✓
  This agent allows Kometa to apply the custom metadata from your YAML files.

- **Episode sorting**: "Oldest first" ✓
  Ensures races appear in chronological order throughout the season.

- **Visibility**: "Include in home screen and global search" is recommended for easy access.

![Plex library settings for sports](https://github.com/s0len/meta-manager-config/blob/main/images/correct-plex-libary-setting.png)

## Adding Metadata to Plex

To add the MotoGP metadata to Plex, we use Kometa (a Plex metadata manager). Add this configuration to your Kometa config file:

```yaml
libraries:
  Motorsport: # This is your Plex Library containing MotoGP
    metadata_files:
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata_files/motogp_2025.yaml
    operations:
      assets_for_all: true
```

This configuration:
1. Identifies your Plex library containing MotoGP content
2. Points to the YAML metadata file with all the MotoGP 2025 information
3. Enables downloading of all assets (posters, backgrounds) for the content

## What the YAML Provides

The `motogp_2025.yaml` file provides:

- **Season metadata**: Title, summary, poster, and background for the 2025 MotoGP season
- **Race weekend metadata**: Title, summary, and poster for each of the 22 Grand Prix weekends
- **Session metadata**: Title and poster for each session (practices, qualifyings, sprint, race)

## 2025 Season Overview

The 2025 MotoGP season features 22 rounds, beginning in Thailand and concluding in Valencia. Notable additions to the 2025 calendar include the return of Czechia (Round 12) and the debut of Hungary (Round 14).

The full season includes:
1. Thailand (Buriram)
2. Argentina (Termas de Río Hondo)
3. USA (Circuit of the Americas)
4. Qatar (Losail)
5. Spain (Jerez)
6. France (Le Mans)
7. United Kingdom (Silverstone)
8. Aragon (MotorLand Aragón)
9. Italy (Mugello)
10. Netherlands (Assen)
11. Germany (Sachsenring)
12. Czechia (Brno)
13. Austria (Red Bull Ring)
14. Hungary (New circuit)
15. Catalonia (Barcelona)
16. San Marino (Misano)
17. Japan (Motegi)
18. Indonesia (Mandalika)
19. Australia (Phillip Island)
20. Malaysia (Sepang)
21. Portugal (Portimão)
22. Valencia (Circuit Ricardo Tormo)

## Troubleshooting

If metadata doesn't appear correctly:
- Verify your folder and file naming matches the structure described above
- Ensure your Kometa configuration is pointing to the correct YAML file
- Check that the YAML file is accessible at the specified URL
- Run a Kometa metadata refresh operation after making any changes

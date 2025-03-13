# UFC Metadata Guide

This guide explains how to set up and organize your UFC content in Plex with proper metadata using the YAML configuration.

## File Structure

For UFC to display correctly in Plex with metadata, organize your files in this structure:

```txt
media/sports/
└── UFC/                           # Main UFC folder (matches title in YAML)
    ├── 300/                       # Event folder (numbered by UFC event)
    │   ├── 300x01 Early Prelims.mkv  # Session files (SXXEXX format)
    │   ├── 300x02 Prelims.mkv
    │   └── 300x03 Main Card.mkv
    ├── 301/                       # Next UFC event
    │   └── [similar session files]
    └── [remaining event folders]
```

**Important naming conventions:**

- Main folder should match the title from YAML (`UFC`)
- Event folders should be numbered by the UFC event number (e.g., `300`, `301`)
- Session files should follow the SxxExx format (`300x01`, `300x02`, etc.)
- Session filenames should match episode titles in the YAML

## Example for 2024 Events

Based on the `ufc.yaml` file, the correct folder structure for the events would be:

```txt
UFC/
├── 300/                           # UFC 300
│   ├── 300x01 Early Prelims - Figueiredo vs Garbrandt.mkv
│   ├── 300x02 Prelims - Sterling vs Kattar.mkv
│   └── 300x03 Main Card - Pereira vs Hill.mkv
├── 301/                           # UFC 301
│   ├── 301x01 Early Prelims - Costa vs Hernandez.mkv
│   ├── 301x02 Prelims - Borralho vs Craig.mkv
│   └── 301x03 Main Card - Pantoja vs Erceg.mkv
├── 302/                           # UFC 302
│   ├── 302x01 Early Prelims.mkv
│   ├── 302x02 Prelims.mkv
│   └── 302x03 Main Card.mkv
```

Continue this pattern for all UFC events. The folder names should be the UFC event number while the detailed event titles will come from the YAML metadata.

## Required Plex Settings for UFC Metadata

Here are the recommended settings for your Sports library to work correctly with the UFC metadata:

### Essential Settings for Plex Library

- **Scanner**: "Plex Series Scanner"
  This scanner correctly interprets the SxxExx format used for UFC sessions.

- **Agent**: "Personal Media Shows"
  This agent allows Plex Meta Manager to apply the custom metadata from your YAML files.

- **Episode sorting**: "Oldest first"
  Ensures events appear in chronological order.

- **Visibility**: "Include in home screen and global search" is recommended for easy access.

## Adding Metadata to Plex

To add the UFC metadata to Plex, use Plex Meta Manager. Add this configuration to your PMM config file:

```yaml
libraries:
  Sports: # This is your Plex Library containing UFC
    metadata_files:
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata-files/ufc.yaml
    operations:
      assets_for_all: true
```

This configuration:

1. Identifies your Plex library containing UFC content
2. Points to the YAML metadata file with all the UFC information
3. Enables downloading of all assets (posters, backgrounds) for the content

## What the YAML Provides

The `ufc.yaml` file provides:

- **Main metadata**: Title, summary, poster, and background for UFC
- **Event metadata**: Title, summary, and poster for each UFC event
- **Session metadata**: Title and poster for each session (Early Prelims, Prelims, Main Card)

## 2024-2025 Events Overview

The UFC events featured in the metadata include:

1. **UFC 300** (April 13, 2024) - Historic milestone event with three championship bouts
2. **UFC 301** (May 4, 2024) - Flyweight championship in Rio de Janeiro
3. **UFC 302** (June 1, 2024) - Lightweight championship in Newark
4. **UFC 303** (June 29, 2024) - Light heavyweight championship in Las Vegas
5. **UFC 304** (July 27, 2024) - Welterweight championship in Manchester
6. **UFC 305** (August 17, 2024) - Middleweight championship in Perth
7. **UFC 306** (September 14, 2024) - Bantamweight championship at The Sphere
8. **UFC 307** (October 5, 2024) - Light heavyweight championship in Salt Lake City
9. **UFC 308** (October 26, 2024) - Featherweight championship in Abu Dhabi
10. **UFC 309** (November 16, 2024) - Heavyweight championship at Madison Square Garden
11. **UFC 310** (December 7, 2024) - Flyweight championship in Las Vegas
12. **UFC 311** (January 18, 2025) - Lightweight championship in Inglewood
13. **UFC 312** (February 8, 2025) - Middleweight championship in Sydney
14. **UFC 313** (March 8, 2025) - Light heavyweight championship at Allegiant Stadium
15. **UFC 314** (April 12, 2025) - Featherweight contender bout in Miami
16. **UFC 315** (May 10, 2025) - Welterweight championship in Montreal

## Troubleshooting

If metadata doesn't appear correctly:

- Verify your folder and file naming matches the structure described above
- Ensure your Plex Meta Manager configuration is pointing to the correct YAML file
- Check that the YAML file is accessible at the specified URL
- Run a Plex Meta Manager metadata refresh operation after making any changes

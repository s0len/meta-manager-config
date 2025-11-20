# Formula 1 Complete Metadata with Posters and Title Cards

This configuration provides comprehensive metadata for Formula 1 seasons, including high-quality posters and title cards for all race weekends and sessions. The 2025 season features 24 rounds with detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## Implementation

Add the following to your Plex Meta Manager configuration:

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/metadata/formula1-2025.yaml
```

This will create a fully structured Formula 1 2025 season with:
- Detailed season summary
- Pre-season testing sessions
- 24 Grand Prix weekends with race-specific descriptions
- All practice sessions, qualifying, sprint races, and main races properly labeled
- Press conferences and pre/post-show content

## Folder Structure

For optimal results, organize your Formula 1 content with this structure:

```
Formula 1/
├── 2025/
│   ├── Pre-Season Testing/
│   │   ├── Session 1.mp4
│   │   ├── Session 2.mp4
│   │   └── ...
│   ├── Round 01 Australian Grand Prix/
│   │   ├── Drivers Press Conference.mp4
│   │   ├── Weekend Warm Up.mp4
│   │   ├── Free Practice 1.mp4
│   │   ├── Free Practice 2.mp4
│   │   ├── Free Practice 3.mp4
│   │   ├── Pre Qualifying Show.mp4
│   │   ├── Qualifying.mp4
│   │   ├── Post Qualifying Show.mp4
│   │   ├── Pre Race Show.mp4
│   │   ├── Race.mp4
│   │   └── Post Race Show.mp4
│   └── ...
```

## Preview

![view of created F1 collections](https://github.com/s0len/meta-manager-config/blob/main/images/f1-view-of-collections.png)
![view of created F1 title cards](https://github.com/s0len/meta-manager-config/blob/main/images/f1-view-of-title-cards.png)

For more detailed instructions on naming conventions and configuration options, check the [full Formula 1 setup guide](docs/Formula1.md).

# Kometa Configs

This is where you'll find all my config files related to Kometa. I've included an example of how you could fire off each overlay in my example config [exampleConfig.yml](https://raw.githubusercontent.com/s0len/meta-manager-config/main/exampleConfig.yml).

<a href="https://www.buymeacoffee.com/solen" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

## Formula 1 Complete Metadata with Posters and Title Cards

This configuration provides comprehensive metadata for Formula 1 seasons, including high-quality posters and title cards for all race weekends and sessions. The 2025 season features 24 rounds with detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

[Read the full Formula 1 setup guide](docs/Formula1.md) for detailed instructions on folder structure, naming conventions, and configuration.

![view of created F1 collections](https://github.com/s0len/meta-manager-config/blob/main/images/f1-view-of-collections.png)
![view of created F1 title cards](https://github.com/s0len/meta-manager-config/blob/main/images/f1-view-of-title-cards.png)

## MotoGP Complete Metadata with Posters and Title Cards

This configuration provides comprehensive metadata for MotoGP seasons, including high-quality posters and title cards for all race weekends and sessions. The 2025 season features 22 rounds with detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

[Read the full MotoGP setup guide](docs/MotoGP.md) for detailed instructions on folder structure, naming conventions, and configuration.

![view of created collections and how they look](https://github.com/s0len/meta-manager-config/blob/main/images/motogp-view-of-collections.png)
![view of created title cards and how they look](https://github.com/s0len/meta-manager-config/blob/main/images/motogp-view-of-title-cards.png)

## IndyCar Complete Metadata

This configuration provides comprehensive metadata for IndyCar seasons, including high-quality posters and title cards for all race weekends and sessions. The 2025 season features detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## Formula E Complete Metadata

This configuration provides comprehensive metadata for Formula E seasons, including high-quality posters and title cards for all race weekends and sessions. The 2025 season features detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## Formula 2 Complete Metadata

This configuration provides comprehensive metadata for Formula 2 seasons, including high-quality posters and title cards for all race weekends and sessions. The 2025 season features detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## WorldSBK Complete Metadata

This configuration provides comprehensive metadata for World Superbike (WorldSBK) seasons, including high-quality posters and title cards for all race weekends and sessions. The 2023-2025 seasons feature detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## World Supersport (WSSP) Complete Metadata

This configuration provides comprehensive metadata for World Supersport (WSSP) seasons, including high-quality posters and title cards for all race weekends and sessions. The 2023-2025 seasons feature detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## World Supersport 300 (WSSP300) Complete Metadata

This configuration provides comprehensive metadata for World Supersport 300 (WSSP300) seasons, including high-quality posters and title cards for all race weekends and sessions. The 2024-2025 seasons feature detailed information for each event.

**Features:**
- Season posters and backgrounds
- Race weekend posters and summaries
- Session-specific title cards
- Complete structural metadata

## World Rally Championship (WRC) Complete Metadata

This configuration provides comprehensive metadata for World Rally Championship seasons, including high-quality posters and title cards for all rally events and stages. The 2024 season features detailed information for each event.

**Features:**
- Season posters and backgrounds
- Rally event posters and summaries
- Stage-specific title cards
- Complete structural metadata

## European Rally Championship (ERC) Complete Metadata

This configuration provides comprehensive metadata for European Rally Championship seasons, including high-quality posters and title cards for all rally events and stages. The 2024 season features detailed information for each event.

**Features:**
- Season posters and backgrounds
- Rally event posters and summaries
- Stage-specific title cards
- Complete structural metadata

## Isle of Man TT Complete Metadata

This configuration provides comprehensive metadata for the Isle of Man TT motorcycle races, including high-quality posters and title cards for all sessions and races.

**Features:**
- Event posters and backgrounds
- Race-specific title cards
- Complete structural metadata
- Detailed race information

## UFC Complete Metadata with Posters and Title Cards

This configuration provides comprehensive metadata for UFC events, including high-quality posters and title cards for all fight cards and sessions. The 2024-2025 schedule features major events with detailed information for each fight card.

**Features:**
- Event posters and backgrounds 
- Session-specific title cards (Early Prelims, Prelims, Main Card)
- Complete structural metadata
- Fighter matchup details
- Event summaries and results

[Read the full UFC setup guide](docs/UFC.md) for detailed instructions on folder structure, naming conventions, and configuration.

![view of created UFC collections](https://github.com/s0len/meta-manager-config/blob/main/images/ufc-view-of-collections.png)
![view of created UFC title cards](https://github.com/s0len/meta-manager-config/blob/main/images/ufc-view-of-title-cards.png)


## Movies

Below you'll find the yaml config which then if used will generate the image below.

### Creates two collections which replace Plex default "New Releases" collection for Movies

These collections are a substantial improvement upon Plex defaults. New Releases shows Movies which has been added in the last 92 days to the Library AND has been Released in the last 365 days. This means in this collection you will always find the freshest media available.
Old Movies Just Added however is a collection of Movies who has been Released more then 365 days ago AND has been added to the Library in the last 30 days. This means in this collection you will find all the Movies which has just recently been added to the Library but has been around for longer then a year.

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/collection_files/better_new_and_old_movie_releases.yml
```

![new movie releases and old movies just added](https://github.com/s0len/meta-manager-config/blob/main/images/new-movie-releases-and-old-movies-just-added.png)

### Common Sense Collection with custom posters

Creates collections for all your media inside the library and sorts it according to the age restriction based on Common Sense.

```yaml
    - default: content_rating_cs
      template_variables:
        use_separator: false
        collection_mode: hide
        url_poster: https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/commonsense/<<key>>.jpg
```

![new movie releases and old movies just added](https://github.com/s0len/meta-manager-config/blob/main/images/commonsense-collection.jpg)

### Creates a ribbon style background in the top left corner with a width of 313 pixels

**Keep in mind**, it has to be run before any overlay which is supposed to be on top of the background**

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
```

### Resolution in the upper left corner in horizontal format

```yaml
# Creates a ribbon style background in the top left corner with a width of 313 pixels. Keep in mind, it has to be run before any overlay which is supposed to be on top of the background
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
# Resolution in the upper left corner in horizontal format
- default: resolution
      template_variables:
            url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/resolution-top-left-horizontal/<<overlay_name>>.png
            horizontal_align: left
            horizontal_offset: 0
            vertical_offset: 0
            vertical_align: top
            final_horizontal_offset: 0
            final_vertical_offset: 0
            back_width: 1000
            back_height: 1500
            back_color: 00
```

### Audio in the upper left corner in horizontal format

```yaml
# Creates a ribbon style background in the top left corner with a width of 313 pixels. Keep in mind, it has to be run before any overlay which is supposed to be on top of the background
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
# Audio in the upper left corner in horizontal format
- default: audio_codec
      template_variables:
          url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/audio-top-left/<<key>>.png
          horizontal_align: left
          horizontal_offset: 0
          vertical_offset: 0
          vertical_align: top
          back_width: 1000
          back_height: 1500
          back_color: 00
```

![movies_resolution_audio_codec_horizontal](https://github.com/s0len/meta-manager-config/assets/35483234/55b9f52c-e057-4a47-939a-4819b50ba4d0)

### Creates a ribbon style background in the top left corner with a width of 313 pixels. Keep in mind, it has to be run before any overlay which is supposed to be on top of the background

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
```

### Resolution in the upper left corner in 45 degree format

```yaml
# Creates a ribbon style background in the top left corner with a width of 313 pixels. Keep in mind, it has to be run before any overlay which is supposed to be on top of the background
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
# Resolution in the upper left corner in 45 degree format
- default: resolution
      template_variables:
            url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/resolution-top-left-45deg/<<overlay_name>>.png
            horizontal_align: left
            horizontal_offset: 0
            vertical_offset: 0
            vertical_align: top
            final_horizontal_offset: 0
            final_vertical_offset: 0
            back_width: 1000
            back_height: 1500
            back_color: 00
```

### Audio in the upper left corner in 45 degree format

```yaml
# Creates a ribbon style background in the top left corner with a width of 313 pixels. Keep in mind, it has to be run before any overlay which is supposed to be on top of the background
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
# Audio in the upper left corner in 45 degree format
- default: audio_codec
      template_variables:
          url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/audio-top-left-45deg/<<key>>.png
          horizontal_align: left
          horizontal_offset: 0
          vertical_offset: 0
          vertical_align: top
          back_width: 1000
          back_height: 1500
          back_color: 00
```

![movies_resolution_audio_codec_45degree](https://github.com/s0len/meta-manager-config/assets/35483234/bbb9469c-8190-441d-a23f-9405af21ab7c)

### Studio overlay in ribbon style in the top left corner

```yaml
# Creates a ribbon style background in the top left corner with a width of 313 pixels. Keep in mind, it has to be run before any overlay which is supposed to be on top of the background
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
# Studio overlay in ribbon style in the top left corner
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
```

![studio overlay movies](https://github.com/s0len/meta-manager-config/assets/35483234/467d2aa1-afc7-4d7e-b038-425492e1c880)

### Award ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_awards.yml
```

![movies_awards](https://github.com/s0len/meta-manager-config/assets/35483234/24b8f0c2-74aa-4395-8265-ca0c6820a38b)

### Trending ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_trending.yml
```

### IMDB ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_imdb.yml
```

![movies_imdb](https://github.com/s0len/meta-manager-config/assets/35483234/6dfa41b0-568c-4a20-846c-753792f34929)

### Rotten tomatoes ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_rotten.yml
```

![movies_rotten](https://github.com/s0len/meta-manager-config/assets/35483234/6b0a7070-e5e3-4e13-aed5-73e1ab2cc8bf)

## TV Shows

Below the you'll find the yaml config which then if used will generate the image below.

### Creates two collections which replace Plex default "New Releases" for TV Shows

These collections are a substantial improvement upon Plex defaults. New Releases shows TV Shows which has been added in the last 92 days to the Library AND has been Released in the last 365 days. This means in this collection you will always find the freshest media available.
Old TV Shows Just Added however is a collection of TV Shows who has been Released more then 365 days ago AND has been added to the Library in the last 30 days. This means in this collection you will find all the TV Shows which has just recently been added to the Library but has been around for longer then a year.

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/collection_files/better_new_and_old_tv_shows_releases.yml
```

![new tv show releases and old TV Shows just added](https://github.com/s0len/meta-manager-config/blob/main/images/new-movie-releases-and-old-tv-shows-just-added.png)

### Status in the top left corner

```yaml
- default: status
      template_variables:
          text_airing: .
          url_airing: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status-top-left/airing.png
          text_returning: .
          url_returning: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status-top-left/returning.png
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
          back_width_airing: 1000
          back_width_returning: 1000
          back_width_ended: 1000
          back_width_cancelled: 1000
          back_width: 1000
          back_height_airing: 1500
          back_height_returning: 1500
          back_height_ended: 1500
          back_height_cancelled: 1500
          back_height: 1500
          back_padding: 0
          back_line_width: 1000
          final_horizontal_offset: 0
          final_vertical_offset: 0
```

### Fallback Network logo

This is a bit of a workaround to fill up the missing network logos by first writing a plex logo on all overlays. Then AFTER this is run we run the below `default: network` so that it is overwritten by default: network if it finds an image for the network.
**Must run before `default: network`.**

```yml
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/network_fallback.yml
```

### Network the show originated from in the top left corner

```yaml
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

### Studio overlay in ribbon style in the top left corner

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
```

![studio overlay shows](https://github.com/s0len/meta-manager-config/assets/35483234/c5763240-abdd-4810-860c-5d78eef07521)

### Streaming Service in the upper left corner

```yaml
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

### Award ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_awards.yml
```

### Trending ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_trending.yml
```

### IMDB ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_imdb.yml
```

### Rotten tomatoes ribbons in the bottom right corner

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon_rotten.yml
```


# Plex Meta Manager Configs

This is where you'll find all my config files related to Plex Meta Manager. I've included an example of how you could fire off each overlay in my example config [exampleConfig.yml](https://raw.githubusercontent.com/s0len/meta-manager-config/main/exampleConfig.yml).

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
    - pmm: content_rating_cs
      template_variables:
        use_separator: false
        collection_mode: hide
        url_poster: https://raw.githubusercontent.com/s0len/meta-manager-config/main/posters/commonsense/<<key>>.jpg
```

![new movie releases and old movies just added](https://github.com/s0len/meta-manager-config/blob/main/images/commonsense-collection.png)

### Creates a ribbon style background in the top left corner with a width of 313 pixels

**Keep in mind**, it has to be run before any overlay which is supposed to be on top of the background**

```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/background_top_left_313_wide.yml
```

### Resolution in the upper left corner in horizontal format

```yaml
- pmm: resolution
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
- pmm: audio_codec
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
- pmm: resolution
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
- pmm: audio_codec
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
- pmm: studio
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
- pmm: status
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

This is a bit of a workaround to fill up the missing network logos by first writing a plex logo on all overlays. Then AFTER this is run we run the below `pmm: network` so that it is overwritten by pmm: network if it finds an image for the network.
**Must run before `pmm: network`.**

```yml
      - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/network_fallback.yml
```

### Network the show originated from in the top left corner

```yaml
- pmm: network
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
- pmm: studio
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
- pmm: streaming
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

## Formula 1 poster overlay

Complete config for Formula 1 with awesome posters.

### This requires your folder structure to be like this

```txt
Formula                                   -> Library Folder
└── Formula1 2023                           -> Folder for each F1 Season
    └── 04 - Azerbaijan GP                -> Folder for each Race in a season
        ├── 04x01 - Azerbaijan GP - Pre-Qualifying Buildup.mkv
        ├── 04x02 - Azerbaijan GP - Qualifying Session.mkv
        ├── 04x03 - Azerbaijan GP - Post-Qualifying Analysis.mkv
        ├── 04x04 - Azerbaijan GP - Ted's Qualifying Notebook.mkv
        ├── 04x05 - Azerbaijan GP - Pre-Sprint Shootout Buildup.mkv
        ├── 04x06 - Azerbaijan GP - Sprint Shootout Session.mkv
        ├── 04x07 - Azerbaijan GP - Post-Sprint Shootout Analysis.mkv
        ├── 04x08 - Azerbaijan GP - Pre-Sprint Race Buildup.mkv
        ├── 04x09 - Azerbaijan GP - Sprint Race Session.mkv
        ├── 04x10 - Azerbaijan GP - Post-Sprint Race Analysis.mkv
        ├── 04x11 - Azerbaijan GP - Ted's Sprint Notebook.mkv
        ├── 04x12 - Azerbaijan GP - Pre-Race Buildup.mkv
        ├── 04x13 - Azerbaijan GP - Race Session.mkv
        ├── 04x14 - Azerbaijan GP - Post-Race Analysis.mkv
        └── 04x15 - Azerbaijan GP - Ted's Race Notebook.mkv
```

### This is the yaml for your config.yml

```yaml
  Formula 1: # This is your plex library
    metadata_files:
    - url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/formula1.yml
    operations:
      assets_for_all: true 
```

![Formula_1_poster_overlay](https://github.com/s0len/meta-manager-config/assets/35483234/ca747f2c-b529-4add-8a95-113c5cf84b25)

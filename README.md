# Plex Meta Manager Configs
This is where you'll find all my config files related to Plex Meta Manager. I've included an example of how you could fire off each overlay in my example config [exampleConfig.yml](https://raw.githubusercontent.com/s0len/meta-manager-config/main/exampleConfig.yml).

## Movies
![Movie_overlay](https://github.com/s0len/meta-manager-config/assets/35483234/36da84a7-d15e-4691-a010-86117d64b16b)
### Resolution in the upper left corner
`- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/resolution.yml`

### Audio in the upper left corner besides resolution
`- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/audio_codec.yml`

### Ribbons in the bottom right corner
`- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/ribbon.yml`

## TV Shows
![series_overlay](https://github.com/s0len/meta-manager-config/assets/35483234/0d578c63-f99d-44da-941e-d51a8a70ef50)

### Status in the top left corner
`- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status.yml`

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

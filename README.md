# Plex Meta Manager Configs
This is where you'll find all my config files related to Plex Meta Manager. I've included an example of how you could fire off each overlay in my example config [exampleConfig.yml](https://raw.githubusercontent.com/s0len/meta-manager-config/main/exampleConfig.yml).

## Movies
![movie overlay res and codec](https://github.com/s0len/meta-manager-config/assets/35483234/b7a6bb56-9415-4883-b9f9-6a03073a5012)

### Resolution as a ribbon style in the upper left corner
```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/resolution.yml
```

### Audio as a ribbon style in the lower right corner
```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/audio_codec.yml
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

## TV Shows
![series-overlay](https://github.com/s0len/meta-manager-config/assets/35483234/d0fac6f2-9114-4cc0-a012-1f5e241fe7a8)

### Status in the top left corner
```yaml
- url: https://raw.githubusercontent.com/s0len/meta-manager-config/main/overlays/status.yml
```

### Fallback Network logo 
This is a bit of a workaround to fill up the missing network logos by first writing a plex logo on all overlays. Then AFTER this is run we run the below `pmm: network` so that it is overwritten by pmm: network if it finds an image for the network. 
** Must run before `pmm: network`. ** 
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

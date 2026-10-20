# corein brand

Decided 2026-10-20. The mark, the wordmark and the app icon are one decision; the in-app
colour system is kept from the project corein forks, because the mark was drawn in ink and
blue so the apps already match it.

## The mark

The **circuit-o**: a ring with three traces inside it, each ending in a node. It is the o of
the wordmark, and alone it is the app icon. Drawn as one compound filled path on a 100-unit
tile, so every generator consumes it unchanged.

- Source of truth: `assets/brand/corein-mark.svg`. Everything else is derived from it.
- `assets/brand/corein-icon.svg`: white squircle tile (`rx=27`), a hairline edge, the mark. This
  is the app icon wherever the icon stands for the app (README, site, favicon).
- `assets/brand/corein-icon-on-dark.svg`: the mark in white on the dark tile, for store
  listings and the splash only.
- `assets/brand/corein-wordmark.svg`: the word **corein**, lower case, in a bold geometric
  sans with the mark as its o. Use it on light fields; on dark fields invert it to white.
- `assets/brand/corein-cover.svg`: the README hero.
- `docs/app-icon.png`: the tile at 512 px with rounded corners, the icon as it sits on a home
  screen. The README hero image and the picture to use wherever the app is shown as an app.

The icon is **not** the mascot. The default face is the bundled dragon; never put the dragon
on the launcher icon, and never put the circuit-o in the chat as a face.

## Colour

| Token | Value | Use |
|---|---|---|
| `brand.ink.start` | `#0B0F19` | left end of the mark's gradient |
| `brand.ink.end` | `#1A2233` | right end of the mark's gradient |
| `tile` | `#FFFFFF` | icon tile |
| `tile.dark` | `#0F1B33` | the dark tile |
| `brand.blue` | `#015CFB` | links, primary buttons, status line (unchanged in the apps) |

The light and dark theme tokens of the apps are unchanged from the fork's origin: `primary`
`#015CFB`, `primary.container` `#E5F0FF`, `ink` `#000000`, `pill` `#F2F2F7`. They were measured
against the N mark and still read well beside an ink mark.

## Rules

- Lower-case `corein` in running text and in the wordmark; never `Corein` or `COREIN` except
  where a platform forces a capital (a store listing's first letter).
- The mark alone is never stretched, outlined or given a drop shadow.
- Clear space around the wordmark is the height of the o on every side.
- Minimum sizes: the mark 16 px, the wordmark 80 px wide.

## Regenerating the icons

```sh
python scripts/gen-android-icons.py   # adaptive icons, notification mark, legacy rasters
python scripts/gen-ios-icons.py       # the iOS icon set and the alternate icons
```

Both read `assets/brand/corein-mark.svg` and need Playwright with Chromium for the rasters.

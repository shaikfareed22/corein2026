# FOMO brand

Decided 2026-10-26. The logo, the app icon and the website's colours are one decision.

## The logo

**FOMO** in heavy white capitals on a deep navy, with an orange arrow, outlined in the navy,
running from the M into the last O.

- Source of truth: `assets/brand/fomo-logo-source.png`, the logo as supplied.
- `assets/brand/fomo-logo.png`: the same at four times the size, on its navy. This is the logo
  on every sign-in and first-run screen (Android, iPhone, the web console, the desktop app) and
  the README's hero.
- `assets/brand/fomo-logo-transparent.png`: the letters and the arrow with the navy removed, for
  dark pages: the website's header and footer, and the docs' header.

## The icon

A wide wordmark cannot be read at launcher size, so the icon is the logo's own key: the last O,
pierced by the orange arrow, on the logo's navy.

- `assets/brand/fomo-mark.svg`: the O (`id="primary"`, white) and the arrow (`id="accent"`,
  orange, outlined in the navy) on a 100-unit tile, absolute `M`/`L`/`C`/`Z` path data only.
  Every icon is generated from it.
- `assets/brand/fomo-icon.svg`: the mark on a rounded navy tile. The favicon, the web app's and
  the relay console's icon, the desktop installer and window icon.
- `docs/app-icon.png`: the tile at 512 px.

The icon is **not** the mascot. The default face is the bundled dragon; never put the dragon on
the launcher icon, and never put the logo in the chat as a face.

## Colour

| Token | Value | Use |
|---|---|---|
| `navy` | `#1C2932` | the logo's backdrop, the icon tile |
| `white` | `#FFFFFF` | the letters, the O |
| `orange` | `#FF9A18` | the arrow |

The website and the docs keep their own dark field (`#070B14`) with the blue to violet to cyan
accent; the logo sits on it with its navy removed. The apps' theme colours are unchanged.

## Rules

- The name is **FOMO**, in capitals, as the logo writes it.
- The logo is never stretched, recoloured or given a shadow; keep it on its navy or on a dark
  field.
- Minimum sizes: the icon 16 px, the logo 96 px wide.

## Regenerating the icons

```sh
python scripts/gen-android-icons.py   # adaptive icons, notification mark, legacy rasters
python scripts/gen-ios-icons.py       # the iOS icon set and the alternate icons
```

Both read `assets/brand/fomo-mark.svg` and need Playwright with Chromium for the rasters.

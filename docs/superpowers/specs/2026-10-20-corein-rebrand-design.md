# corein: rebrand, legal frame and release readiness

Decided 2026-10-20. corein is a fork of nanoMuse (GPL-3.0-or-later), itself built on
OpenMinis (GPL-3.0). This page records what the fork changes, what it keeps, and why.

## Intent

- One product name, **corein**, on the Android app, the iPhone app, the desktop app, the web
  console, the relay and the docs. Lower-case wordmark, as the logo is drawn.
- A legal frame that lets the owner distribute installers and earn from the product without
  breaking the licences it stands on.
- Release-ready: the three desktop bugs found with Gemini are fixed in source, not in
  installed files; the apps point at the owner's own relay; the brand assets exist in every
  size the build pipeline reads.

## Business model (default, changeable later)

Free apps; each person brings their own model key; the relay does sign-in, the hub and
conversation sync only, with no upstream model key. No billing code ships. A paid tier can
later be added on the relay (allowance, members, `SIGNUP_OPEN`) without touching the apps.

## What changes

| Thing | nanoMuse | corein |
|---|---|---|
| Product name (every UI string, docs, store copy) | nanoMuse | corein |
| Relay product name | nanoMuse Cloud | corein Cloud |
| Desktop product | nanoMuse Desktop | corein Desktop |
| Android applicationId | io.github.nanomuse.app | com.corein.app |
| iOS bundle ids | io.github.nanomuse.* | com.corein.* |
| System URL scheme | nanomuse:// | corein:// |
| Desktop appId / executable / artifact | io.github.nanomuse.desktop / nanomuse-desktop / nanoMuse-Desktop-* | com.corein.desktop / corein-desktop / corein-Desktop-* |
| Default relay | https://cloud.nanomuse.cn | https://cloud.fomo.corein.in |
| Site, demo | nanomuse.cn, demo.nanomuse.dev | fomo.corein.in, demo.fomo.corein.in |
| Repository | github.com/nano-muse/nanoMuse | github.com/shaikfareed22/corein2026 |
| Brand mark, icon, wordmark, cover | the one-stroke N | the corein circuit-o mark and wordmark |
| Upstream badges (stars, trendshift, hits, Discord, TestFlight link) | nanoMuse's | removed; owner adds their own when they exist |

All of these are constants at the top of `scripts/rebrand-corein.mjs`; change one there and
re-run.

## What stays, on purpose

- **Licence.** GPL-3.0-or-later. LICENSE unchanged. NOTICE credits nanoMuse (commit
  821b7f6, 2026-10-17) and OpenMinis 1.13, and says the complete corresponding source is the
  tagged commit of the corein repository plus the proot submodule.
- **Internal identifiers.** The Python package `nanomuse`, its CLI, the `NANOMUSE_*`
  environment variables, the data directory `~/.nanomuse`, the Kotlin packages
  `com.openminis.*` and `io.github.nanomuse.*`, the `nm_` string prefix, the harness plugin
  package `dsh-nanomuse`, the Swift type names `NanoMuse*`. Renaming them buys nothing a
  person can see and would make every upstream pull a conflict. The same rule nanoMuse
  applies to OpenMinis.
- **History.** CHANGELOG.md and docs/releases/ keep the nanoMuse name; a corein entry is
  added on top.
- **The UI palette.** The brand blue and the theme tokens of docs/brand.md stay; the new mark
  is ink with blue accents, so the apps' colours already match it.
- **The dragon** as the default face. It is a face, not a logo.
- **The Meta disclaimer.** The product is not affiliated with Meta's Muse.

## Brand assets

Source of truth is `assets/brand/corein-mark.svg`: the circuit-o, a single compound filled
path on a 100-unit tile, which the icon generators consume unchanged. Derived:
`corein-wordmark.svg` (the word with the mark as its o), `corein-icon.svg` (white tile +
mark), `corein-icon-on-dark.svg`, `corein-cover.svg` (README hero). The generators write the
Android adaptive icons, the iOS icon set and the desktop icon. docs/brand.md is rewritten.

## Legal frame

- NOTICE: corein copyright line, derivation from nanoMuse and OpenMinis with commits, source
  location, trademarks: "nanoMuse" and "OpenMinis" are their authors'; corein uses neither
  name nor logo as its own.
- THIRD_PARTY_NOTICES.md: a nanoMuse entry at the top.
- README: an *Origin* section stating the derivation and linking upstream, and the citation
  of the nanoMuse paper kept under *Acknowledgements*.
- docs/privacy.md reworded for the owner as operator; it is the privacy policy the stores
  ask for.
- CONTRIBUTING.md and AGENTS.md: the DCO stays; the maintainer contact becomes the owner's.
- What the owner must still do themselves: pick a GitHub org, register the domain, own an
  Android signing key, and, if they want store listings, a developer account per store.

## Source fixes shipped with the rebrand

1. `providers.ts` `listModelRows`: strip a `models/` prefix from `id` as it already does from
   `name` (Google's compatible layer returns prefixed ids).
2. `providers.ts` `ownProviderRow`: emit `compat.supportsStore: false` for a row whose base
   URL is `generativelanguage.googleapis.com` (Google rejects the `store` field).
3. The thought-signature bypass on echoed tool calls for Google's endpoint: applied to the
   bundled pi-ai by a postinstall patch in `harness/desktop/scripts/`, with the upstream
   issue noted, until pi-ai carries it.
4. The retired `gemini-2.5-flash` and the slow `gemini-3.8-flash` leave the catalogue's
   defaults for Gemini: chat and hands default to `gemini-3.5-flash-lite`.

## Testing

- `node scripts/rebrand-corein.mjs --check` exits non-zero when any renamed token is left
  outside the excluded history and vendored trees; CI runs it.
- The existing checks for the area: `pnpm test` in the plugin, `node tests/fences.test.mjs`,
  `node scripts/providers-json.mjs --check`, `node scripts/connectors-json.mjs --check`,
  `python scripts/rebrand.py --check`.
- A manual pass: install the Windows build, sign in against the owner's relay, chat on a
  Gemini key, run one hands task.

## Out of scope here

Building and signing installers, store listings, the public relay deployment and billing.
Each is its own step after this one.

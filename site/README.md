# The website

`site/` is published by `.github/workflows/pages.yml` to GitHub Pages at <https://fomo.corein.in/>
(`site/CNAME`). The workflow also builds the docs (`website/`, VitePress over `docs/`) into
`site/docs/`, served at <https://fomo.corein.in/docs/>.

- `index.html` is the landing page: one static file, no framework. Its download links follow the
  latest GitHub release, so a new version needs no edit here.
- `assets/` is not committed. The workflow's *Assemble site/assets* step copies the brand files
  from `assets/brand/`, the icons from `web/public/` and the Figtree font into it.

## Preview

Run the assemble step's `cp` lines from the repository root, build the docs, and serve both the
way Pages does:

```bash
cd website && DOCS_BASE=/docs/ npm run docs:build && cd ..
mkdir -p /tmp/site/docs && cp -R site/. /tmp/site/ && cp -R website/.vitepress/dist/. /tmp/site/docs/
cd /tmp/site && python3 -m http.server 8000      # http://localhost:8000/ and /docs/
```

The docs must be built with `DOCS_BASE=/docs/` (the default); any other base and the live pages
load without their styles.

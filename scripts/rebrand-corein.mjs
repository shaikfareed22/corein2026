#!/usr/bin/env node
// corein: turn the nanoMuse tree into corein. Idempotent; re-run after every upstream merge,
// then `python scripts/rebrand.py` and the icon generators (CONTRIBUTING.md).
//
//   node scripts/rebrand-corein.mjs            apply
//   node scripts/rebrand-corein.mjs --check    exit 1 when a renamed token is still present
//
// What changes: the product's visible identity (names, ids the system knows the apps by,
// domains, the repository, the brand files). What stays: internal identifiers (the Python
// package `nanomuse`, NANOMUSE_* variables, the Kotlin packages, `nm_` strings, `dsh-nanomuse`,
// the Swift `NanoMuse*` types) and history (CHANGELOG.md, docs/releases/). The design record is
// docs/superpowers/specs/2026-10-20-corein-rebrand-design.md.
import { readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

// ---- the identity: change these, re-run ------------------------------------------------------
export const NAME = 'corein'
export const CLOUD = `${NAME} Cloud`
export const DESKTOP = `${NAME} Desktop`
export const REPO = 'corein-app/corein'
export const DOMAIN = 'corein.app'
export const RELAY = `cloud.${DOMAIN}`
export const DEMO = `demo.${DOMAIN}`
export const ANDROID_ID = 'com.corein.app'
export const IOS_PREFIX = 'com.corein'
export const SCHEME = 'corein'
export const DESKTOP_APP_ID = 'com.corein.desktop'
export const DESKTOP_EXE = 'corein-desktop'
export const DESKTOP_ARTIFACT = 'corein-Desktop-'
export const MARK = 'corein-mark.svg'

const ROOT = join(fileURLToPath(import.meta.url), '..', '..')

// Directories never touched: vendored trees, build output, history, this design's own record.
const SKIP_DIRS = new Set(['.git', 'node_modules', 'deps', 'static', 'traces', 'screenshots', 'releases', 'superpowers', 'dist', 'build', '.gradle', 'DerivedData'])
// Files kept as history or authored by hand for the fork.
const SKIP_FILES = new Set(['CHANGELOG.md', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'CITATION.cff', 'rebrand-corein.mjs', 'package-lock.json', 'pnpm-lock.yaml', 'uv.lock'])
const TEXT = /\.(md|txt|ts|tsx|mts|mjs|cjs|js|json|jsonc|yml|yaml|toml|py|kt|kts|swift|xml|xcstrings|html|css|svg|sh|ps1|env|example|cff|plist|pbxproj|strings|gradle|pro|properties|cfg|ini|Dockerfile|dockerignore|gitignore|editorconfig|caddy|conf)$/i
const NAMED = new Set(['Dockerfile', 'Caddyfile', 'LICENSE', 'SECURITY.md', 'AGENTS.md', 'CLAUDE.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', '.env.example', '.dockerignore', '.gitattributes'])
const MAX_BYTES = 4 * 1024 * 1024

// Ordered: the longest, most specific tokens first so a later rule never sees a half-renamed one.
const SUBS = [
  [/github\.com\/nano-muse\/nanoMuse/g, `github.com/${REPO}`],
  [/\bnano-muse\/nanoMuse\b/g, REPO],
  [/https:\/\/cloud\.nanomuse\.cn/g, `https://${RELAY}`],
  [/\bcloud\.nanomuse\.cn\b/g, RELAY],
  [/\bdemo\.nanomuse\.dev\b/g, DEMO],
  [/\bwww\.nanomuse\.cn\b/g, DOMAIN],
  [/\bnanomuse\.cn\b/g, DOMAIN],
  [/\bio\.github\.nanomuse\.app\b/g, ANDROID_ID],
  [/\bio\.github\.nanomuse\.desktop\b/g, DESKTOP_APP_ID],
  [/\bio\.github\.nanomuse\.(MinisTests|MinisUITests)\b/g, `${IOS_PREFIX}.$1`],
  [/\bnanoMuse-Desktop-/g, DESKTOP_ARTIFACT],
  [/\bexecutableName: nanomuse-desktop\b/g, `executableName: ${DESKTOP_EXE}`],
  [/\bnanomuse-desktop\.exe\b/g, `${DESKTOP_EXE}.exe`],
  [/android:scheme="nanomuse"/g, `android:scheme="${SCHEME}"`],
  [/SYSTEM_SCHEME = "nanomuse"/g, `SYSTEM_SCHEME = "${SCHEME}"`],
  [/\bnanomuse-mark\.svg\b/g, MARK],
  [/\bnanomuse-cover\.png\b/g, 'corein-cover.svg'],
  [/\bnanomuse-icon\.svg\b/g, 'corein-icon.svg'],
  [/\bnanomuse:\/\//g, `${SCHEME}://`],
  [/\[nanomuse-desktop\]/g, `[${DESKTOP_EXE}]`],
  [/\bnanomuse-desktop\.desktop\b/g, `${DESKTOP_EXE}.desktop`],
  [/Icon=nanomuse-desktop\b/g, `Icon=${DESKTOP_EXE}`],
  [/\.\/nanomuse-desktop\b/g, `./${DESKTOP_EXE}`],
  [/OWNER = "nano-muse"/g, `OWNER = "${REPO.split('/')[0]}"`],
  [/\bnanoMuse Cloud\b/g, CLOUD],
  [/\bnanoMuse Desktop\b/g, DESKTOP],
  [/\bnanoMuse\b/g, NAME],
]

// README badge rows and community links that belong to the upstream project, not to the fork.
const DROP_LINES = /trendshift\.io|hits\.sh|discord\.gg\/|shields\.io\/github\/(stars|downloads|license)\/|huggingface\.co\/papers|testflight\.apple\.com\/join/

// Leftovers the check looks for (what SUBS would have changed).
const LEFT = [/\bnanoMuse\b/, /\bnanomuse\.cn\b/, /\bnano-muse\/nanoMuse\b/, /\bio\.github\.nanomuse\.(app|desktop)\b/, /\bcloud\.nanomuse\b/, /\bdemo\.nanomuse\b/]

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    const st = statSync(path)
    if (st.isDirectory()) {
      if (SKIP_DIRS.has(name)) continue
      yield* walk(path)
    } else if (st.size <= MAX_BYTES && (TEXT.test(name) || NAMED.has(name)) && !SKIP_FILES.has(name)) {
      yield path
    }
  }
}

function isReadme(rel) {
  return /(^|[\\/])README(_[a-zA-Z-]+)?\.md$/.test(rel) || rel.replace(/\\/g, '/').startsWith('docs/readme/')
}

export function rebrand(text, rel) {
  let out = text
  for (const [re, to] of SUBS) out = out.replace(re, to)
  if (isReadme(rel)) out = out.split('\n').filter((line) => !DROP_LINES.test(line)).join('\n')
  return out
}

function main(argv) {
  const check = argv.includes('--check')
  const changed = []
  const left = []
  for (const path of walk(ROOT)) {
    const rel = relative(ROOT, path).split(sep).join('/')
    let text
    try { text = readFileSync(path, 'utf8') } catch { continue }
    if (text.includes('\u0000')) continue
    if (check) {
      const hits = LEFT.filter((re) => re.test(text)).map(String)
      if (hits.length) left.push(`${rel}: ${hits.join(' ')}`)
      continue
    }
    const out = rebrand(text, rel)
    if (out !== text) { writeFileSync(path, out, 'utf8'); changed.push(rel) }
  }
  if (check) {
    if (left.length) { console.error(`rebrand-corein: ${left.length} file(s) still carry the old identity:\n  ${left.join('\n  ')}`); return 1 }
    console.log('rebrand-corein: clean')
    return 0
  }
  console.log(`rebrand-corein: ${changed.length} file(s) changed`)
  return 0
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) process.exit(main(process.argv.slice(2)))

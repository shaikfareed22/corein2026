# Maintaining the fork

corein forks [nanoMuse](https://github.com/nano-muse/nanoMuse). This page is the recipe for
keeping it that way: taking upstream's fixes, keeping the corein identity, and cutting a
release. The design record is
[superpowers/specs/2026-10-20-corein-rebrand-design.md](superpowers/specs/2026-10-20-corein-rebrand-design.md).

## What the fork changes, and what it keeps

Everything a person sees says corein: names, the ids the systems know the apps by
(`com.corein.in`, `com.corein.*`, `corein://`, `com.corein.desktop`), the relay and site
domains, the repository, the brand files. Everything internal keeps upstream's name: the
Python package `nanomuse`, `NANOMUSE_*` variables, `~/.nanomuse`, the Kotlin packages, the
`nm_` string prefix, `dsh-nanomuse`, the Swift `NanoMuse*` types, the `nanomuse-mcp` OAuth
callback scheme. That split is what lets `git merge upstream/main` keep working.

One script owns the rename, `scripts/rebrand-corein.mjs`. Its constants at the top are the
identity; `--check` fails when any renamed token is still in the tree, and CI should run it.

## Taking upstream's changes

```sh
git fetch upstream                                   # https://github.com/nano-muse/nanoMuse.git
git merge upstream/main                              # resolve conflicts as usual
node scripts/rebrand-corein.mjs                      # rename what the merge brought in
python scripts/rebrand.py                            # upstream's own Android/iOS rebrand, now with corein's constants
python scripts/gen-android-icons.py && python scripts/gen-ios-icons.py
node scripts/providers-json.mjs && node scripts/connectors-json.mjs
node scripts/rebrand-corein.mjs --check && python scripts/rebrand.py --check
```

Then the checks for whatever the merge touched ([AGENTS.md](../AGENTS.md)). Two things the
rename script cannot do and a merge may need by hand: a directory or file *named* after
upstream (rename it, as `demo/mobilegym/apps/corein` was), and a new place where upstream
writes its own name as a lowercase identifier the system sees (add a rule to the script, as
for `OwnScheme.SYSTEM` and the iOS `CFBundleURLSchemes`).

The web console under `nanomuse/server/static/` must be rebuilt on Linux after a merge that
touches `web/`; a Windows build names every chunk differently and CI compares bytes. The
simplest way on any machine:

```sh
docker run --rm -v "$PWD:/src" node:22 sh -c \
  "git config --global --add safe.directory /src && git clone -q /src /tmp/r && cd /tmp/r/web && npm ci && npm run build && cp -R ../nanomuse/server/static/. /src/nanomuse/server/static/"
```

## Cutting a release

Versions move in one commit with `scripts/release-bump.sh` and `scripts/rebrand.py`
([CONTRIBUTING.md](../CONTRIBUTING.md#releasing-maintainers)); the tag is `v<version>`.
Pushing the tag starts:

- **Android** (`.github/workflows/android.yml`, the *release* job): builds the natives,
  signs `assembleRelease` with the keystore in the repository's secrets, refuses the debug
  key, names the APK `corein-<version>-arm64.apk` with its `.sha256`, and creates the
  GitHub release with `docs/releases/v<version>.md` as the notes.
- **desktop app**: builds the Windows, macOS and Linux installers and attaches them to that
  release once it exists.
- **Docker image**: publishes the relay and runtime image under the tag.

The secrets the Android release job reads, all under *Settings → Secrets and variables →
Actions*:

| Secret | What |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | the release keystore, `base64 -w0 corein-release.jks` |
| `ANDROID_KEYSTORE_PASSWORD` | its store password |
| `ANDROID_KEY_ALIAS` | the key alias, `corein` |
| `ANDROID_KEY_PASSWORD` | the key password |

One keystore for every version: a later APK signed with another key cannot install over an
earlier one. Keep the file and the passwords outside the repository, in two places.

macOS signing and notarisation, and the iOS TestFlight upload, read the Apple secrets the
workflows name (`MAC_CERT_P12_BASE64`, `APP_STORE_CONNECT_*`, `APPLE_TEAM_ID`); without them
the macOS build is unsigned and the first launch needs right-click → *Open*.

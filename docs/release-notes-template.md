# FOMO <version> · <Codename>

<!-- The first line is the GitHub release title (scripts/release-apk.sh reads it).
     English first; the Chinese version of the same notes goes in the <details> block at the end.
     Codenames so far: Foundation, Identity, Home, Guardrails, Memory, Avatar, Welcome, Polish,
     Portrait, Motion, Hatch, Hands, Reach, Home, Stage, Palette, Open, Ensemble, Presence,
     Footing, Commons, Welcome, Signal, Mirror, Window, Ledger, Harness, Likeness, Rooms, Locks,
     Union, Steps, Turns, Accord, Thread, Weave, Loom, Keys, Clear, Choice, Keel, Ballast, Trim, Helm, Compass, Lookout, Launch, Rise, Clear (CHANGELOG.md has the list). One word, capitalised,
     not on that list (Home and Welcome were each used twice early on; do not add a third).

     Voice: plain and specific, the maintainer talking to one person. Facts over promises; no
     slogans, no "every one brings…", no exclamation marks.

     The shape follows the releases people know (nanobot's): a short story, then Highlights,
     Upgrade Notes, Community; What's Changed, New Contributors, Contributors and the Full
     Changelog link are generated from the merged pull requests by scripts/release_notes.py
     where the marker below stands, when the release is published. -->

🐉 **FOMO `<version>` “<Codename>”** <one sentence: what this version is about>.

<One or two short paragraphs: the headline, and the other story; in plain words, what it means for the person using it.>

## Highlights

- **<Thing>.** <What it is, where to find it, what it replaces.>
- …

## Upgrade Notes

- **Android installs over <previous> and keeps your data.** `fomo-<version>-arm64.apk` (Android 8.0+, arm64; versionCode <n>) is signed with the same key as every version before it. Verify with `sha256sum -c fomo-<version>-arm64.apk.sha256`.
- **The desktop installers are not notarised.** On macOS open the app once from *System Settings → Privacy & Security → Open Anyway* (or right-click → *Open*); on Windows click *Run anyway*. They arrive a little after the APK (CI builds them from the tag), and `SHA256SUMS-desktop.txt` lists every checksum, the Windows update metadata included (`latest.yml` and the installer's `.exe.blockmap`).
- <Anything a person upgrading must know: a setting that moved, a relay version an operator needs, a platform that needs a newer build.>
- **Where to get it.**

  | | |
  |---|---|
  | Browser | [demo.fomo.corein.in](https://demo.fomo.corein.in/): a FOMO on a simulated phone, after a sign-in; a demo, the apps below are the real thing |
  | Android 8.0+, arm64 | `fomo-<version>-arm64.apk` |
  | iPhone, iPad | [TestFlight](https://testflight.apple.com/join/ZHexbDqc): a beta; build <n>, delivered once Apple's beta review has passed |
  | Windows 10+ | `fomo-Desktop-<version>-win-x64.exe` (the desktop app, on DeepSeek Harness) |
  | macOS 12+ | `fomo-Desktop-<version>-mac-arm64.dmg` / `-mac-x64.dmg` (or the `.zip`: unzip, drag to Applications) |
  | Linux x64 | `fomo-Desktop-<version>-linux-x64.deb` / `.AppImage` (needs FUSE; `--appimage-extract-and-run` without) / `.tar.gz` (unpack anywhere, run `./fomo-desktop`) |
  | DeepSeek Harness Desktop you already run | `dsh-nanomuse-<version>.tgz`: `dsh plugin --profile desktop add …` ([how](https://github.com/shaikfareed22/corein2026/blob/main/harness/README.md)) |

  In our measurements GitHub's own downloads are quick from China as well; if they fail where you are, the same files are on [fomo.corein.in/dl/v<version>/](https://fomo.corein.in/dl/v<version>/) within fifteen minutes.

## Community

FOMO is open source, free and non-profit. Sign in with a phone number or an e-mail and you get a starting allowance; the developer pays for it. The account page shows what is left and how to add more. When it is gone, use your own key or a plan you already pay for ([how](https://github.com/shaikfareed22/corein2026/blob/main/docs/own-key.md)). With an account, the text of your conversations is kept on FOMO Cloud so that your devices show the same chats; one switch in Data controls turns it off and deletes it; nothing is sold ([privacy policy](https://fomo.corein.in/privacy/)); delete the account whenever you want.

A stable version is not the last word: FOMO keeps evolving, and the [roadmap](https://github.com/shaikfareed22/corein2026/blob/main/docs/roadmap.md) says what comes next. We use it every day and know where it is rough; tell us where it broke for you and what you want it to do. Thanks to everyone who tried a build and reported what broke. [Open an issue](https://github.com/shaikfareed22/corein2026/issues/new/choose) · [send a pull request](https://github.com/shaikfareed22/corein2026/blob/main/CONTRIBUTING.md) · [Discussions](https://github.com/shaikfareed22/corein2026/discussions) · [Discord](https://discord.gg/bkTySmm28X) · [star the repo](https://github.com/shaikfareed22/corein2026); if it is useful to you, a star helps others find it.

Based on [OpenMinis](https://github.com/OpenMinis/OpenMinis) 1.13 (GPL-3.0), modified since 2026-09-24. The complete corresponding source of this build is tag `v<version>` plus the `android/deps/proot` submodule ([nano-muse/proot](https://github.com/nano-muse/proot)). The whole repository is GPL-3.0-or-later. FOMO Desktop carries DeepSeek Harness unmodified, with its licence files inside; *harness* in the name is the word, not DeepSeek's. FOMO is not affiliated with Meta; Muse is a trademark of Meta Platforms, Inc. The desktop follows what Muse's app looks like and does, written down from using it; none of Meta's assets, code or content is in it.

<!-- pull requests -->

<details>
<summary>Simplified Chinese</summary>

🐉 **FOMO `<version>`<Codename>**<>

<>

### 

- **<>** <>
- …

### 

- **Android  <previous>** `fomo-<version>-arm64.apk` 8.0+ <n>`sha256sum -c fomo-<version>-arm64.apk.sha256`
-  macOS   APK `SHA256SUMS-desktop.txt`  Windows 
- <>
- 

  | | |
  |---|---|
  |  | [demo.fomo.corein.in](https://demo.fomo.corein.in/) FOMO |
  | Android 8.0+ | `fomo-<version>-arm64.apk` |
  | iPhone | [TestFlight](https://testflight.apple.com/join/ZHexbDqc) Apple  <n>  |
  | Windows 10+ | `fomo-Desktop-<version>-win-x64.exe` |
  | macOS 12+ | `fomo-Desktop-<version>-mac-arm64.dmg` / `-mac-x64.dmg` |
  | Linux x64 | `fomo-Desktop-<version>-linux-x64.deb` / `.AppImage`/ `.tar.gz`|
  |  DeepSeek Harness Desktop | `dsh-nanomuse-<version>.tgz``dsh plugin --profile desktop add …`[](https://github.com/shaikfareed22/corein2026/blob/main/harness/README.md) |

   GitHub  [fomo.corein.in/dl/v<version>/](https://fomo.corein.in/dl/v<version>/)

### 

FOMO  key[](https://github.com/shaikfareed22/corein2026/blob/main/docs/own-key.md) FOMO Cloud[](https://fomo.corein.in/privacy/)

 [](https://github.com/shaikfareed22/corein2026/blob/main/docs/zh/roadmap.md) issue[ issue](https://github.com/shaikfareed22/corein2026/issues/new/choose) · [ PR](https://github.com/shaikfareed22/corein2026/blob/main/CONTRIBUTING.md) · [Discussions](https://github.com/shaikfareed22/corein2026/discussions) · [Discord](https://discord.gg/bkTySmm28X) · [ Star](https://github.com/shaikfareed22/corein2026) Star

 [OpenMinis](https://github.com/OpenMinis/OpenMinis) 1.13-3.0 2026-09-24  tag `v<version>`  `android/deps/proot`[nano-muse/proot](https://github.com/nano-muse/proot) GPL-3.0-or-later   DeepSeek Harness  *harness*  DeepSeek   Meta   Meta Platforms, Inc.  Muse  Meta 

</details>

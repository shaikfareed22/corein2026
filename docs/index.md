---
layout: home
title: FOMO docs
hero:
  name: FOMO
  text: An open-source personal agent for every device you own.
  tagline: One agent on your phone, your computer and the web, one account across them. It does things instead of answering questions, keeps going when the app is closed, remembers you in files you can read, and asks before anything you could not undo.
  actions:
    - theme: brand
      text: Get started
      link: /android
    - theme: alt
      text: Download
      link: https://github.com/shaikfareed22/corein2026/releases/latest
    - theme: alt
      text: Run it yourself
      link: /self-hosting
features:
  - icon: ⚡
    title: Does things
    details: A Linux shell, a browser, MCP servers and skills, and, with Hands on, the apps on your phone and the windows on your computer through their screens.
    link: /every-device
    linkText: Every device
  - icon: 🛡️
    title: Asks first
    details: A stop before deleting, sending or paying, remembered for once, this chat or always. Passwords and codes are yours to type.
    link: /sentinel
    linkText: How the guard works
  - icon: 📱
    title: Reaches your other devices
    details: Say it on the phone, it runs on your PC. Approvals come back to the device in your hand.
    link: /hub
    linkText: The hub
  - icon: ⏰
    title: Keeps going
    details: Goals checked on a schedule, routines that run while the app is closed, a feed written for you each morning.
    link: /desktop-muse
    linkText: Feed, Goals, Routines
  - icon: 📝
    title: Remembers you
    details: What it is, what it knows about you and when it wakes are Markdown files you can read and edit.
    link: /configuration
    linkText: Memory and files
  - icon: 🔑
    title: Your key, your relay
    details: Model requests go from your device to the provider you chose. The relay does sign-in and sync, and you can run it yourself.
    link: /own-key
    linkText: Bring your own key
---

## Install

| Platform | Get it | Then read |
|---|---|---|
| **Android** 8.0+, 64-bit | [fomo-1.2.0-arm64.apk](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-1.2.0-arm64.apk) | [Android](/android) |
| **Windows** 10+ | [fomo-Desktop-1.2.0-win-x64.exe](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-Desktop-1.2.0-win-x64.exe) | [The desktop app](/desktop) |
| **macOS** 12+ | [Apple Silicon](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-Desktop-1.2.0-mac-arm64.dmg) · [Intel](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-Desktop-1.2.0-mac-x64.dmg) | [The desktop app](/desktop) |
| **Linux** x64 | [AppImage](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-Desktop-1.2.0-linux-x64.AppImage) · [.deb](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-Desktop-1.2.0-linux-x64.deb) · [tar.gz](https://github.com/shaikfareed22/corein2026/releases/download/v1.2.0/fomo-Desktop-1.2.0-linux-x64.tar.gz) | [The desktop app](/desktop) |
| **iPhone / iPad** | Build it yourself for now | [iOS](/ios) |
| **Web and servers** | `bash scripts/self-host.sh --local` for your own relay; `docker compose up -d app` for the web app | [Run it yourself](/self-hosting) |

Every file and its checksum is on the [latest release](https://github.com/shaikfareed22/corein2026/releases/latest). Windows shows *Run anyway* and macOS *Open Anyway* once; the installers are not yet signed with paid certificates.

## Three steps to a working agent

1. **Install and sign in.** Open the app and sign in with an e-mail. The relay it signs in to does sign-in, the hub and conversation sync; it holds no model key. To use a relay of your own, tap *Use a different server* on the sign-in screen.
2. **Add a model key.** *Settings → Models*: Google Gemini, OpenRouter, OpenAI, DeepSeek or any OpenAI-compatible endpoint. The key goes from your device to that provider and nowhere else. [Bring your own key](/own-key) has the steps per provider.
3. **Give it something to do.** "Create a file on my desktop with three lines about today", "open the news site and give me the top three headlines", or switch on Hands and say "open Notepad and type hello". The [troubleshooting page](/troubleshooting) has the answer when something does not.

## Where to go next

| You want to | Read |
|---|---|
| Use it on the phone, the desktop or the web | [Android](/android) · [iOS](/ios) · [The desktop app](/desktop) · [The web console](/app) |
| Let your devices work together | [Every device](/every-device) · [The hub](/hub) |
| Let it operate a screen | [The screen as a hand](/gui) · [Computer use on the desktop](/desktop-muse) |
| Connect your tools and chat apps | [Connectors](/channels) · [The browser](/browser) · [Coding agents](/coding-agents) |
| Understand what it keeps and what it may do | [Privacy](/privacy) · [The Sentinel](/sentinel) |
| Run the relay or the web app on a server | [Run it yourself](/self-hosting) · [The relay](/cloud) · [Deployment](/deployment) |
| Change the code | [Architecture](/architecture) · [Configuration](/configuration) · [Roadmap](/roadmap) |

::: info Free software
FOMO is GPL-3.0-or-later. The source, the licence and the notices are in the [repository](https://github.com/shaikfareed22/corein2026); every release is a tagged commit you can build yourself. Tell us where it broke for you: [open an issue](https://github.com/shaikfareed22/corein2026/issues/new/choose).
:::

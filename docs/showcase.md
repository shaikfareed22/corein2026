# Showcase: seven things a Chinese day asks for

corein is one agent with several hands. It reads and writes files, searches the web, runs commands, drives a browser; it calls MCP servers and command-line tools; it follows skills; and, when it runs on a phone, it uses the phone's own calendar, clipboard and alarms, and, as the last resort, the apps on the phone's screen. The [ladder](gui.md#the-ladder) says which hand comes first: a skill, a CLI or an MCP server; then a fetch with the user's login; then the in-app browser; only then the screen. Of the seven cases below, one uses the screen. That is the point.

Nothing here spends money: every send, order or payment stops for your approval, and the operator never fills in passwords or codes. Which services stand behind the cases, and which have been run where: [services.md](services.md).

**Traces.** Each case links to what actually happened: the chat's timeline as the app stores it, or a phone trace with every screen and tap. Cases marked *pending* have not been run end to end yet, and the line says what they wait for: the four Tier-1 services need the owner's keys and logins (a Amap key, a Feishu and a Tencent Meeting login), and the phone cases need an Android phone with the apps on it. The [launch checklist](launch-checklist.md#9-chinese-services-and-the-showcase-p0) tracks them.

## 1. A business trip in one sentence

> 

| Hand | What it does |
|---|---|
| `skills` | reads `train-tickets`: search through the 12306 server, book on the phone only when told to |
| `remember` | : a preference, used the next time trains come up |
| `12306__get-current-date` · `get-station-code-of-citys` · `get-station-code-by-names` · `get-tickets` | tomorrow's date from the server, the codes for Beijing and Shanghai, the G trains before 13:00 with seats and prices; a second query when the first is sold out |
| `amap__maps_geo` · `maps_direction_transit_integrated` | home (remembered) → Beijing at that hour: leave by 06:40 |
| `calendar` | a draft for the departure with  and seat, for you to confirm |
| `shell: lark-cli im +chat-search` · `im +messages-send --idempotency-key …` | the group, the one message; its text on an approval card first |

No screen anywhere. The Sentinel asks once, for the message; everything else is read-only or in your own workspace.

**Trace:** [the train half](traces/case-1-train.md), recorded on 2026-09-24 in the web app with the 12306 server; the model found every  before 13:00 sold out, said so, and gave the nearest alternatives instead of pretending. The Amap route, the calendar draft and the Feishu message are *pending*: a Amap key and a Feishu login on the test machine.

## 2. The morning brief

>  7:30  Meeting

| Hand | What it does |
|---|---|
| `reminders` (a routine) | `weekdays 07:30`, delivered as a notification with the app closed; on the phone, the runtime's alarm wakes it for this |
| `amap__maps_weather` | Beijing today: temperature, rain, air |
| `shell: lark-cli calendar +agenda --as user` · `task +get-my-tasks --as user` | the day's events and the open tasks, `--jq` to keep them short |
| `shell: tmeet meeting list --compact` | today's meetings with  and link |
| the notification | one card; tapping it opens the chat with the full brief |

**Trace:** *pending*: Amap key, Feishu and Tencent Meeting logins. The routine and the notification path themselves are exercised by the app's tests and the emulator (the *Keep it running* work in [archive/android-python-line.md](archive/android-python-line.md#keeping-it-running)).

## 3. Where is my JD.com order

>.com

| Hand | What it does |
|---|---|
| `browser` (the phone's WebView, offscreen) | opens JD.com's order page in the background |
| the login wall | the agent stops: *Take over* slides the real page up as a sheet, you log in once, **Done** hands it back; the login persists in the app's own browser profile |
| `browser` `extract` | the order and its tracking number and courier |
| `kuaidi100__query_trace` (when configured) | the parcel's events; otherwise the order page's own tracking list |
| the reply | where it is, when it should arrive |

The second rung (a page with your login, in the app) before any screen: JD.com has no personal API, but its web works without an app. Configured,  turns the tracking into one tool call.

**Trace:** *pending*: a JD.com login on a phone with the local build. The browser backend, the take-over sheet and the login persisting were verified on the emulator in [browser.md](browser.md).

## 4. A budget table for  over the holiday

>  400  4.5  trips/chengdu-2026-10/budget.md

| Hand | What it does |
|---|---|
| `browser` (Playwright on the computer, or the phone's WebView) |  hotel search for the dates and the area, filters, three listings read |
| `files` | `trips/chengdu-2026-10/budget.md`: name, location, price per night, three nights, rating |
| Library | the table opens as a page in the app |

Third rung: a public site, no login, browsed in the background while you do something else. The agent does not book; is also what the `browser` tool's Sentinel rules enforce for order and payment buttons.

**Trace:** *pending*: tried on the computer on 2026-09-24, where  sent the headless desktop Chromium to its homepage and rendered only the footer (bot detection); 21 tool calls, then stopped. To be run through the phone's WebView, the backend meant for it; the [launch checklist](launch-checklist.md#9-chinese-services-and-the-showcase-p0) tracks it.

## 5. Book a meeting and tell the group

>  Meeting

| Hand | What it does |
|---|---|
| `calendar` | the slot is free |
| `shell: tmeet meeting create --subject  --start 2026-09-30T15:00+08:00 --end 2026-09-30T15:30+08:00` | one approval card with the exact command; the answer carries `meeting_code` and `join_url` |
| `shell: lark-cli im +messages-send --chat-id oc_… --text "…"` | the group message with  and link; its text on a second card |
| `reminders` | ten minutes before |

Two CLIs, two approvals, no app opened. **Trace:** *pending*: Tencent Meeting and Feishu logins on the test machine (`tmeet auth login`, `lark-cli auth login`).

## 6. Clipboard → calendar + alarm

>  a message:

| Hand | What it does |
|---|---|
| `device__clipboard_read` | the text (Android lets an app read the clipboard only while it is on screen; the tool says so when it is not) |
| `device__calendar_create` | Friday 10:00, the address as the location in the notes; Android's own permission dialog the first time |
| `device__alarm_set` | 09:00 Friday through the clock app |
| `amap__maps_geo` (optional) | the address checked, the travel time added to the notes |

The phone's own capabilities as MCP tools ([device.md](device.md)); nothing leaves the phone except the optional geocode. **Trace:** *pending*: the local build on an Android phone (the device server runs only there).

## 7. A Meituan order that stops before payment

> 

| Hand | What it does |
|---|---|
| `phone_task` in Meituan | search, the restaurant, the set meal, the address; the capsule shows the step and **Stop** all the while |
| the Sentinel | the tap on Submit order is SENSITIVE (`sensitive_words`): **Allow once** / **Deny** on the capsule itself, on the Android phone and in the hosted demo's phone alike; the chat card carries the same request |
| the stop | the operator ends on the payment page and says so; paying is yours, in the app |

The only case on the screen, because Meituan has no personal API and its web needs the app's login. Everything the operator saw and did is in the trace, every tap drawn on its screenshot. Two models share the work: the chat model plans and reports (`MAIN_MODEL` in the showcase box's `.env`; `deepseek-v4.1-flash` when it is empty), the hands model reads each screenshot and picks the tap (`qwen3.8-27b`, `GUI_MODEL`); a visitor's own OpenRouter key gets `qwen/qwen3.8-27b` for the hands.

**Trace:** *pending*: an Android phone with Meituan installed (the x86 emulator cannot run it). The executor, the capsule and Stop were verified on the emulator in [gui.md](gui.md).

## Documented, not shown

Four more screen cases are written up in the `train-tickets` and `phone-messages` skills and stop at the same place; the last confirmation is yours:

- : look up fines, stop before paying.
- : fill in the destination, stop before.
- 12306 app: a booking up to Submit order (the search itself no longer needs the screen).
- JD.com app: the cart up to.

## Never in public material

The agent can read WeChat on the phone's screen when you ask it to, and some people will. The real app does not appear in the showcase, the site or the film, nor do Alipay statements,  or : services whose terms forbid automation or whose data should not be in a demo.

## Reading the trail

Every step is a row in the chat (`12306__get-tickets(…)`, `shell: lark-cli calendar +agenda --as user`, `phone_act: tap "Submit order" at (318,742) in Meituan`) and every approval card says what will be done and why it asks. `Activity` under the avatar keeps the audit log with the channel of every call; `Permissions` shows the grants, which for phone steps are only ever *once*. On your own server, `nanomuse phone traces` lists every phone task and `nanomuse phone trace <id> -o trace.html` renders one as a page with every screen the operator saw and every tap drawn on it ([gui.md → Traces](gui.md#traces)). The Markdown traces under [`docs/traces/`](traces/) are the same timelines, rendered for reading.

Eleven skills carry these habits: `feishu`, `tencent-meeting`, `amap`, `kuaidi100` and `train-tickets` for the services above, `phone-messages` for the screen, `trip-plan`, `meeting-prep`, `inbox-triage`, `compare-options` and `weekly-review` for the agent's own work. `Skills` in the app lists them; a folder of your own with the same name replaces one. Skills written for other agents in the [Agent Skills](https://agentskills.io) format drop into `<data_dir>/skills` as they are, Larksuite's own `lark-*` skills included.

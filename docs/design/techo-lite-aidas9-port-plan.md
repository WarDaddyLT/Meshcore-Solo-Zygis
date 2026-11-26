# T‑Echo Lite Kit AIDAS9 port plan

**Status** · Decisions approved. Implementation and bench validation are in progress.

**Scope** · LilyGO T‑Echo Lite Kit with the physical KeyShield keypad. Proposed integration branch is `update/solo-2.3.0`. The existing Žygis kit target on `main` provides the reference for the keypad, ES8311 audio, and tracking LEDs.

**Source reviewed** · AIDAS9 `aidas9-v0.1.0-pre.1` at commit `3134ba4e`. The review covered its README, keypad handling, menu model, display changes, companion integration, and message storage. [AIDAS9 review source](https://github.com/ksk-lizdeika/MeshCore/tree/3134ba4e) · [Žygis hardware reference](../hardware.md)

The proposal uses AIDAS9’s device-first interface for the kit and Žygis’s transport, tracking, and device configuration underneath it. Review the rows before implementation.

## Screen and keypad

| # | Feature | Proposed source and handling | Replaces or removes | Decision |
| --- | --- | --- | --- | --- |
| 1 | Home carousel | **AIDAS9.** Six entries for Messages, Contacts, Radio, Advert, Device, and Settings. Put Tracking near the top of Settings and make the remaining Solo tools reachable from the kit. | Replaces the kit’s Solo home layout. | use the meain menu style of aidas 9, but include the items and structure of zygis  |
| 2 | Startup splash | **Žygis branding + AIDAS9 behavior.** Use the Žygis logo and WarDaddy credit in a square layout. Hold the screen until a key press. Keep the device handle out of the branding. | Replaces the timed Solo splash and AIDAS9 artwork. | there is a loadign bar that tells exaclty whats happening, it should be in the splash screen at the bottom |
| 3 | E-paper layout and refresh | **AIDAS9 UX + Žygis driver.** Use static frames, bounded text, clear focus, and partial updates. Evaluate the AIDAS9 refresh and rendering changes against the physical kit. | Replaces kit layouts that assume a smaller display. Scope any driver changes to the kit’s panel. | approve |
| 4 | Navigation | **AIDAS9.** Up and Down wrap on Home and stop at the ends of lists. Center and Yes select, Esc goes back, and Home returns to the carousel. | Replaces conflicting Solo key mappings on the kit. | approve |
| 5 | Wake and hardware reset | **AIDAS9.** Consume the first press when waking a sleeping display. The lower-right physical reset button stays wired to reset. | Suppresses the wake press so it cannot also navigate, send, or delete. | aidas9 better as on e ink you always see last state |
| 6 | Keypad driver and diagnostics | **Žygis driver + AIDAS9 diagnostic ideas.** Reuse `TEchoKeyShield.cpp` as the sole keypad FIFO reader and map its events to the approved actions. Use a development build to check physical keys. | Exclude the separate AIDAS9 keypad reader. | approve |
| 7 | Mail, No/X, digits, and `*` | **AIDAS9.** Mail composes or replies in context. No/X requests deletion in a conversation and backspaces in the composer. Digits use multi-tap entry. `*` handles punctuation or a contextual action. | Replaces conflicting kit shortcuts. Deletion requires a separate confirmation. | approve |

## Messages, contacts, and rooms

| # | Feature | Proposed source and handling | Replaces or removes | Decision |
| --- | --- | --- | --- | --- |
| 8 | Channel and private inboxes | **AIDAS9 screens + Žygis data.** Separate the inboxes and show unread counts and empty states using existing channels and contacts. | Replaces the kit’s inbox navigation. | approve |
| 9 | Conversation view | **AIDAS9.** Show one message per screen, chronological scrolling, a position scrollbar, real sender handles, multiline previews, and full-message details. | Replaces the kit’s Solo conversation layout. | approve |
| 10 | Message signal and route details | **AIDAS9 layout + Žygis packet data.** Show route hops, RX RSSI in dBm, and SNR in dB when recorded. Display missing measurements as unavailable. | Adds a details page alongside Žygis discovery commands such as `!triangulate`. | combine where apropriate |
| 11 | Composer | **AIDAS9.** Use a single New message action, multi-tap entry, a static cursor, and draft retention when a send fails. Enforce the actual mesh payload limit. | Replaces the kit’s Solo composer. | approve |
| 12 | Per-conversation drafts | **AIDAS9.** Use its bounded in-memory draft cache, keyed by conversation identity. Clear a draft on successful send and confirm before discarding text. | Adds per-conversation drafts to the kit UX. | approve |
| 13 | Unread state | **AIDAS9 behavior + Žygis storage.** Persist unread state by stable message sequence and conversation identity. Count incoming messages only. | Replaces transient or slot-based unread counting in the kit UI. | approve |
| 14 | Message deletion | **AIDAS9 UX.** Delete by stable message ID with a confirmation that defaults to Cancel. | Replaces index-based deletion. The action applies to the selected message. | approve |
| 15 | Offline delivery and local history | **Žygis storage policy + selected AIDAS9 safeguards.** Keep companion delivery separate from local history. Consider borrowing checksummed replay and deletion markers. | Skip AIDAS9’s drain-on-sync semantics for local history, which would remove messages after phone sync. | approve |
| 16 | Contact directories | **AIDAS9 layout + Žygis contacts.** Group clients, rooms, repeaters, and other nodes. Identify the target by full identity when opening details or starting a message. | Replaces the kit’s contact browser. Keep Solo favourites and available admin actions reachable. | approve |
| 17 | Room login | **AIDAS9 flow + Žygis transport.** Provide masked password entry, deliberate reveal, retry, timeout and rejection states, and Forget password. Remember credentials only after accepted login and associate them with the room’s full public key. Clear them when the room is removed. | Replaces the kit’s room login workflow. | approve |

## Radio, tracking, and hardware

| # | Feature | Proposed source and handling | Replaces or removes | Decision |
| --- | --- | --- | --- | --- |
| 18 | Radio status | **AIDAS9 pages + Žygis readings.** Show the LoRa preset, TX power, RX gain, path-hash mode, noise floor, recent RSSI/SNR, link margin, airtime, queues, errors, packet and advert age, and direct/flood counters. | Replaces the kit’s radio status layout. LoRa editing stays in Žygis settings. | approve |
| 19 | Device health | **AIDAS9 pages + Žygis board data.** Show battery voltage and percentage, power source, uptime, reset reason, temperature, available storage and capacity, BLE, GPS, and build info. Use cached readings and show unavailable values explicitly. | Adds a compact health view. | approve |
| 20 | Manual advert | **AIDAS9 review screen + Žygis send policy.** Confirm before sending a manual identity advert. Keep automatic public location output blocked. | Replaces the advert confirmation screen. The send logic stays with Žygis. | approve |
| 21 | GPS and Tracking | **Žygis.** Keep `!kur`, `!power`, scheduled reporting, fresh and last-known fix labels, discovery, and tracking settings. Show tracking policy and fix state on the kit GPS page. | The kit GPS control goes through the Žygis scheduler. Exclude the separate AIDAS9 GPS power toggle. | approve |
| 22 | Tracking channel lock | **Žygis.** Protect the bound channel’s name, key, scope, and delete action in the kit UI. Preserve USB repair access. | Applies the existing tracking-channel lock to the kit’s channel actions. | approve |
| 23 | BLE and clock | **AIDAS9 controls + Žygis settings.** Use compact Bluetooth and date/time pages while retaining BLE/USB companion support and the saved pairing configuration. | Replaces the kit’s settings layout. Exclude the AIDAS9 default PIN from migration. | approve |
| 24 | Blue and green notification LEDs | **Merge.** Add AIDAS9’s per-event pattern selection, preview, and persistence for channel/private/room messages and newly discovered channels/clients/rooms/repeaters. Give Žygis GPS-fix and position-TX indications priority. | One controller owns both LEDs. Keep automatic BLE and generic TX blinking disabled on the kit. | approve |
| 25 | Sound and tracking alerts | **Žygis.** Keep the ES8311 speaker path, fullscreen alerts, and the rule that an alert-dismissal press is consumed. Route approved AIDAS9 notification events through the existing audio path. | Exclude a separate AIDAS9 buzzer or alarm path. | approve |
| 26 | About and credits | **Žygis About + AIDAS9 attribution.** Show the firmware version and credit KSK Lizdeika for the ported interface. Preserve source and dependency license notices. | Omit the AIDAS9 donation tile and artwork unless approved. | ommit lizdeika, this is now a wardaddy project |
| 27 | Builds, migration, and validation | **Žygis workflow + AIDAS9 test ideas.** Use a dedicated kit build and manual release workflow. Review layout, storage and migration before flashing. Validate keypad, display, tracking, persistence, audio, LEDs, and companion behavior on hardware. | Exclude AIDAS9’s release automation. Any import of AIDAS9 settings or message queues needs its own migration decision. | approved |

## Review decisions

- **#15 Message retention.** Proposed default is to keep local history after companion sync. Choose whether to borrow the AIDAS9 journal safeguards or defer storage work.
- **#24 LED priority.** Proposed default is for Žygis tracking indications to take priority over ordinary message and discovery patterns on each LED.
- **Approval.** Mark the desired rows as Include, Change, Skip, or Defer. Use the Change decision to record the preferred source and what the feature should replace.

# Additional feature
- use the hardware keyboard capability to backlich inputs when interacting and turn off backligt when done with key input
- the up arrow press followed by square arrow press locks the screen into clock view, stops backlight of the inputs, when in locked state, pressing the same two keys one after another unlocks the screen and move to main menu. lock screen always shows message for "press up then square" with icosn like old nokia

## Follow-up decisions

- Match the AIDAS9 carousel’s original center and side icon pixel dimensions. Use the same Font Awesome Free icon pack for Žygis-only destinations.
- Use the Žygis clock and battery row at the top of the carousel.
- Keep the full Žygis emblem and WarDaddy credit on the splash, above the loading progress.
- Place Quick messages and its recent-conversation shortcuts under Messages.

## Bench results

- Žygis Kit K0.1.9 / Solo 2.3.0 / MeshCore 1.18.0 booted after app-only USB DFU. The firmware retained its radio identity, preset, and channels.
- The 192×176 kit framebuffer showed the revised carousel and the Žygis status row. The selected Map icon matched all 4,752 pixels of the AIDAS9-scaled center canvas.
- A second radio verified exact UTF-8 messages in both directions, `!power`, `!kur` with route ACK and status, and `!triangulate` with route ACK and discovery summary. The bench setup removed both temporary channels and restored the kit configuration.
- Host checks passed for gesture timing, icon sizes, the tracking scheduler, command dispatch, CLI framing, and tracking record persistence. Physical lock, notification LEDs, audio, and room and history behavior still need dedicated bench checks.

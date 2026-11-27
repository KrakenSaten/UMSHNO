# External Git dependencies

Reviewed 2026-11-27 for milestone M1. Everything else comes from crates.io, pinned by
`Cargo.lock` with checksums.

## What is pinned

| Dependency | Source | Pinned commit | Used by | Fork vs. its upstream |
|---|---|---|---|---|
| `lora-phy`, `lora-modulation` | `darconeous/lora-rs` | `0a97a66d2c63` | Both workspaces (`[patch.crates-io]`) | 11 ahead, 270 behind `lora-rs/lora-rs` |
| `trouble-host` (BLE host stack, pairing) | `darconeous/trouble` | `9c4f8c0fbfd1` | Both workspaces | 4 ahead, 151 behind `embassy-rs/trouble` |
| `esp-hal` and siblings | `darconeous/esp-hal` | `6477a7b71ef8` | `firmware-esp32` | 7 ahead, 317 behind `esp-rs/esp-hal` |
| `buoyant` (UI layout) | `darconeous/buoyant` | `dd7d37c3b233` | Communicator UI | 55 ahead, 0 behind `riley-williams/buoyant` |
| `nrf-sdc`, `nrf-mpsl` | `alexmoon/nrf-sdc` | `abe49d22ebfc` | nRF52840 firmware | Upstream project itself |
| `esp32*` PACs | `esp-rs/esp-pacs` | `33d9b665f3f9` | `firmware-esp32` | Upstream project itself |

Every pin is a full commit hash recorded in the lockfile, and every pinned commit was still
reachable on 2026-11-27. A force-push cannot silently change what builds; a different commit
fails the build instead.

## Risks

1. **Availability.** Four of the six live on one person's GitHub account. If a fork is
   deleted or its history rewritten and garbage-collected, a clean checkout stops building,
   firmware included. No UMSHNO-controlled copy exists.
2. **Stale security fixes.** The forks are far behind their upstreams. `trouble` matters
   most: it implements BLE pairing and bonding, the boundary security finding S4 is about,
   and it is 151 commits behind. Whether those commits include security fixes has not been
   reviewed.
3. **Review burden.** Moving a pin means reviewing a fork's private changes plus whatever it
   merged from upstream. The patches are not tracked anywhere else.
4. **No policy gate.** Nothing stops a pull request from adding a new Git source, or a
   crates.io dependency with a known advisory.

## Recommendations

In order of value:

1. **Mirror the six pinned repositories under a UMSHNO-controlled account** (each as a fork,
   so the relationship stays visible), and point `[patch.crates-io]` and the ESP32
   workspace at the mirrors **at the same commits**. The lockfiles then change only in their
   source URLs, and the build is unchanged. This needs new GitHub repositories, so it waits
   for maintainer approval.
2. **Add `cargo-deny` to CI** with an allow-list of Git sources (the mirrors) and the RustSec
   advisory database, failing on a new Git source or an advisory. It runs in seconds.
3. **Review `trouble` upstream's changes since the fork point** for pairing, bonding, and
   LE Secure Connections fixes, together with the open question of whether UMSH enforces
   Secure Connections only (assessment, "Open questions").
4. **Record each fork's private patches** (the "ahead" commits) in this file, so moving a pin
   is a bounded review, and offer them to their upstreams where they are general.

# UMSHNO technical assessment

Baseline: upstream UMSH `38f06ba28` (2026-11) plus the ThinkNode M6 port. This is an
engineering review of what exists, done to set UMSHNO's priorities. It is not a
specification.

Status legend: **Implemented** (code and tests), **Experimental** (code, light testing, or
flagged WIP), **Incomplete** (partly built), **Proposed** (documents only).

## Summary

UMSH is far more mature than an "experimental protocol" label suggests. The core stack is
`no_std` Rust with about 4,100 unit tests, nine continuously fuzzed targets, release builds
of every nRF52840 board in CI, two native mobile apps over one shared Rust core, a
self-hosted internet bridge, and first-class Wireshark tooling. UMSHNO should not rewrite any
of it. The weaknesses are in the gaps between components:

1. **Verification on real hardware.** There is no hardware-in-the-loop testing. The Android
   app is verified only on the emulator. Most board support packages have no tests.
2. **Reliability features that users notice.** Mesh-level store-and-forward does not exist,
   manual retry of a failed message is unfinished, and the routing reliability plan is about
   half delivered.
3. **Protocol maturity.** Every UEP is still Experimental, and ULCP, bridging, and node
   management are unnumbered proposals whose normative text lives in the legacy book.
4. **Maintainability.** A handful of files are very large (`umsh-ulcp-device/src/session.rs`
   23.6k lines, `umsh-mobile-core/src/ulcp.rs` 15.6k, `umsh-mac/src/coordinator.rs` 10.1k,
   `firmware/nrf52-tracker/src/main.rs` 8.3k), and several plan documents are stale.
5. **Upstream concentration.** One maintainer, and forked dependencies hosted on that
   maintainer's personal account.

## 1. Protocol architecture and security

See [Security review](#security-review) below: no Critical or High findings, four Medium.

- **Implemented:** Ed25519 identities with 3-byte hints; X25519 ECDH; AES-SIV (RFC 5297)
  with AES-256; HKDF with per-purpose domain separation; monotonic frame counters with
  counter resynchronization; PFS sessions; blind unicast; channel keys; authenticated ACKs.
- **Design strengths worth keeping:** nonce-misuse resistance (a counter reuse after a
  reboot leaks only plaintext equality), no clock dependency, composable routing options,
  and a wire format designed together with its dissector.
- **Concern:** the UEP set is Experimental throughout. Interop is defined by the reference
  implementation, not by an accepted spec. UMSHNO's compatibility promise is only as
  strong as upstream's stability. This is a reason to stay close to upstream, not to fork the
  protocol.

## 2. Cryptographic implementation and key management

See [Security review](#security-review). Key custody is well designed on mobile: iOS keeps
the identity in the Keychain (ADR ios/0002), Android wraps it with Keystore (ADR
android/0002, StrongBox and TEE unverified on hardware), and frame counters persist
(ADR ios/0003). No non-cryptographic RNG is permitted anywhere, by project rule.

## 3. Mesh routing, flooding, and reliability (`crates/umsh-mac`, 571 tests)

| Feature | Status |
|---|---|
| Flood forwarding, hop limits, region codes, duplicate suppression | Implemented |
| Source routes, route cache, trace route, path discovery | Implemented |
| ACK paths, forward confirmation, retries | Implemented |
| Repeater role, adaptive ("auto") forwarding | Implemented, recently changed |
| Routing reliability plan M0, M1/M2 (reduced), M5 (narrow), first slice of M4 | Implemented |
| Plan items M3, M6–M10 | Proposed |
| Network simulator | Incomplete: `test_support::ModeledNetwork` covers single scenarios; no multi-node simulation tool |
| Signal reports, signal-quality filtering | Proposed |

The coordinator is well tested but concentrated in one 10k-line file. Without a multi-node
simulator, routing changes are judged on unit scenarios and anecdotal field use. That is the
main limit on routing work.

## 4. Firmware and hardware support

- One shipping image per board, role chosen by configuration: a good decision that keeps the
  release matrix small.
- nRF52840: T-1000E, T-Echo, SenseCAP Solar P1, Wio Tracker L1, XIAO nRF52840, ThinkNode M6.
  ESP32/ESP32-S3: Heltec V2 and V3 (plus a V3 bridge image), T-Beam Supreme, T-LoRa Pager,
  T-Deck, XIAO ESP32S3.
- Budgets are tight and watched: nRF images use 462–478 KiB of a 756 KiB window and 134–145
  KiB of 256 KiB SRAM, with an 8 KiB heap. CI guards flash size and stack depth.
- **ThinkNode M6 (UMSHNO):** Experimental. It builds in CI's firmware matrix. LoRa RX, the
  battery divider, buttons and LEDs, System OFF, and GNSS fixes are unverified on hardware.
  It is missing from `scripts/release.py`, `site/`, and the shipping matrix, and its BSP has no
  tests.
- `alloc` is required by `umsh-node` and the layers above it, which forces a heap on every
  MCU. This is acceptable at 8 KiB, and not worth a rewrite.

## 5. Chat, private messaging, and groups (`crates/umsh-text`, 178 tests)

| Feature | Status |
|---|---|
| Codec, sequencing, fragmentation, bounded repair and resend | Implemented |
| Direct messages; delivery state from MAC ACKs | Implemented |
| Channels and groups | Implemented (the plan document's status is stale) |
| Manual retry of a failed fragment | Incomplete: needs an attempt/generation design |
| Compose-state checkpoint beyond 8 active / 24 cold conversations | Incomplete |
| Device-side queue for an absent phone (`CMD_QUEUE_DRAIN`) | Experimental |
| Mesh-level store-and-forward for an offline recipient | Proposed (not designed) |
| Chat rooms | Removed upstream (`umsh-chat-room`); only a proposal remains |

Offline delivery is the largest user-visible gap compared with MeshCore room servers. It
needs a protocol design, so it belongs on the roadmap as research, not as a quick feature.

## 6. Android (`apps/android`)

Kotlin and Jetpack Compose over the shared Rust core (UniFFI over JNA), about 40k lines of
app code, with 11.5k lines of JVM tests and 15.3k lines of instrumented tests. It covers
onboarding, conversations, channels, peers (QR and Meet exchange, neighbors, ping and route),
the map, settings, and a background link through CompanionDeviceManager. Seven ADRs are
Accepted.

**Experimental:** verified on the emulator against a Bumble peripheral, not on a phone and a
radio. Instrumented tests do not run in CI. Compared with iOS it lacks remote node
management, device setup and provisioning, Wi-Fi, and bridge configuration. UMSHNO does not
need a new Android app; it needs this one verified on hardware and brought to parity.

## 7. iOS (`apps/ios`)

SwiftUI, about 45k lines, the most feature-complete client (including remote management and
an LAN radio extension), over `umsh-mobile-core` (992 tests, the best-tested crate). The app's
own tests are thin: about 2.5k lines. Its store identity (`com.voria.umsh.*`) belongs to
upstream's distribution, so UMSHNO cannot ship it as-is (see [branding.md](branding.md)).

## 8. Repeaters and internet gateways

| Component | Status |
|---|---|
| Repeater role on every board; MeshCore v1 forwarding on Solar, XIAO nRF52, M6 | Implemented / Experimental |
| `tools/umsh-bridge`: TLS 1.3, Ed25519 pinning, rate limits, BLE/serial/UDP radios (95 tests) | Implemented |
| Embedded bridge client (`umsh-bridge-client`), Heltec V3 bridge image, T-Beam client | Experimental |
| LAN bearer (UDP multicast, DNS-SD) | Experimental (its plan document is stale) |
| BLE bearer | Proposed |

The bridge joins separate meshes through an operator-run server with no CA or cloud service.
That matches UMSHNO's principles. What is missing is operational: health monitoring,
configuration at scale, and documented deployment.

## 9. Diagnostics, logging, and network inspection

Strongest area of the project. `umshctl` (183 tests) covers inspection, configuration,
ping, routes, discovery, management, and capture, and installs as a Wireshark extcap. The Lua
dissector decrypts with configured keys and has golden-pcap tests in CI. Firmware records
panic breadcrumbs and watchdog captures. The browser ULCP debugger is Experimental.
**Missing:** mesh-wide health telemetry (signal reports are only a proposal), and a way to
collect field diagnostics from users.

## 10. Tests, performance, and resource use

- CI: rustfmt in three workspaces, `cargo test --locked`, feature-matrix tests, clippy
  `-D warnings`, mdBook builds, dissector tests, fuzz builds, region database, nRF52840
  release builds, iOS, and Android. ESP32 builds run on `main` only, not on pull requests.
- Fuzzing: nine targets, run nightly, with seeds replayed by `cargo test`.
- **Gaps:** no hardware-in-the-loop; board BSPs largely untested; Android instrumented tests
  and ESP32 builds do not gate pull requests; no multi-node simulation; no on-air
  performance measurements (airtime per delivered message, delivery ratio).
- **Windows:** `umsh-mobile-core` does not build on Windows (`libc::clock_gettime` in
  `app_core/clock.rs`, and `rusqlite` without `bundled`). Because it is a default workspace
  member, `cargo test` fails on Windows. UMSHNO develops on Windows, so this matters.

## Security review

A read-only review of the implementation against UEP-0007 and UEP-0009. It found **no
Critical or High findings**. The cryptographic core is sound. The findings are in replay
state, physical security, and authorization boundaries. None needs a wire change to fix.

| ID | Severity | Finding | Where | Fix direction |
|---|---|---|---|---|
| S1 | Medium | A peer's first-contact baseline is not persisted until 16 frames arrive, so after a power loss its earlier frames (up to 15) replay as first contact. UEP-0007 requires persisting each known peer's baseline. | `crates/umsh-mac/src/rx_windows.rs` (`accept`, `needs_persist`) | Set `write_now` on the first accepted frame of a registered window, and when a stranger is promoted to a peer |
| S2 | Medium | Unsigned multicast (and signed frames from strangers once the displacement quota is spent) can be replayed indefinitely by cycling more than 64 frames through the FIFO duplicate cache. A reboot clears the cache too. The spec concedes eventual replay; the cache size makes it trivial. | `crates/umsh-mac/src/coordinator.rs` (`accept_first_copy`), `lib.rs` (`DUP` = 64) | A larger, separately sized first-copy cache, or a reject-only counter floor per claimed source; document that applications must not act on unsigned channel traffic |
| S3 | Medium (physical) | The node private key, BLE bond keys, pairing PIN, and entropy seed are stored in plaintext flash, with no nRF52 APPROTECT and no ESP32 flash encryption. SWD or the ESP32 download mode yields the identity. | `crates/umsh-flash-store`, `crates/umsh-journal-store` | APPROTECT in release images; ESP32 flash encryption with download mode disabled; a documented physical threat model. Needs a DFU and recovery plan first, because both lock out debug access |
| S4 | Medium | A mesh administrator can write `PROP_BLE_BOND_COUNT`, `PROP_BLE_PAIRING`, and `PROP_BLE_PAIRING_PIN`. Wiping the bonds clears the PIN and opens a Just Works pairing window, and anyone in BLE range who pairs gets a secure link that can install a device private key, which mesh admin is otherwise forbidden to do. | `crates/umsh-ulcp/src/ids.rs` (`admin_writable`), `firmware/nrf52-tracker/src/main.rs` (bond wipe) | Exclude the three BLE properties from `admin_writable`, or refuse a mesh-initiated bond wipe and window while no PIN is set |
| S5 | Low | `umshctl` writes its admin private key with default permissions (typically 0644). | `tools/umshctl/src/mesh.rs` | `create_new` with mode 0600 and a 0700 directory, as `tools/umsh-bridge/src/keygen.rs` does; an ACL on Windows |
| S6 | Low | X25519 secrets are not zeroized (`x25519-dalek` built without `zeroize`), against UEP-0009's erasure requirement for PFS ephemerals. `ChannelKey` is `Copy` with no zeroize. | `Cargo.toml`, `crates/umsh-crypto/src/lib.rs`, `crates/umsh-core/src/packet.rs` | Enable `x25519-dalek/zeroize`; make `ChannelKey` non-`Copy` and `ZeroizeOnDrop` |
| S7 | Low | Mesh admin requests need authentication but not encryption, so in unencrypted (amateur) mode a key-bearing write crosses the air in cleartext. Forgery is still impossible. | `crates/umsh-node-mgmt/src/device_adapter.rs` | Refuse key-bearing writes that did not arrive encrypted |
| S8 | Low | The pairing-PIN lockout resets on every power cycle. | `crates/umsh-ulcp-runtime/src/ble_security.rs` | Persist the escalation, or rotate the PIN after repeated failures |
| S9 | Low | Forwarding amplification: the forward duplicate cache (64 entries, keyed on the unverified MIC) and 15-hop floods let junk or evicted old floods re-flood the mesh; there is no per-neighbor rate limit. | `crates/umsh-mac/src/coordinator.rs` | Per-neighbor token buckets on forwarding; a larger cache |

**Informational:** blind-unicast keys are the XOR of the pairwise and channel keys (an HKDF
combine with a label would be cleaner; no practical attack); counter-journal entries are keyed
on an 8-byte key prefix (collision needs about 2^64 work); 4-byte MICs on PFS sessions and
ACKs are a stated design choice bounded by airtime; with no PIN set, first pairing is open
Just Works to whoever is in range first (documented).

**Strengths to preserve:** AES-SIV checked against RFC 5297 vectors; constant-time MIC
comparison; AAD covering the header, addresses, SECINFO, static options, and the blind
address block; distinct HKDF labels; pairwise info binding both full Ed25519 keys; canonical
points, all-zero shared-secret rejection, and `verify_strict`; TRNG-seeded keys with no
non-cryptographic RNG; a write-only device private key that cannot be set over the mesh;
bonded, encrypted BLE before any ULCP access; Keychain and Keystore custody on mobile; PFS
ephemerals authenticated, rate-limited, and never persisted; 25 fuzz targets across the
parsers.

**Open questions for deeper review:** whether the BLE stack (`trouble-host`) enforces LE
Secure Connections only; whether a factory reset or `CMD_CLEAR` clears counters while
keeping peers (which would put every peer into S1 at once); the safety of the counter
resynchronization path that can move a baseline backwards; ESP32 Wi-Fi credential storage;
fuzz targets for `PfsSessionRecord::decode_all` and the journal-store decoders; admin replay
protection when `umshctl-admin.counters` is lost.

S1, S2, S4, and S6 apply to upstream UMSH as well and should be reported there.

## Technical debt, ranked

1. Security findings S1, S2, S4 (code fixes) and S3 (release hardening).
2. No hardware-in-the-loop; board and Android verification is manual or missing.
3. Mesh-level offline delivery is undesigned.
4. Very large source files in the device session, mobile ULCP, MAC coordinator, and firmware
   main.
5. Duplicated per-board manifests (nRF52 copies the feature table; ESP32 needs a drift
   checker).
6. Stale plan documents (LAN bearer, MeshCore forwarder, text chat engine, shipping matrix).
7. Windows host build broken.
8. ThinkNode M6 release and site integration missing.
9. Forked dependencies hosted on the upstream maintainer's account.

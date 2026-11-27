# UMSHNO identity and identifier policy

UMSHNO is the project. UMSH is the protocol it speaks. This page records which names
UMSHNO has changed, which it keeps, and what it would take to change the rest.

The rule: **a name that a device, an install, or another UMSH node depends on keeps its
current value until an ADR gives a migration that cannot lose an identity, a key, or a
setting.** Project-level prose, documentation, and metadata change freely.

## Changed

| Item | From | To |
|---|---|---|
| Project name in README, AGENTS.md, and the UMSHNO docs | UMSH | UMSHNO (on UMSH) |
| Workspace `repository` metadata (`Cargo.toml`, `firmware-esp32/Cargo.toml`); not compiled into any binary | `darconeous/umsh` | `KrakenSaten/UMSHNO` |
| Communicator About › Credits first entry (`crates/umsh-ux-communicator/src/ui/about.rs`) | UMSH | UMSHNO, built on UMSH, with both licenses and links |
| Simulator window title (`firmware/host-communicator/src/main.rs`) | UMSH communicator | UMSHNO communicator |

## Kept, and why

| Identifier | Where | Category | What changing it breaks |
|---|---|---|---|
| Crate names `umsh-*`, `umsh` umbrella, Rust module paths | `crates/`, `umsh/` | Code | Every upstream merge conflicts; no user value |
| KDF, signature, and hash domain-separation labels (`UMSH-PAIRWISE-SALT`, `UMSH-CHAN-ID`, `UMSH-MCAST-V2`, `UMSH-UNICAST-V3`, `UMSH-SIG`, `UMSH-VERIFY-FRAME-NONCE`, `UMSH meet *`) | `crates/umsh-crypto/src/lib.rs`, `crates/umsh-core/src/packet.rs`, `crates/umsh-mac/src/coordinator.rs`, `crates/umsh-node/src/meet/mod.rs` | Wire | Nothing decrypts or verifies against UMSH nodes; every existing channel is lost |
| Local RNG labels (`umsh-entropy-pool-v1`, `umsh-reseeding-rng-v1`) | `crates/umsh-crypto/src/pool.rs`, `crates/umsh-ulcp-runtime/src/reseed.rs` | Local derivation | Changes how persisted seed material is derived, for no gain |
| URI prefixes `umsh:n:`, `umsh:gs:`, `umsh:gk:`; URL schemes `umsh`, `umsh-notification` | `crates/umsh-uri`, both apps | Wire / interop | Every shared contact, channel invitation, and printed QR code |
| GATT service UUID `21EB6B15-…`, BLE company ID `0xFFFF` and model IDs | `crates/umsh-ulcp/src/gatt.rs`, `crates/umsh-ulcp-runtime/src/ble_privacy.rs` | Discovery | Every app and host tool finds radios by these, not by name |
| DNS-SD `_umsh._udp` and its multicast group; ALPN `umsh-bridge/1` | `crates/umsh-lan-bearer`, `crates/umsh-bridge-client`, `tools/umsh-bridge` | Wire | LAN peers stop seeing each other; deployed bridge clients fail TLS |
| ULCP identifiers, PHY profile IDs (`umsh-us-ca`) | `crates/umsh-ulcp*` | Wire / persisted | Host tools and apps talking to a radio; saved profile selections |
| Default BLE names `UMSH <board>` | `firmware/nrf52-tracker/src/main.rs`, `firmware-esp32/firmware/esp32-tracker/src/main.rs` | Host matching | Discovery is UUID-based, but user-written `--ble=` and bridge `selector` values substring-match the name, tests assert it, and an unrenamed radio would change name on a firmware update |
| iOS bundle IDs `com.voria.umsh.*`, App Group `group.com.voria.umsh`, Android `applicationId` `com.voria.umsh` | `apps/ios/UMSH.xcodeproj`, `*.entitlements`, `apps/android/app/build.gradle.kts` | Persisted | A new ID is a new app with an empty sandbox, Keychain, and Keystore |
| iOS Keychain services `com.voria.umsh.identity-secret`, `com.voria.umsh.channel-keys`; Android Keystore aliases `com.voria.umsh.*`; app storage directories (`UMSH/`, `files/umsh/`) | `apps/ios/UMSH/Services/Identity`, `apps/android/.../AppPaths.kt` | Persisted | **Identity private key** and channel keys lost; contacts, conversations, and frame counters lost |
| ESP32 flash partition label `umsh` | `firmware-esp32/partitions-umsh*.csv`, `umsh-bsp-esp32/src/flash_store.rs` | Persisted | Firmware panics at boot; node identity and settings live there |
| `umshctl` state directory (`$XDG_STATE_HOME/umsh`, holding `umshctl-admin.key` and its counters) | `tools/umshctl/src/connection.rs` | Persisted | Admin identity lost, so every managed device must re-authorize it; counter reset looks like replay |
| `/etc/umsh-bridge/` identity and config, `UMSH_BRIDGE_CONFIG` | `tools/umsh-bridge/src/cli.rs`, `contrib/systemd` | Persisted | Bridge identity and config not found |
| `umshctl`, `umsh-bridge` binaries; Wireshark extcap `umsh`/`umsh-lan`; dissector protocols `umsh`, `umsh.ulcp`, `umsh.app` | `tools/`, `dissectors/` | Host integration | Scripts, systemd units, saved Wireshark preferences, display filters, and coloring rules |
| Firmware flash layout on nRF52 | `crates/umsh-flash-store`, `crates/umsh-journal-store` | Persisted | Node identity, counters, and configuration on every flashed board |
| Device splash logo | `crates/umsh-splash` | User-visible | Nothing technical; needs UMSHNO artwork first |
| Protocol spec links `darconeous.github.io/umsh/docs/protocol/` | Rustdoc, README | Reference | Nothing; it is the UMSH specification |

## Deferred decisions

These need a decision from the maintainers before any code changes:

1. **App identity.** The `com.voria.*` namespace belongs to upstream's distribution, so
   UMSHNO cannot publish store builds under it. Publishing UMSHNO apps needs a UMSHNO-owned
   reverse-DNS prefix and signing identities, and then a new bundle ID and application ID.
   Those are new apps: users move over by exporting and importing identities (the Identity
   Export Format proposal), not by an in-place upgrade. App display names, permission texts,
   localized "UMSH …" strings, and log subsystems change in the same step, so a build never
   says "UMSHNO" while carrying upstream's ID. Change the iOS log subsystems together with
   `DiagnosticsLog.swift`'s `subsystemPrefix`, which filters on them.
2. **Release channel.** `scripts/release.py` (`DEFAULT_REPO`), `make release-mirror`, the
   web flasher, and `site/` publish to upstream's GitHub Releases and `umsh.dev`. UMSHNO
   needs its own release repository, and a domain or GitHub Pages site, before
   these are repointed.
3. **Forked dependencies.** `lora-rs`, `trouble`, `esp-hal`, and `buoyant` are pinned
   from the upstream maintainer's GitHub account. UMSHNO should mirror each pinned
   revision under its own organization so a deleted or rewritten upstream fork cannot
   break a clean build.
4. **Default BLE names.** If UMSHNO firmware ever advertises a different default name,
   it applies only to devices without a saved name, and host tools must accept both prefixes
   first.

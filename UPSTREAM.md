# UMSHNO and upstream UMSH

UMSHNO is an independently maintained LoRa mesh communication platform built on
[UMSH](https://github.com/darconeous/umsh), created by Robert Quattlebaum. UMSH supplies the
protocol, the Rust reference implementation, the firmware, the mobile apps, and the tooling
that UMSHNO starts from. UMSHNO keeps that work and its history intact, and builds on it.

## Attribution and licensing

- UMSH is dual-licensed under [Apache-2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT). UMSHNO
  keeps both license files unchanged, keeps the upstream copyright notice, and distributes its
  own contributions under the same dual license.
- The full upstream Git history is preserved. Every upstream commit keeps its original author.
- Files UMSHNO modifies are identified by Git history (Apache-2.0 §4(b)). Upstream carries no
  `NOTICE` file, so there is no NOTICE text to propagate.
- Forked third-party dependencies (`lora-rs`, `trouble`, `esp-hal`, `buoyant`) are pinned by
  commit in `Cargo.toml` and `firmware-esp32/Cargo.toml`, and are hosted on the upstream
  maintainer's GitHub account. Their own licenses apply.

## What "UMSHNO" renames, and what it does not

UMSHNO is the name of this project and its distribution. **UMSH is the name of the protocol it
speaks**, and the protocol identity stays UMSH so UMSHNO nodes and upstream UMSH nodes form one
mesh. The following deliberately keep their `umsh` names:

| Kept | Why |
|---|---|
| Crate names (`umsh-*`), the `umsh` umbrella crate, Rust APIs | Renaming buys nothing and makes every upstream merge conflict |
| Wire constants, KDF labels, URI scheme (`umsh:`), ULCP identifiers | Changing any of them forks the protocol |
| GATT service UUID, BLE company and model IDs, DNS-SD `_umsh._udp`, ALPN `umsh-bridge/1` | Hosts, apps, and bridges find each other by them |
| Default BLE names (`UMSH <board>`) | User-written `--ble=` and bridge `selector` values match them, and an unrenamed radio would change name on update |
| iOS bundle ID, Android application ID, Keychain/Keystore names, App Group, storage directories, ESP32 `umsh` partition, `umshctl` state directory, `/etc/umsh-bridge` | Changing them strands existing identities, keys, and settings |
| `umshctl`, `umsh-bridge` binary names | Scripts, Wireshark extcap, and systemd units name them |
| Protocol specification links (`darconeous.github.io/umsh`) | That is where the UMSH specification is published |

Renaming any of these needs an ADR with a migration path that cannot lose a key or a setting.
See [docs/umshno/branding.md](docs/umshno/branding.md) for the identifier inventory.

## Tracking upstream

The local clone carries two remotes:

```sh
git remote add upstream https://github.com/darconeous/umsh.git   # read-only reference
git fetch upstream
```

- `origin`: the UMSHNO repository.
- `upstream`: UMSH. Never pushed to.

Importing upstream work:

1. `git fetch upstream`, then review `git log --oneline HEAD..upstream/main`.
2. Prefer merging `upstream/main` into a dedicated `sync/upstream-YYYY-MM-DD` branch over
   cherry-picking. A merge keeps upstream commit IDs, so later syncs stay cheap and
   `git log upstream/main..HEAD` stays an accurate list of UMSHNO divergence.
3. Cherry-pick only when a single upstream fix is needed ahead of a full sync.
4. Run the checks for the areas the sync touched, then merge the sync branch by pull request.

Work worth sending back to UMSH (bug fixes, board support) goes as a pull request from the
`KrakenSaten/umsh` fork, branched from `upstream/main`, so it carries no UMSHNO branding.

## Divergence log

| Change | Wire-compatible | Notes |
|---|---|---|
| Project identity, documentation, roadmap | Yes | No protocol, storage, or identifier changes |
| Elecrow ThinkNode M6 board support | Yes | New board; `crates/umsh-bsp-thinknode-m6`, `firmware/thinknode-m6` |

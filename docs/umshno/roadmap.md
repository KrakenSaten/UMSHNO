# UMSHNO roadmap

UMSHNO's aim is a LoRa mesh people can rely on: messages that arrive or say clearly that
they did not, keys that stay safe, firmware that stays up, and apps that work on real
phones. The roadmap puts that ahead of protocol growth. It builds on the
[technical assessment](assessment.md).

Principles for every milestone:

- **Wire-compatible with upstream UMSH by default.** A protocol change needs its own UEP,
  a justification, and a migration plan, and is offered upstream.
- **No lost state.** No change may strand an identity, a key, a counter, or a setting.
- **Measured, not assumed.** A reliability or performance claim comes with the test or
  measurement that shows it.
- **No cloud dependency.** Everything works on a mesh with no internet, and anything
  internet-facing is self-hostable.
- **Stay mergeable.** Prefer work that keeps `git merge upstream/main` cheap.

## Priority assessment

| Candidate | Value | Feasibility now | Verdict |
|---|---|---|---|
| P1 Core stability: correctness, security, firmware stability, tests | Highest: everything else depends on it | High; the base is strong | **First** |
| P2 Communication: delivery states, retry, offline delivery, bandwidth | High: what users judge | Delivery and retry high; offline delivery needs protocol design | **Second**, offline delivery as research |
| P3 Android | High: most users carry Android | An app already exists; needs hardware verification and parity, not a rewrite | **Second, in parallel** |
| P4 Mesh infrastructure: repeaters, bridges, health, administration | Medium-high for operators | Bridge and repeaters exist; health telemetry needs a protocol | **Third** |
| P5 Advanced: mapping, sensors, adaptive routing, extensions | Medium | Maps and sensors partly exist; adaptive routing needs a simulator first | **Research track** |

## Milestones

### M0: UMSHNO foundation (this branch)

- **Objective:** establish UMSHNO's identity without risk to devices, installs, or interop.
- **Delivered:** rebased on current upstream; ThinkNode M6 carried forward and aligned;
  README, AGENTS.md, `UPSTREAM.md`, the [identifier policy](branding.md), this roadmap, and the
  assessment.
- **Acceptance:** no wire, storage, or identifier change (see branding.md); CI green on the
  new repository.

### M1: Trusted baseline (recommended next)

- **Objective:** a baseline UMSHNO can build, test, and trust on its own machines and its own
  GitHub account, with known security issues closed.
- **Scope:**
  1. Fix security findings S1 (persist first-contact baselines), S4 (keep BLE pairing
     properties out of mesh admin), S2 (replay-resistant first-copy cache), S5 (`umshctl`
     key file permissions), and S6 (zeroize X25519 secrets and channel keys), each with a
     regression test, and report S1, S2, S4, and S6 upstream. S3 (APPROTECT and ESP32 flash
     encryption) gets a written plan here, covering DFU, recovery, and support access, and
     lands in M6 with the first UMSHNO release.
  2. Make the host workspace build and test on Windows: a Windows arm for
     `umsh-mobile-core/src/app_core/clock.rs` (`QueryPerformanceCounter` or `std::time::Instant`
     with matching semantics), and SQLite bundling for host builds.
  3. Mirror the pinned forks (`lora-rs`, `trouble`, `esp-hal`, `buoyant`) under the UMSHNO
     organization at the same revisions, and point both workspaces at the mirrors.
  4. CI on the UMSHNO repository: the existing workflow green, plus a `windows-latest` host
     job.
- **Dependencies:** M0; the GitHub repository (see "GitHub repository" in `UPSTREAM.md`).
- **Deliverables:** fixes with tests; a Windows CI job; mirrored dependencies; an updated
  divergence log in `UPSTREAM.md`.
- **Acceptance:** `cargo test --locked` passes on Windows, macOS, and Linux; `cargo tree`
  resolves only UMSHNO-hosted or crates.io sources; each security fix has a failing-before,
  passing-after test.
- **Security and compatibility:** fixes must not change the wire format. If one must, it
  gets a UEP and goes upstream first.
- **Order:** Windows build first (it unblocks local testing), then S4 and S1 (the two with a
  concrete remote or power-loss attack), then S2, S5, and S6, then the dependency mirrors and
  CI.

- **Progress (2026-11-27, branch `m1-trusted-baseline`):** Windows host build and CI job
  done; S1, S5, and S6 (X25519) fixed and S4 mitigated (residual: reset into the first-boot window), each with regression tests; S2 reproduced and deferred
  to a UEP-0007 discussion; dependency review in [dependencies.md](dependencies.md). Remaining:
  mirroring the forked dependencies (needs new repositories), `cargo-deny`, and the S3 plan.

#### Protocol behavior changes in M1

One change alters what a device does in response to a protocol message, with no change to
the wire format:

- **Administrative binding refuses Bluetooth pairing writes.** `PROP_BLE_BOND_COUNT`,
  `PROP_BLE_PAIRING`, and `PROP_BLE_PAIRING_PIN` join `PROP_DEV_PRIVATE_KEY` in the set a
  mesh administrator may not write, answered with the existing `STATUS_NOT_PERMITTED`
  (`docs/protocol-legacy/src/app-node-management.md`, "The mesh administrative binding").
  The device's own interface keeps them.
  - *Justification:* a bond grants the local binding, which may install a device
    identity, so these writes let an administrator exceed its binding (security finding S4).
  - *Compatibility:* UMSHNO and upstream nodes still interoperate. A client managing a
    UMSHNO device over the mesh sees a refusal it already handles; upstream devices
    behave as before.
  - *Migration:* none needed; nothing persisted changes.
  - *Upstream:* to be proposed to UMSH with the fix, as an amendment to the node
    management specification.

#### M1 follow-ups

Open after M1, in order. None changes the wire format.

1. **Dependency hardening** (no hardware; needs approval to create repositories).
   - Mirror the six Git-pinned dependencies under a UMSHNO-controlled account at the
     same commits.
   - Repoint both workspaces at the mirrors. Only the lockfiles' source URLs may change.
   - Add `cargo-deny`, with the mirrors as the only allowed Git sources and RustSec
     advisories checked.
   - *Done when:* `cargo tree` shows no source outside crates.io and the mirrors, and
     CI fails on a new Git source.
2. **S4 residual: first-boot pairing window** (firmware; first change of M2).
   - *Impact:* a mesh administrator can factory-reset a device, or reboot one with no
     bonds, into the Just Works window that opens at boot when no PIN is set. Whoever is
     in BLE range can then pair, and through the local binding install an identity. The
     original identity is erased, not stolen; the device itself is taken over.
   - *Requirement:* a boot window with no PIN opens only on a physical action (button
     or screen), or is refused after a reset requested over the mesh.
   - *Done when:* verified on at least one nRF52840 and one ESP32 board, and the
     first-pairing behavior is written into the node management specification.
3. **S2: unsigned multicast replay** (spec first).
   - *Impact:* an eavesdropper without the channel key who records more than 64 channel
     frames can replay them, and each is delivered to applications again. Signed and
     unicast traffic is unaffected.
   - *Interim requirement:* applications must not act on unsigned channel traffic as if
     it were fresh.
   - *Fix path:* propose a UEP-0007 amendment upstream: a reject-only check of unsigned
     frames against the claimed source's existing window, which unsigned frames never
     advance. Measure its false-rejection rate (hint collisions, reordering) in the
     simulator before implementing.
4. **Offer the M1 fixes upstream:** S1, S4, S5, S6, and the Windows build, as separate
   pull requests from a fresh fork.
5. **Small items from review:**
   - hide remote pairing controls for devices that report UMSHNO firmware;
   - write the S1 baseline for a first frame carrying counter 0;
   - make `ChannelKey` non-`Copy` and zeroized;
   - fix the flaky upstream test helper (`sent()` racing the chat engine).

### M2: Hardware verification loop

- **Objective:** know that each supported board works, and keep knowing it.
- **Scope:** a written per-board acceptance checklist (radio TX/RX, battery reading,
  buttons, LEDs, sleep, GNSS, BLE pairing, persistence across reboot and update); complete it for
  the ThinkNode M6 and the boards UMSHNO maintainers own; a small bench rig (two or three
  radios on USB) driven by `umshctl` scripts that run a send/receive/ACK smoke test.
- **Dependencies:** M1. Hardware access.
- **Deliverables:** checklists under `docs/hardware/`; smoke-test scripts in `scripts/`;
  results recorded per release.
- **Acceptance:** each board in the UMSHNO shipping matrix has a dated, passed checklist; the
  smoke test runs from one command.
- **Security and compatibility:** the smoke test also checks that identity and counters
  survive a firmware update.

### M3: Delivery you can trust (P2)

- **Objective:** a sender always knows whether a message arrived, and failures recover.
- **Scope:** finish manual retry of a failed fragment (attempt/generation design in
  `docs/text-chat-engine-plan.md`); persist the compose checkpoint beyond the current
  conversation limits; align delivery states across iOS, Android, and the communicator; build
  a multi-node simulator on `umsh_mac::test_support::ModeledNetwork` that reports delivery ratio
  and airtime per delivered message under loss.
- **Dependencies:** M1.
- **Deliverables:** retry in the text engine and all three clients; the simulator with baseline
  numbers committed.
- **Acceptance:** simulator scenarios (line, star, lossy links) meet a documented delivery
  ratio; retry has engine tests and client UI tests.
- **Protocol changes:** none expected. If the retry design needs a wire change, it gets
  its own UEP section first.

### M4: Android on real hardware (P3)

- **Objective:** the existing Android app, verified on phones and radios, at feature parity
  with iOS for everyday use.
- **Scope:** run each ADR's Pixel checklist; run instrumented tests in CI on an emulator; add
  device setup and provisioning and remote node management, reusing `umsh-mobile-core`.
- **Dependencies:** M2 (bench radios); M6 decides the shipping identity, but this work does
  not wait for it.
- **Acceptance:** every Android ADR moves from "emulator-verified" to "verified on hardware"; a
  phone can pair, message, join channels, and configure a repeater.
- **Security:** confirm StrongBox and TEE key wrapping on hardware (ADR android/0002).

### M5: Mesh infrastructure (P4)

- **Objective:** repeaters and bridges an operator can deploy and watch.
- **Scope:** qualify the embedded bridge images; document bridge deployment (systemd unit,
  TLS pinning, rate limits); a health view in `umshctl` and the apps built on existing
  statistics; then a Signal Reports UEP for mesh-wide health, proposed upstream.
- **Dependencies:** M2.
- **Acceptance:** a two-mesh bridge deployment guide that a new operator can follow; health
  readouts for repeaters reachable by node management.
- **Protocol changes:** Signal Reports is a protocol addition and needs a UEP and upstream
  review before implementation.

### M6: UMSHNO distribution

- **Objective:** UMSHNO releases users can install.
- **Scope:** decide the reverse-DNS namespace and signing identities; new iOS bundle ID and
  Android application ID with UMSHNO names; identity export/import as the migration path from
  upstream apps; a release repository and web flasher; ThinkNode M6 in `scripts/release.py` and
  the board site; a vector master of the UMSHNO mark, app icons from it, and a 1-bit splash for
  the communicators.
- **Dependencies:** M1, M2, and M4 for Android.
- **Acceptance:** a tagged firmware release, a TestFlight build, and a Play internal-test build,
  each installable from UMSHNO's own channels.
- **Compatibility:** new app IDs are new apps. Moving over is by identity export, tested
  before release. Firmware updates keep every persisted setting.

### Research track (P5 and longer term)

These are not scheduled. Each needs a written design and, where it touches the wire, a UEP:

- **Offline delivery.** Store-and-forward on repeaters or designated nodes for absent
  recipients: storage limits, privacy (what a store node learns), spam resistance.
- **Adaptive routing.** Remaining routing reliability plan items (M3, M6–M10), evaluated
  in the M3 simulator before any firmware change.
- **Mapping and sensors.** Build on the existing GNSS, region database, and environmental
  sensor proposals.
- **Code health.** Split `umsh-ulcp-device/src/session.rs`, `umsh-mobile-core/src/ulcp.rs`, and
  `firmware/nrf52-tracker/src/main.rs` along existing seams, coordinated with upstream so the
  merge cost stays bounded.

## Recommended next milestone (after M1)

**M2: Hardware verification loop**, starting with the bench rig and the ThinkNode M6
checklist. The open S4 residual can only be closed with a firmware change to the pairing
window, and that change must be verified on real radios, which M2 provides. Run
dependency hardening (follow-up 1) at the same time: it needs no hardware.

## Recommended first engineering milestone (M0 assessment)

**M1: Trusted baseline**, starting with the Windows host build. Today the UMSHNO maintainer's
own machine cannot run `cargo test`, so every later milestone would depend on CI for
feedback. Next come the security fixes: S4 first, because a leaked admin key currently leads
to installing a device identity over BLE, then S1. After that come the dependency mirrors. This
milestone is small, has clear acceptance criteria, and needs no protocol changes. Everything
after it depends on it.

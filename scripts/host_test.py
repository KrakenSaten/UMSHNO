#!/usr/bin/env python3
"""Run the host workspace's tests the way `cargo test` would, on any host.

On Linux and macOS this is `cargo test`. On Windows it tests each default
member in a cargo invocation of its own.

The reason is feature unification. Building the default members together
turns on `umsh-hal/embassy` (the nRF52840 board support crates need it), so
every test binary in that build links `embassy-time`, whose driver only
firmware and simulator binaries install. The GNU linkers on Linux drop the
driver's unresolved symbols as dead code; MinGW's linker, writing PE images,
does not, and every such binary fails to link. Built one at a time, a crate
gets only the features it asks for.

Crates whose own tests link `embassy-time` without a driver cannot link on
Windows at all; they are listed in WINDOWS_SKIPPED and run on Linux CI.

Extra arguments go to every `cargo test` invocation, for example
`scripts/host_test.py --locked`.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Default members whose own tests link `embassy-time` without a driver.
WINDOWS_SKIPPED: dict[str, str] = {
    "umsh-ulcp-admin": "its tests link umsh-ulcp-runtime's device link, "
    "which brings embassy-time without a driver",
}

# MinGW keeps debug information inside the executable (MSVC writes it to a
# separate .pdb), and the full amount makes some test binaries too large
# for Windows to load (`chat_loop` reached 3.5 GB). Line tables keep
# backtraces readable.
WINDOWS_ENV = {"CARGO_PROFILE_DEV_DEBUG": "line-tables-only"}


def package_name(member: str) -> str:
    manifest = tomllib.loads((ROOT / member / "Cargo.toml").read_text(encoding="utf-8"))
    return manifest["package"]["name"]


def cargo_test(packages: list[str], extra: list[str], env: dict[str, str] | None = None) -> int:
    command = ["cargo", "test", *extra]
    for package in packages:
        command += ["-p", package]
    print("+", " ".join(command), flush=True)
    return subprocess.call(command, cwd=ROOT, env={**os.environ, **(env or {})})


def main() -> int:
    extra = sys.argv[1:]
    if sys.platform != "win32":
        return cargo_test([], extra)

    workspace = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
    failed: list[str] = []
    for member in workspace["workspace"]["default-members"]:
        name = package_name(member)
        if name in WINDOWS_SKIPPED:
            print(f"host_test.py: skipping {name} on Windows: {WINDOWS_SKIPPED[name]}")
            continue
        if cargo_test([name], extra, WINDOWS_ENV) != 0:
            failed.append(name)
    if failed:
        print(f"host_test.py: failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

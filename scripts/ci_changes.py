#!/usr/bin/env python3
"""Decide which CI jobs a change needs.

Reads the changed paths between two commits and prints, one per line,
`name=true|false` for each component CI can test, in the format
GitHub Actions takes for job outputs (`>> "$GITHUB_OUTPUT"`).

    scripts/ci_changes.py BASE HEAD     # what a pull request or push changed
    scripts/ci_changes.py --full        # everything (dispatch, tag, schedule)

A change to the CI configuration itself, or to this script, runs everything:
otherwise a broken job could only be noticed by a later change that happens
to select it. With no usable base (a new branch, a force push), everything
runs too.

Stdlib only, like the rest of scripts/.
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys

# Shared Rust: the protocol stack, the host tools, and the workspace itself.
RUST = [
    "Cargo.toml",
    "Cargo.lock",
    ".cargo/*",
    "rust-toolchain*",
    "crates/*",
    "umsh/*",
    "tools/umshctl/*",
    "tools/umsh-bridge/*",
    "tools/uniffi-bindgen/*",
    "tools/ulcp-web-debugger/*",
    "firmware/*",
    "fuzz/*",
    "scripts/host_test.py",
    "Makefile",
]

COMPONENTS: dict[str, list[str]] = {
    # fmt, host tests, clippy, the Windows host tests, fuzz build.
    "rust": RUST,
    # The Wireshark dissector's own suite.
    "dissector": ["dissectors/*"],
    # The protocol books.
    "docs": ["docs/protocol/*", "docs/protocol-legacy/*"],
    # nRF52840 firmware images: the shared crates they link and their tools.
    "nrf": [
        "Cargo.toml",
        "Cargo.lock",
        "crates/*",
        "umsh/*",
        "firmware/*",
        "Makefile",
        "scripts/mkuf2.py",
        "scripts/mkimage.py",
        "scripts/firmware_image.py",
        "scripts/stack_check.py",
        "scripts/crate_notices.py",
    ],
    # ESP32 firmware on a pull request only when its own tree changes; the
    # full matrix runs on dispatch, tags, and the weekly schedule.
    "esp32": ["firmware-esp32/*", "scripts/check_xtensa_stack.py"],
    # The Rust mobile core, built for iOS and tested on the host there.
    "ios": [
        "Cargo.toml",
        "Cargo.lock",
        "crates/*",
        "umsh/*",
        "packages/*",
        "apps/ios/*",
        "scripts/ios/*",
        "tools/uniffi-bindgen/*",
        "docs/hardware/boards.json",
    ],
    # The Rust mobile core cross-built for Android.
    "android_core": ["Cargo.toml", "Cargo.lock", "crates/*", "umsh/*"],
    # Upstream's Android application, kept building but not maintained.
    "android_app": ["apps/android/*", "docs/hardware/boards.json"],
    "regions": ["regions/*", "tools/regiondb-build/*", "crates/umsh-regiondb/*"],
}

# Changes that must run everything.
EVERYTHING = [".github/workflows/*", "scripts/ci_changes.py"]


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def select(paths: list[str]) -> dict[str, bool]:
    if any(matches(path, EVERYTHING) for path in paths):
        return {name: True for name in COMPONENTS}
    return {
        name: any(matches(path, patterns) for path in paths)
        for name, patterns in COMPONENTS.items()
    }


def changed(base: str, head: str) -> list[str] | None:
    """The paths that differ, or None when `base` cannot be compared."""
    if not base or set(base) == {"0"}:
        return None
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    args = sys.argv[1:]
    if args == ["--full"]:
        chosen = {name: True for name in COMPONENTS}
    elif len(args) == 2:
        paths = changed(*args)
        chosen = {name: True for name in COMPONENTS} if paths is None else select(paths)
        if paths is not None:
            print(f"{len(paths)} changed path(s)", file=sys.stderr)
    else:
        print(__doc__, file=sys.stderr)
        return 2
    for name, needed in chosen.items():
        print(f"{name}={'true' if needed else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

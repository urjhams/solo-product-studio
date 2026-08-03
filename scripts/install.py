#!/usr/bin/env python3
"""Install the portable product-studio skill into a supported host directory."""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "product-studio"
RESOURCE_DIRS = ("schemas", "templates", "pattern-library", "scripts")
TARGETS = {
    "codex": Path.home() / ".codex" / "skills",
    "claude-code": Path.home() / ".claude" / "skills",
    "opencode": Path.home() / ".config" / "opencode" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=sorted(TARGETS), required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--symlink", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    destination = (args.destination or TARGETS[args.target]).expanduser()
    installed = destination / "product-studio"
    if args.uninstall:
        if installed.is_symlink() or installed.is_file():
            installed.unlink()
        elif installed.is_dir():
            shutil.rmtree(installed)
        print(f"Removed {installed}")
        return 0
    if installed.exists() or installed.is_symlink():
        raise SystemExit(f"Refusing to overwrite existing {installed}; uninstall it first")
    destination.mkdir(parents=True, exist_ok=True)
    if args.symlink:
        installed.symlink_to(SOURCE, target_is_directory=True)
    else:
        shutil.copytree(SOURCE, installed)
    # SKILL.md refers to these resources by relative path. Package them beside
    # the skill so project-local and global installs are self-contained. A
    # symlink install links them instead of copying, so they cannot drift from
    # the repository root.
    for resource in RESOURCE_DIRS:
        target = SOURCE / resource if args.symlink else installed / resource
        if target.exists() or target.is_symlink():
            continue
        if args.symlink:
            target.symlink_to(Path("..") / ".." / resource, target_is_directory=True)
        else:
            shutil.copytree(ROOT / resource, target)
    print(f"Installed {installed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

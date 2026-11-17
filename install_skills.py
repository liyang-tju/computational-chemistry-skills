#!/usr/bin/env python3
"""Install independent skill copies without overwriting existing directories."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# Configuration
SOURCE_ROOT = Path(__file__).resolve().parent / "skills"
INSTALL_ROOT = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills"


def main() -> None:
    if not SOURCE_ROOT.is_dir():
        raise FileNotFoundError(f"Missing skill source directory: {SOURCE_ROOT}")
    sources = sorted(path for path in SOURCE_ROOT.iterdir() if path.is_dir())
    if not sources:
        raise ValueError(f"No skill directories found: {SOURCE_ROOT}")
    incomplete = [path.name for path in sources if not (path / "SKILL.md").is_file()]
    if incomplete:
        raise ValueError(f"Missing SKILL.md in: {', '.join(incomplete)}")

    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    installed = 0
    preserved = 0
    for source in sources:
        target = INSTALL_ROOT / source.name
        if target.exists() or target.is_symlink():
            preserved += 1
            print(f"PRESERVED {source.name}")
            continue
        shutil.copytree(source, target)
        installed += 1
        print(f"INSTALLED {source.name}")
    print(f"Installed: {installed}; preserved existing: {preserved}")


if __name__ == "__main__":
    main()

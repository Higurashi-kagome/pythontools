from __future__ import annotations

import os
import re
from pathlib import Path


HASH_PATTERN = re.compile(r"superpowers/([0-9a-f]{8})/skills")

def resolve_junction_target(path: Path) -> Path | None:
    try:
        target = os.readlink(path)
    except OSError:
        return None

    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = (path.parent / target_path).resolve()
    return target_path.resolve()


def ensure_junction(link_path: Path, target_path: Path) -> None:
    target_resolved = target_path.resolve()

    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink():
            existing_target = resolve_junction_target(link_path)
            if existing_target == target_resolved:
                return
            link_path.unlink()
        else:
            return

    if link_path.parent.exists() is False:
        link_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess_command = f'mklink /J "{link_path}" "{target_path}"'
    exit_code = os.system(f'cmd /c {subprocess_command}')
    if exit_code != 0:
        raise RuntimeError(f"failed to create junction: {link_path} -> {target_path}")


def iter_session_hashes(sessions_root: Path) -> set[str]:
    hashes: set[str] = set()
    if not sessions_root.exists():
        return hashes

    for session_file in sessions_root.rglob("*.jsonl"):
        try:
            text = session_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hashes.update(HASH_PATTERN.findall(text))
    return hashes


def main() -> int:
    codex_home = Path.home() / ".codex"
    cache_root = codex_home / "plugins" / "cache" / "openai-curated" / "superpowers"
    system_skills_root = codex_home / "skills" / ".system"
    stable_skill_link = system_skills_root / "superpowers"
    sessions_root = codex_home / "sessions"

    if not cache_root.exists():
        return 0

    plugin_dirs = [
        path for path in cache_root.iterdir()
        if path.is_dir() and ".bak-" not in path.name
    ]
    if not plugin_dirs:
        return 0

    latest_plugin_dir = max(plugin_dirs, key=lambda path: path.stat().st_mtime)
    target_skills_path = latest_plugin_dir / "skills"
    if not target_skills_path.exists():
        return 0

    system_skills_root.mkdir(parents=True, exist_ok=True)
    ensure_junction(stable_skill_link, target_skills_path)

    current_hash = latest_plugin_dir.name
    for hash_value in iter_session_hashes(sessions_root):
        if hash_value == current_hash:
            continue
        alias_path = cache_root / hash_value
        ensure_junction(alias_path, latest_plugin_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

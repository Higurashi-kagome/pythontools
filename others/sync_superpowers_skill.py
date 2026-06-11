from __future__ import annotations

import os
import re
import stat
from pathlib import Path


HASH_PATTERN = re.compile(r"superpowers/([0-9a-f]{8})/skills")
SKILL_SENTINEL = "using-superpowers"
LEGACY_SOURCE_MARKER = ".superpowers-source"


def is_reparse_point(path: Path) -> bool:
    try:
        attributes = os.lstat(path).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def resolve_existing_target(path: Path) -> Path | None:
    if not path.exists() and not path.is_symlink():
        return None

    try:
        return path.resolve()
    except OSError:
        return None


def remove_existing_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return

    if path.is_symlink() or is_reparse_point(path):
        os.rmdir(path)
        return

    if path.is_dir():
        raise RuntimeError(f"refusing to replace real directory: {path}")

    path.unlink()


def ensure_junction(link_path: Path, target_path: Path) -> None:
    target_resolved = target_path.resolve()
    existing_target = resolve_existing_target(link_path)
    if existing_target == target_resolved:
        return

    if existing_target is not None:
        remove_existing_path(link_path)

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


def score_plugin_dir(path: Path) -> tuple[int, int, float, str]:
    skills_path = path / "skills"
    sentinel_path = skills_path / SKILL_SENTINEL
    return (
        1 if sentinel_path.exists() else 0,
        1 if skills_path.exists() else 0,
        path.stat().st_mtime,
        path.name,
    )


def choose_plugin_dir(plugin_dirs: list[Path]) -> Path:
    real_plugin_dirs = [path for path in plugin_dirs if not is_reparse_point(path)]
    candidates = real_plugin_dirs or plugin_dirs
    return max(candidates, key=score_plugin_dir)


def is_legacy_superpowers_skill_dir(path: Path, cache_root: Path) -> bool:
    marker_path = path / LEGACY_SOURCE_MARKER
    if not marker_path.exists():
        return False

    try:
        source_text = marker_path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return False

    if not source_text:
        return False

    normalized_source = Path(source_text)
    normalized_cache_root = cache_root.resolve()
    try:
        normalized_source.relative_to(normalized_cache_root)
    except ValueError:
        return False

    return True


def cleanup_legacy_skill_mirrors(system_skills_root: Path, cache_root: Path) -> None:
    if not system_skills_root.exists():
        return

    for skill_dir in system_skills_root.iterdir():
        if not skill_dir.is_dir():
            continue
        if not is_legacy_superpowers_skill_dir(skill_dir, cache_root):
            continue

        for child in skill_dir.iterdir():
            if child.is_dir() and not child.is_symlink():
                for nested in child.rglob("*"):
                    if nested.is_file() or nested.is_symlink():
                        nested.unlink()
                for nested_dir in sorted(
                    (p for p in child.rglob("*") if p.is_dir()),
                    reverse=True,
                ):
                    nested_dir.rmdir()
                child.rmdir()
                continue

            if child.is_file() or child.is_symlink():
                child.unlink()

        skill_dir.rmdir()


def main() -> int:
    codex_home = Path.home() / ".codex"
    cache_root = codex_home / "plugins" / "cache" / "openai-curated" / "superpowers"
    sessions_root = codex_home / "sessions"
    system_skills_root = codex_home / "skills" / ".system"

    if not cache_root.exists():
        return 0

    plugin_dirs = [
        path for path in cache_root.iterdir()
        if path.is_dir() and ".bak-" not in path.name
    ]
    if not plugin_dirs:
        return 0

    latest_plugin_dir = choose_plugin_dir(plugin_dirs)
    target_skills_path = latest_plugin_dir / "skills"
    if not target_skills_path.exists():
        return 0

    cleanup_legacy_skill_mirrors(system_skills_root, cache_root)

    current_hash = latest_plugin_dir.name
    for hash_value in iter_session_hashes(sessions_root):
        if hash_value == current_hash:
            continue
        alias_path = cache_root / hash_value
        ensure_junction(alias_path, latest_plugin_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

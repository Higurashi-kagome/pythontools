from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path


HASH_PATTERN = re.compile(r"superpowers/([0-9a-f]{8})/skills")
SKILL_SENTINEL = "using-superpowers"
LEGACY_SOURCE_MARKER = ".superpowers-source"
INDEX_FILENAME = "superpowers-session-hashes.json"


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


def load_session_hash_index(index_path: Path) -> dict[str, dict[str, object]]:
    # 索引文件损坏时直接回退到全量重建，避免影响 SessionStart。
    if not index_path.exists():
        return {}

    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    files = payload.get("files")
    if not isinstance(files, dict):
        return {}

    sanitized_files: dict[str, dict[str, object]] = {}
    for relative_path, record in files.items():
        if not isinstance(relative_path, str) or not isinstance(record, dict):
            continue

        hashes = record.get("hashes")
        if not isinstance(hashes, list) or not hashes:
            continue

        sanitized_files[relative_path] = record

    return sanitized_files


def save_session_hash_index(index_path: Path, files_index: dict[str, dict[str, object]]) -> None:
    if not index_path.parent.exists():
        index_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"files": files_index}
    index_path.write_text(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def extract_hashes_from_session_file(session_file: Path) -> set[str]:
    hashes: set[str] = set()
    try:
        # 按行扫描，避免把大型 jsonl 一次性读入内存。
        with session_file.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                hashes.update(HASH_PATTERN.findall(line))
    except OSError:
        return set()
    return hashes


def build_session_file_record(session_file: Path, sessions_root: Path) -> dict[str, object] | None:
    try:
        stat_result = session_file.stat()
    except OSError:
        return None

    relative_path = session_file.relative_to(sessions_root).as_posix()
    hashes = sorted(extract_hashes_from_session_file(session_file))
    return {
        "relative_path": relative_path,
        "mtime_ns": stat_result.st_mtime_ns,
        "size": stat_result.st_size,
        "hashes": hashes,
    }


def build_session_file_scan_key(session_file: Path, sessions_root: Path) -> dict[str, object] | None:
    try:
        stat_result = session_file.stat()
    except OSError:
        return None

    return {
        "relative_path": session_file.relative_to(sessions_root).as_posix(),
        "mtime_ns": stat_result.st_mtime_ns,
        "size": stat_result.st_size,
    }


def collect_session_hashes_incremental(sessions_root: Path, index_root: Path) -> set[str]:
    hashes: set[str] = set()
    if not sessions_root.exists():
        return hashes

    index_path = index_root / INDEX_FILENAME
    previous_index = load_session_hash_index(index_path)
    next_index: dict[str, dict[str, object]] = {}

    for session_file in sessions_root.rglob("*.jsonl"):
        scan_key = build_session_file_scan_key(session_file, sessions_root)
        if scan_key is None:
            continue

        relative_path = str(scan_key["relative_path"])
        previous_record = previous_index.get(relative_path)

        if (
            previous_record
            and previous_record.get("mtime_ns") == scan_key["mtime_ns"]
            and previous_record.get("size") == scan_key["size"]
            and isinstance(previous_record.get("hashes"), list)
            and previous_record.get("hashes")
        ):
            # 未变化的历史会话直接复用上次提取结果，避免每次启动全量重扫。
            hashes.update(str(hash_value) for hash_value in previous_record["hashes"])
            next_index[relative_path] = previous_record
            continue

        current_record = build_session_file_record(session_file, sessions_root)
        if current_record is None:
            continue

        current_hashes = current_record.get("hashes", [])
        hashes.update(str(hash_value) for hash_value in current_hashes)
        if current_hashes:
            next_index[relative_path] = current_record

    save_session_hash_index(index_path, next_index)
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
    state_root = codex_home / "state"

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
    # 历史 session 里可能固化了旧 hash 路径，这里继续补兼容 Junction。
    for hash_value in collect_session_hashes_incremental(sessions_root, state_root):
        if hash_value == current_hash:
            continue
        alias_path = cache_root / hash_value
        ensure_junction(alias_path, latest_plugin_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

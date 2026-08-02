import argparse
import shutil
import subprocess
import sys
from pathlib import Path, PureWindowsPath


def find_7zip() -> str:
    """查找 7-Zip 命令行程序并返回可执行文件路径。"""
    for command in ('7z', '7zz', '7z.exe', '7zz.exe'):
        executable = shutil.which(command)
        if executable:
            return executable

    for executable in (
        Path(r'C:\Program Files\7-Zip\7z.exe'),
        Path(r'C:\Program Files (x86)\7-Zip\7z.exe'),
    ):
        if executable.is_file():
            return str(executable)

    raise FileNotFoundError('未找到 7z.exe，请将 7-Zip 加入 PATH 或安装到默认目录。')


def _run_7zip(executable: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """执行 7-Zip 命令并返回结果。"""
    return subprocess.run(
        [executable, *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
    )


def _result_error(result: subprocess.CompletedProcess[str]) -> str:
    """提取 7-Zip 命令的错误信息。"""
    return (result.stderr or result.stdout).strip() or f'退出码：{result.returncode}'


def _list_archive_entries(archive_path: Path, executable: str) -> list[tuple[str, bool]]:
    """使用 7-Zip 列出压缩包条目，返回条目路径及是否为目录。"""
    result = _run_7zip(executable, ['l', '-slt', '-ba', '-sccUTF-8', str(archive_path)])
    if result.returncode != 0:
        raise RuntimeError(f'读取压缩包内容失败：{_result_error(result)}')

    entries: list[tuple[str, bool]] = []
    entry_path: str | None = None
    is_directory = False
    for line in result.stdout.splitlines():
        if line.startswith('Path = '):
            if entry_path is not None:
                entries.append((entry_path, is_directory))
            entry_path = line[7:]
            is_directory = False
        elif line.startswith('Folder = '):
            is_directory = line[9:] == '+'

    if entry_path is not None:
        entries.append((entry_path, is_directory))
    return entries


def _safe_entry_parts(entry_path: str) -> tuple[str, ...]:
    """校验压缩包内路径并拆分为 Windows 路径片段。"""
    normalized_path = PureWindowsPath(entry_path.replace('/', '\\'))
    if normalized_path.drive or normalized_path.root or '..' in normalized_path.parts:
        raise ValueError(f'压缩包包含不安全路径：{entry_path}')

    parts = tuple(part for part in normalized_path.parts if part not in ('.', '\\'))
    if not parts:
        raise ValueError(f'压缩包包含无效路径：{entry_path}')
    return parts


def _prepare_entries(
    entries: list[tuple[str, bool]],
) -> list[tuple[tuple[str, ...], bool]]:
    """校验并规范化 7-Zip 返回的压缩包条目。"""
    prepared_entries = [(_safe_entry_parts(path), is_directory) for path, is_directory in entries]
    if not prepared_entries:
        raise ValueError('压缩包中没有可解压的内容。')
    return prepared_entries


def _choose_destination(
    archive_path: Path,
    entries: list[tuple[tuple[str, ...], bool]],
) -> Path:
    """根据压缩包顶层结构选择解压目标目录。"""
    top_level_names = {parts[0].casefold() for parts, _ in entries}
    has_root_file = any(len(parts) == 1 and not is_directory for parts, is_directory in entries)
    if len(top_level_names) == 1 and not has_root_file:
        return archive_path.parent
    return archive_path.parent / archive_path.stem


def extract_archive(src_file: str | Path) -> Path:
    """根据压缩包结构调用 7-Zip 解压，并返回实际解压目录。

    Args:
        src_file: 压缩包路径

    Returns:
        实际解压目录路径
    """
    archive_path = Path(src_file).expanduser().resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(f'压缩包不存在：{archive_path}')

    executable = find_7zip()
    entries = _prepare_entries(_list_archive_entries(archive_path, executable))
    destination = _choose_destination(archive_path, entries)

    if destination != archive_path.parent and destination.exists():
        raise FileExistsError(f'解压目标已存在：{destination}')

    for parts, _ in entries:
        existing_path = destination.joinpath(*parts)
        if existing_path.exists():
            raise FileExistsError(f'解压后路径已存在：{existing_path}')

    result = _run_7zip(
        executable,
        ['x', '-y', '-aoa', '-sccUTF-8', f'-o{destination}', str(archive_path)],
    )
    if result.returncode != 0:
        raise RuntimeError(f'解压失败：{_result_error(result)}')
    return destination


def main(argv: list[str] | None = None) -> int:
    """解析命令行参数并执行解压。

    Args:
        argv: 命令行参数；为空时使用系统参数

    Returns:
        进程退出码，0 表示成功
    """
    parser = argparse.ArgumentParser(description='根据压缩包顶层结构调用 7-Zip 自动解压')
    parser.add_argument('archive', type=Path, help='压缩包路径')
    args = parser.parse_args(argv)

    try:
        destination = extract_archive(args.archive)
    except (FileNotFoundError, FileExistsError, OSError, RuntimeError, ValueError) as error:
        print(f'解压失败：{error}', file=sys.stderr)
        return 1

    print(f'解压完成：{destination}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

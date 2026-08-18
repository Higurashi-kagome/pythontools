import argparse
import os
from pathlib import Path
import subprocess
import zipfile


def run_git(repo_path: Path, *args: str) -> bytes:
    """在指定仓库中执行 Git 命令。

    :param repo_path: Git 仓库目录
    :param args: Git 子命令及其参数
    :return: Git 标准输出的字节内容
    """
    try:
        result = subprocess.run(
            ['git', '-c', 'core.quotePath=false', '-C', os.fspath(repo_path), *args],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError('未找到 git 命令，请先安装 Git 并将其加入 PATH') from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode(errors='replace').strip()
        raise RuntimeError(message or '执行 Git 命令失败') from exc

    return result.stdout


def get_repo_root(repo_path: Path) -> Path:
    """获取指定路径所属 Git 仓库的根目录。

    :param repo_path: Git 仓库目录或其子目录
    :return: Git 仓库根目录
    """
    output = run_git(repo_path, 'rev-parse', '--show-toplevel')
    return Path(os.fsdecode(output).strip()).resolve()


def get_untracked_files(repo_root: Path) -> list[Path]:
    """获取仓库中未被 Git 跟踪且未被忽略的文件路径。

    :param repo_root: Git 仓库根目录
    :return: 相对于仓库根目录的文件路径列表
    """
    output = run_git(repo_root, 'ls-files', '--others', '--exclude-standard', '-z')
    paths = []

    for item in output.split(b'\0'):
        if not item:
            continue

        relative_path = Path(os.fsdecode(item))
        if relative_path.is_absolute() or '..' in relative_path.parts:
            raise RuntimeError(f'Git 返回了不安全的文件路径: {relative_path}')
        paths.append(relative_path)

    return paths


def create_archive(repo_root: Path, output_path: Path) -> int:
    """将仓库中的未跟踪非忽略文件打包为 ZIP。

    :param repo_root: Git 仓库根目录
    :param output_path: 输出 ZIP 的完整路径
    :return: 打包的文件数量
    """
    if output_path.exists():
        raise FileExistsError(f'输出文件已存在，已取消打包: {output_path}')

    untracked_files = get_untracked_files(repo_root)
    archive_created = False

    try:
        # 使用独占创建，避免在检查后覆盖同名文件
        with output_path.open('xb') as output_file:
            archive_created = True
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                for relative_path in untracked_files:
                    source_path = repo_root / relative_path
                    if not source_path.is_file():
                        raise FileNotFoundError(f'待打包文件不存在或不是普通文件: {source_path}')
                    archive.write(source_path, relative_path.as_posix())
    except Exception:
        if archive_created:
            output_path.unlink(missing_ok=True)
        raise

    return len(untracked_files)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    :return: 解析后的命令行参数
    """
    parser = argparse.ArgumentParser(
        description='导出 Git 仓库中未纳入版本管理且未被忽略的文件',
    )
    parser.add_argument(
        'repo_path',
        type=Path,
        nargs='?',
        default=Path.cwd(),
        help='Git 仓库路径，默认当前目录',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='输出 ZIP 路径，默认在仓库根目录创建"仓库名-untracked.zip"',
    )
    return parser.parse_args()


def main() -> None:
    """执行未跟踪文件导出流程。"""
    args = parse_args()
    repo_path = args.repo_path.expanduser().resolve(strict=False)

    try:
        repo_root = get_repo_root(repo_path)
        output_path = args.output
        if output_path is None:
            output_path = repo_root / f'{repo_root.name}-untracked.zip'
        else:
            output_path = output_path.expanduser().resolve(strict=False)

        if output_path.suffix.lower() != '.zip':
            raise ValueError(f'输出文件必须为 .zip 格式: {output_path}')
        if not output_path.parent.is_dir():
            raise NotADirectoryError(f'输出目录不存在: {output_path.parent}')

        file_count = create_archive(repo_root, output_path)
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f'错误: {exc}') from exc

    print(f'打包完成，共 {file_count} 个文件: {output_path}')


if __name__ == '__main__':
    main()

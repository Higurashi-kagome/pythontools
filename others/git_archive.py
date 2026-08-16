import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


def find_git_repos(project_root: Path) -> list[Path]:
    repos = []

    if (project_root / '.git').exists():
        repos.append(project_root)

    for git_dir in project_root.rglob('.git'):
        if git_dir.parent == project_root:
            continue
        repos.append(git_dir.parent)

    return sorted(set(repos), key=lambda p: (len(p.parts), str(p)))


def git_ls_files(repo: Path) -> list[Path]:
    result = subprocess.run(
        ['git', '-C', str(repo), 'ls-files', '-z'],
        check=True,
        capture_output=True,
    )
    return [Path(item) for item in result.stdout.decode('utf-8').split('\0') if item]


def copy_git_files(repo: Path, project_root: Path, stage_dir: Path) -> None:
    repo_rel = repo.relative_to(project_root)
    target_base = stage_dir / repo_rel

    for rel_path in git_ls_files(repo):
        src = repo / rel_path
        dst = target_base / rel_path
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def copy_git_metadata(repo: Path, project_root: Path, stage_dir: Path) -> None:
    """复制仓库的 Git 元数据。

    :param repo: Git 仓库目录
    :param project_root: 打包根目录
    :param stage_dir: 临时打包目录
    """
    git_path = repo / '.git'
    target_path = stage_dir / repo.relative_to(project_root) / '.git'
    if git_path.is_dir():
        shutil.copytree(git_path, target_path, copy_function=shutil.copy2)
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(git_path, target_path)


def zip_dir(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob('*'):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f'{label}不存在: {path}')
    if not path.is_dir():
        raise NotADirectoryError(f'{label}不是目录: {path}')


def archive_git_sources(project_root: Path, zip_path: Path, include_git: bool = False) -> Path:
    """将 Git 已跟踪文件打包为 ZIP 压缩包。

    :param project_root: Git 仓库根目录
    :param zip_path: 输出 ZIP 压缩包路径
    :param include_git: 是否包含各仓库的 .git 元数据
    :return: 已生成的 ZIP 压缩包路径
    """
    ensure_directory(project_root, '项目目录')

    repos = find_git_repos(project_root)
    if not repos:
        raise RuntimeError(f'未在项目目录中找到 Git 仓库: {project_root}')

    with tempfile.TemporaryDirectory(prefix='git-archive-') as temp_dir:
        stage_dir = Path(temp_dir)
        for repo in repos:
            copy_git_files(repo, project_root, stage_dir)
            if include_git:
                copy_git_metadata(repo, project_root, stage_dir)

        if zip_path.exists():
            zip_path.unlink()

        zip_dir(stage_dir, zip_path)
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description='打包 Git 仓库中已跟踪的文件')
    parser.add_argument('project_root', type=Path, help='Git 仓库路径')
    parser.add_argument('zip_path', type=Path, help='输出 zip 压缩包路径')
    parser.add_argument(
        '--include-git',
        action='store_true',
        help='在压缩包中包含 .git 文件夹或文件',
    )
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve(strict=False)
    zip_path = args.zip_path.expanduser().resolve(strict=False)
    if zip_path.suffix.lower() != '.zip':
        parser.error('输出压缩包必须是 .zip 文件')

    zip_path = archive_git_sources(project_root, zip_path, args.include_git)
    print(f'打包完成: {zip_path}')


if __name__ == '__main__':
    main()

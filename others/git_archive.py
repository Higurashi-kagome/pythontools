import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


@dataclass(frozen=True)
class ArchiveSource:
    """描述一个需要写入压缩包的 Git 工作目录。"""

    repo: Path
    archive_root: Path


def find_git_repos(project_root: Path) -> list[Path]:
    """递归查找项目目录中的 Git 仓库。

    :param project_root: 项目扫描根目录
    :return: 按目录深度和路径排序后的 Git 仓库目录列表
    """
    repos = []

    if (project_root / '.git').exists():
        repos.append(project_root)

    for git_dir in project_root.rglob('.git'):
        if git_dir.parent == project_root:
            continue
        repos.append(git_dir.parent)

    return sorted(set(repos), key=lambda p: (len(p.parts), str(p)))


def run_git(repo: Path, *args: str) -> bytes:
    """在指定仓库中执行 Git 命令并返回标准输出。

    :param repo: Git 仓库或 worktree 目录
    :param args: Git 子命令及参数
    :return: Git 标准输出的字节内容
    """
    result = subprocess.run(
        ['git', '-c', 'core.quotePath=false', '-C', os.fspath(repo), *args],
        check=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,
    )
    return result.stdout


def parse_git_paths(output: bytes, validate: bool = False) -> list[Path]:
    """解析 Git 以 NUL 分隔返回的相对路径。

    :param output: Git 命令的标准输出
    :param validate: 是否校验路径不能越出仓库根目录
    :return: 相对路径列表
    """
    paths = []
    for item in output.split(b'\0'):
        if not item:
            continue

        relative_path = Path(os.fsdecode(item))
        if validate and (relative_path.is_absolute() or '..' in relative_path.parts):
            raise RuntimeError(f'Git 返回了不安全的文件路径: {relative_path}')
        paths.append(relative_path)
    return paths


def git_ls_files(repo: Path) -> list[Path]:
    """获取仓库中已跟踪的文件路径。

    :param repo: Git 仓库或 worktree 目录
    :return: 相对于仓库根目录的已跟踪文件路径列表
    """
    return parse_git_paths(run_git(repo, 'ls-files', '-z'))


def git_ls_untracked_files(repo: Path) -> list[Path]:
    """获取仓库中未跟踪且未被忽略的文件路径。

    :param repo: Git 仓库或 worktree 目录
    :return: 相对于仓库根目录的未跟踪文件路径列表
    """
    return parse_git_paths(
        run_git(repo, 'ls-files', '--others', '--exclude-standard', '-z'),
        validate=True,
    )


def resolve_git_path(repo: Path, git_path: str) -> Path:
    """将 Git 返回的目录路径解析为绝对路径。

    :param repo: Git 仓库或 worktree 目录
    :param git_path: Git 返回的目录路径
    :return: 解析后的绝对路径
    """
    path = Path(git_path)
    if not path.is_absolute():
        path = repo / path
    return path.resolve(strict=False)


def is_linked_worktree(repo: Path) -> bool:
    """判断目录是否为 Git linked worktree。

    :param repo: 待判断的 Git 工作目录
    :return: 是否为 linked worktree
    """
    git_file = repo / '.git'
    if not git_file.is_file():
        return False

    output = run_git(repo, 'rev-parse', '--git-dir', '--git-common-dir')
    git_dirs = output.decode('utf-8').splitlines()
    if len(git_dirs) < 2:
        return False

    return resolve_git_path(repo, git_dirs[0]) != resolve_git_path(repo, git_dirs[1])


def find_linked_worktrees(repo: Path) -> list[tuple[Path, Path]]:
    """查找仓库登记且当前仍存在的 linked worktree。

    :param repo: 主仓库或其 linked worktree 目录
    :return: linked worktree 目录及其主仓库目录
    """
    common_dir = run_git(repo, 'rev-parse', '--git-common-dir').decode('utf-8').strip()
    main_repo = resolve_git_path(repo, common_dir).parent
    output = run_git(repo, 'worktree', 'list', '--porcelain')
    listed_worktrees = []
    for line in output.decode('utf-8').splitlines():
        if not line.startswith('worktree '):
            continue

        worktree = Path(line.removeprefix('worktree ')).resolve(strict=False)
        if worktree.is_dir():
            listed_worktrees.append(worktree)

    worktrees = []
    for worktree in listed_worktrees:
        if worktree == repo.resolve(strict=False) or worktree == main_repo:
            continue
        if is_linked_worktree(worktree):
            worktrees.append((worktree, main_repo))

    return sorted(set(worktrees), key=lambda item: str(item[0]).casefold())


def allocate_archive_name(preferred: str, used_names: set[str]) -> str:
    """为外部 worktree 分配不重复的压缩包目录名称。

    :param preferred: 优先使用的名称
    :param used_names: 已经使用的名称集合
    :return: 可用的唯一名称
    """
    preferred = preferred or 'item'
    candidate = preferred
    suffix = 2
    used_keys = {name.casefold() for name in used_names}
    while candidate.casefold() in used_keys:
        candidate = f'{preferred}-{suffix}'
        suffix += 1
    used_names.add(candidate)
    return candidate


def find_archive_sources(project_root: Path, include_git: bool) -> list[ArchiveSource]:
    """收集需要打包的仓库、项目内 worktree 和外部 worktree。

    :param project_root: 项目扫描根目录
    :param include_git: 是否包含 Git 元数据和 linked worktree
    :return: 待打包的工作目录及其压缩包内根路径
    """
    project_root = project_root.resolve(strict=False)
    repos = [repo.resolve(strict=False) for repo in find_git_repos(project_root)]
    if not repos:
        raise RuntimeError(f'未在项目目录中找到 Git 仓库: {project_root}')

    sources: dict[Path, ArchiveSource] = {}
    linked_flags = {repo: is_linked_worktree(repo) for repo in repos}

    for repo in repos:
        if repo != project_root and linked_flags[repo] and not include_git:
            continue
        sources[repo] = ArchiveSource(
            repo=repo,
            archive_root=repo.relative_to(project_root),
        )

    if not include_git:
        return list(sources.values())

    external_worktrees: dict[Path, Path] = {}
    for repo in repos:
        for worktree, main_repo in find_linked_worktrees(repo):
            if worktree in sources:
                continue
            if worktree.is_relative_to(project_root):
                sources[worktree] = ArchiveSource(
                    repo=worktree,
                    archive_root=worktree.relative_to(project_root),
                )
                continue
            external_worktrees.setdefault(worktree, main_repo)

    repo_names: dict[Path, str] = {}
    used_repo_names: set[str] = set()
    worktree_names: dict[Path, set[str]] = {}
    for worktree, repo in sorted(
        external_worktrees.items(),
        key=lambda item: (str(item[1]).casefold(), str(item[0]).casefold()),
    ):
        repo_name = repo_names.get(repo)
        if repo_name is None:
            repo_name = allocate_archive_name(repo.name, used_repo_names)
            repo_names[repo] = repo_name

        used_worktree_names = worktree_names.setdefault(repo, set())
        worktree_name = allocate_archive_name(worktree.name, used_worktree_names)
        sources[worktree] = ArchiveSource(
            repo=worktree,
            archive_root=Path('__worktrees__') / repo_name / worktree_name,
        )

    return list(sources.values())


def copy_file_list(
    repo: Path,
    archive_root: Path,
    relative_paths: list[Path],
    stage_dir: Path,
    excluded_path: Path | None = None,
    excluded_roots: tuple[Path, ...] = (),
    fail_if_missing: bool = False,
) -> None:
    """将指定文件列表复制到临时打包目录。

    :param repo: 文件所属的 Git 工作目录
    :param archive_root: 文件在压缩包中的根目录
    :param relative_paths: 相对于工作目录的文件路径列表
    :param stage_dir: 临时打包目录
    :param excluded_path: 需要排除的绝对路径，通常是输出压缩包
    :param excluded_roots: 需要排除的仓库目录
    :param fail_if_missing: 文件不存在时是否抛出异常
    """
    target_base = stage_dir / archive_root
    for relative_path in relative_paths:
        source_path = repo / relative_path
        resolved_source_path = source_path.resolve(strict=False)
        if excluded_path and resolved_source_path == excluded_path:
            continue
        if any(
            resolved_source_path == root or root in resolved_source_path.parents
            for root in excluded_roots
        ):
            continue

        if not source_path.is_file():
            if fail_if_missing:
                raise FileNotFoundError(f'待打包文件不存在或不是普通文件: {source_path}')
            continue

        target_path = target_base / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def copy_git_files(
    repo: Path,
    project_root: Path,
    stage_dir: Path,
    excluded_path: Path | None = None,
) -> None:
    """复制仓库中已跟踪的文件。

    :param repo: Git 仓库目录
    :param project_root: 打包根目录
    :param stage_dir: 临时打包目录
    :param excluded_path: 需要排除的绝对路径
    """
    copy_file_list(
        repo,
        repo.relative_to(project_root),
        git_ls_files(repo),
        stage_dir,
        excluded_path=excluded_path,
    )


def copy_untracked_files(
    repo: Path,
    archive_root: Path,
    stage_dir: Path,
    excluded_path: Path | None = None,
    excluded_roots: tuple[Path, ...] = (),
) -> None:
    """复制仓库中未跟踪且未被忽略的文件。

    :param repo: Git 仓库或 worktree 目录
    :param archive_root: 文件在压缩包中的根目录
    :param stage_dir: 临时打包目录
    :param excluded_path: 需要排除的绝对路径
    :param excluded_roots: 需要排除的仓库目录
    """
    copy_file_list(
        repo,
        archive_root,
        git_ls_untracked_files(repo),
        stage_dir,
        excluded_path=excluded_path,
        excluded_roots=excluded_roots,
        fail_if_missing=True,
    )


def copy_git_metadata_to(repo: Path, archive_root: Path, stage_dir: Path) -> None:
    """复制仓库的 Git 元数据。

    :param repo: Git 仓库目录
    :param archive_root: 元数据在压缩包中的根目录
    :param stage_dir: 临时打包目录
    """
    git_path = repo / '.git'
    target_path = stage_dir / archive_root / '.git'
    if git_path.is_dir():
        shutil.copytree(git_path, target_path, copy_function=shutil.copy2)
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(git_path, target_path)


def copy_git_metadata(repo: Path, project_root: Path, stage_dir: Path) -> None:
    """复制仓库的 Git 元数据。

    :param repo: Git 仓库目录
    :param project_root: 打包根目录
    :param stage_dir: 临时打包目录
    """
    copy_git_metadata_to(repo, repo.relative_to(project_root), stage_dir)


def zip_dir(source_dir: Path, zip_path: Path) -> None:
    """将临时打包目录压缩为 ZIP 文件。

    :param source_dir: 待压缩的目录
    :param zip_path: 输出 ZIP 文件路径
    """
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob('*'):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir).as_posix())


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f'{label}不存在: {path}')
    if not path.is_dir():
        raise NotADirectoryError(f'{label}不是目录: {path}')


def resolve_output_path(project_root: Path, zip_path: Path | None = None) -> Path:
    """解析输出压缩包路径，必要时为默认路径分配序号。

    :param project_root: Git 仓库或项目扫描根目录
    :param zip_path: 用户指定的输出路径，省略时自动生成
    :return: 最终输出 ZIP 文件路径
    """
    if zip_path is not None:
        return zip_path.resolve(strict=False)

    archive_name = project_root.name
    output_path = project_root.parent / f'{archive_name}.zip'
    suffix = 2
    while output_path.exists():
        output_path = project_root.parent / f'{archive_name}-{suffix}.zip'
        suffix += 1
    return output_path


def archive_git_sources(
    project_root: Path,
    zip_path: Path | None = None,
    include_git: bool = True,
    include_untracked: bool = False,
) -> Path:
    """将 Git 仓库文件打包为 ZIP 压缩包。

    :param project_root: Git 仓库或项目扫描根目录
    :param zip_path: 输出 ZIP 压缩包路径，省略时在项目目录同级自动生成
    :param include_git: 是否包含各仓库的 .git 元数据，默认包含
    :param include_untracked: 是否包含未跟踪且未被忽略的文件，默认不包含
    :return: 已生成的 ZIP 压缩包路径
    """
    ensure_directory(project_root, '项目目录')

    project_root = project_root.resolve(strict=False)
    zip_path = resolve_output_path(project_root, zip_path)
    sources = find_archive_sources(project_root, include_git)
    all_repo_roots = tuple(
        repo.resolve(strict=False)
        for repo in find_git_repos(project_root)
        if repo.resolve(strict=False) != project_root
    )

    with tempfile.TemporaryDirectory(prefix='git-archive-') as temp_dir:
        stage_dir = Path(temp_dir)
        for source in sources:
            excluded_roots = tuple(
                repo_root
                for repo_root in all_repo_roots
                if repo_root != source.repo and repo_root.is_relative_to(source.repo)
            )
            copy_file_list(
                source.repo,
                source.archive_root,
                git_ls_files(source.repo),
                stage_dir,
                excluded_path=zip_path,
            )
            if include_untracked:
                copy_untracked_files(
                    source.repo,
                    source.archive_root,
                    stage_dir,
                    excluded_path=zip_path,
                    excluded_roots=excluded_roots,
                )
            if include_git:
                copy_git_metadata_to(source.repo, source.archive_root, stage_dir)

        if zip_path.exists():
            zip_path.unlink()

        zip_dir(stage_dir, zip_path)
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description='打包 Git 仓库文件')
    parser.add_argument('project_root', type=Path, help='Git 仓库路径')
    parser.add_argument(
        'zip_path',
        type=Path,
        nargs='?',
        help='输出 zip 压缩包路径，省略时在仓库同级自动生成',
    )
    parser.add_argument(
        '--no-git',
        dest='include_git',
        action='store_false',
        help='不包含 .git 元数据，也不打包关联的 linked worktree',
    )
    parser.add_argument(
        '--include-untracked',
        action='store_true',
        help='同时包含未跟踪且未被忽略的文件（默认不包含）',
    )
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve(strict=False)
    zip_path = args.zip_path.expanduser().resolve(strict=False) if args.zip_path else None
    if zip_path is not None and zip_path.suffix.lower() != '.zip':
        parser.error('输出压缩包必须是 .zip 文件')

    zip_path = archive_git_sources(
        project_root,
        zip_path,
        args.include_git,
        args.include_untracked,
    )
    print(f'打包完成: {zip_path}')


if __name__ == '__main__':
    main()

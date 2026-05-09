from pathlib import Path
import shutil
import subprocess
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


def zip_dir(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob('*'):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def prompt_path(message: str, default: Path | None = None) -> Path:
    while True:
        prompt = f'{message} [{default}]: ' if default else f'{message}: '
        raw = input(prompt).strip().strip('"')
        if not raw:
            if default is not None:
                return default
            print('路径不能为空，请重新输入。')
            continue
        return Path(raw).expanduser().resolve(strict=False)


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f'{label}不存在: {path}')
    if not path.is_dir():
        raise NotADirectoryError(f'{label}不是目录: {path}')


def ensure_safe_to_delete(target: Path, work_dir: Path) -> None:
    if target == work_dir or work_dir in target.parents:
        return
    raise ValueError(f'拒绝删除非工作目录下的路径: {target}')


def prompt_existing_directory(message: str, default: Path | None = None) -> Path:
    while True:
        path = prompt_path(message, default)
        try:
            ensure_directory(path, '目录')
            return path
        except (FileNotFoundError, NotADirectoryError) as exc:
            print(f'{exc}，请重新输入。')


def prompt_zip_path(work_dir: Path, default_name: str) -> Path:
    while True:
        zip_path = prompt_path('请输入 zip 输出文件路径', work_dir / default_name)
        if zip_path.suffix.lower() != '.zip':
            print('输出文件必须是.zip，请重新输入。')
            continue
        return zip_path


def archive_git_sources(project_root: Path, work_dir: Path, zip_path: Path) -> Path:
    ensure_directory(project_root, '项目目录')
    work_dir.mkdir(parents=True, exist_ok=True)

    stage_dir = work_dir / 'stage'

    if stage_dir.exists():
        ensure_safe_to_delete(stage_dir, work_dir)
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)

    repos = find_git_repos(project_root)
    if not repos:
        raise RuntimeError(f'未在项目目录中找到 Git 仓库: {project_root}')

    for repo in repos:
        copy_git_files(repo, project_root, stage_dir)

    if zip_path.exists():
        zip_path.unlink()

    zip_dir(stage_dir, zip_path)
    return zip_path


def main() -> None:
    default_project_root = Path.cwd()
    project_root = prompt_existing_directory('请输入项目根目录路径', default_project_root)
    default_work_dir = project_root.parent / f'{project_root.name}-archive'
    work_dir = prompt_path('请输入工作目录路径(用于暂存文件)', default_work_dir)
    default_zip_name = f'{project_root.name}-source.zip'
    zip_path = prompt_zip_path(work_dir, default_zip_name)
    zip_path = archive_git_sources(project_root, work_dir, zip_path)
    print(f'打包完成: {zip_path}')


if __name__ == '__main__':
    main()

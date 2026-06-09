# -*- coding: utf-8 -*-
"""
交互式完成 GitHub/GitLab 仓库初始化、提交与推送。

特点：
1. 交互式输入，不依赖命令行参数。
2. 只写入当前仓库的本地 Git 用户信息，不污染全局配置。
3. 自动识别超过平台普通限制的大文件，并使用 Git LFS 处理。
4. GitHub 尽量保持原有行为，GitLab 支持 gitlab.com 与自建实例。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


FILE_LIMIT_BYTES = 100 * 1024 * 1024
PLATFORM_GITHUB = 'github'
PLATFORM_GITLAB = 'gitlab'
DEFAULT_GITLAB_HOST = 'gitlab.com'

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
PromptRunner = Callable[[str, str | None, bool], str]


@dataclass(eq=True)
class Account:
    """平台当前登录账号信息。"""

    login: str
    active: bool
    host: str


@dataclass
class LoginResult:
    """账号选择/登录的返回结果。"""

    account: Account
    newly_logged_in: bool


@dataclass
class Profile:
    """平台无关的用户资料。"""

    login: str
    display_name: str | None
    email: str | None
    commit_email_fallback: str | None

    @property
    def commit_name(self) -> str:
        return (self.display_name or '').strip() or self.login

    @property
    def commit_email(self) -> str | None:
        public_email = (self.email or '').strip()
        if public_email:
            return public_email
        fallback_email = (self.commit_email_fallback or '').strip()
        return fallback_email or None


class CommandError(RuntimeError):
    """外部命令执行失败。"""


def print_header(title: str) -> None:
    print(f'\n=== {title} ===')


def prompt_text(message: str, default: str | None = None, allow_empty: bool = False) -> str:
    while True:
        suffix = f' [{default}]' if default is not None else ''
        value = input(f'{message}{suffix}: ').strip()
        if value:
            return value
        if default is not None:
            return default
        if allow_empty:
            return ''
        print('输入不能为空，请重新输入。')


def prompt_yes_no(message: str, default: bool = True) -> bool:
    default_text = 'Y/n' if default else 'y/N'
    while True:
        value = input(f'{message} [{default_text}]: ').strip().lower()
        if not value:
            return default
        if value in {'y', 'yes'}:
            return True
        if value in {'n', 'no'}:
            return False
        print('请输入 y 或 n。')


def prompt_choice(message: str, options: list[str], default_index: int = 0) -> int:
    print(message)
    for index, option in enumerate(options, start=1):
        default_mark = ' (默认)' if index - 1 == default_index else ''
        print(f'{index}. {option}{default_mark}')

    while True:
        value = input('请输入选项编号: ').strip()
        if not value:
            return default_index
        if value.isdigit():
            selected = int(value) - 1
            if 0 <= selected < len(options):
                return selected
        print('编号无效，请重新输入。')


def run_command(
    command: list[str],
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = None
    if env is not None:
        merged_env = os.environ.copy()
        merged_env.update(env)

    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding='utf-8',
        errors='replace',
        capture_output=capture_output,
        env=merged_env,
    )
    if check and result.returncode != 0:
        command_text = ' '.join(command)
        stderr = (result.stderr or result.stdout or '').strip()
        raise CommandError(f'命令执行失败：{command_text}\n{stderr}')
    return result


def run_interactive(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    merged_env = None
    if env is not None:
        merged_env = os.environ.copy()
        merged_env.update(env)
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, env=merged_env)
    if result.returncode != 0:
        raise CommandError(f"命令执行失败：{' '.join(command)}")


def ensure_tool_exists(name: str) -> None:
    try:
        run_command([name, '--version'])
    except FileNotFoundError as exc:
        raise CommandError(f'未找到命令：{name}，请先安装并加入 PATH。') from exc


def parse_github_accounts(text: str) -> list[Account]:
    accounts: list[Account] = []
    current_login: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if 'Logged in to github.com account ' in line:
            current_login = line.split('Logged in to github.com account ', 1)[1].split(' ', 1)[0]
        elif current_login and line.startswith('- Active account:'):
            active = line.endswith('true')
            accounts.append(Account(login=current_login, active=active, host='github.com'))
            current_login = None

    return accounts


def parse_gitlab_accounts(text: str, active_host: str) -> list[Account]:
    accounts: list[Account] = []
    current_host: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(('✓', 'x', '-')):
            if 'Logged in to ' in line and ' as ' in line:
                host = line.split('Logged in to ', 1)[1].split(' as ', 1)[0].strip()
                login = line.rsplit(' as ', 1)[1].strip()
                accounts.append(Account(login=login, active=host == active_host, host=host))
            continue
        current_host = line
        if current_host and current_host == active_host:
            continue

    return accounts


def get_github_accounts(command_runner: CommandRunner = run_command) -> list[Account]:
    result = command_runner(['gh', 'auth', 'status'], capture_output=True)
    status_text = (result.stdout or '') + (result.stderr or '')
    return parse_github_accounts(status_text)


def get_gitlab_accounts(host: str, command_runner: CommandRunner = run_command) -> list[Account]:
    result = command_runner(['glab', 'auth', 'status', '--all'], capture_output=True)
    status_text = (result.stdout or '') + (result.stderr or '')
    return parse_gitlab_accounts(status_text, host)


def get_accounts(platform: str, host: str, command_runner: CommandRunner = run_command) -> list[Account]:
    if platform == PLATFORM_GITHUB:
        return get_github_accounts(command_runner=command_runner)
    return get_gitlab_accounts(host, command_runner=command_runner)


def get_active_account(platform: str, host: str, command_runner: CommandRunner = run_command) -> Account:
    accounts = get_accounts(platform, host, command_runner=command_runner)
    for account in accounts:
        if account.active:
            return account
    raise CommandError('未检测到当前平台的活动账号，请先登录。')


def build_hostname_env(host: str) -> dict[str, str] | None:
    if host == DEFAULT_GITLAB_HOST:
        return None
    return {'GITLAB_HOST': host}


def github_login_or_switch_account(command_runner: CommandRunner = run_command) -> LoginResult:
    print_header('GitHub 账号')
    accounts = get_github_accounts(command_runner=command_runner)

    if accounts:
        print('当前 gh 已登录账号：')
        for account in accounts:
            mark = ' [活动]' if account.active else ''
            print(f'- {account.login}{mark}')
    else:
        print('当前 gh 尚未登录任何账号。')

    options = [
        '继续使用当前活动账号',
        '切换到已登录账号',
        '通过浏览器登录一个新账号',
    ]
    default_index = 0 if accounts else 2
    selected = prompt_choice('请选择账号操作方式：', options, default_index=default_index)

    if selected == 0:
        return LoginResult(account=get_active_account(PLATFORM_GITHUB, 'github.com', command_runner=command_runner), newly_logged_in=False)

    if selected == 1:
        if not accounts:
            print('当前没有可切换账号，将转为浏览器登录。')
            run_interactive(['gh', 'auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https', '--web', '--skip-ssh-key'])
            return LoginResult(account=get_active_account(PLATFORM_GITHUB, 'github.com', command_runner=command_runner), newly_logged_in=True)

        existing_options = [account.login for account in accounts]
        switch_index = prompt_choice('请选择要切换到的账号：', existing_options, default_index=0)
        target_login = existing_options[switch_index]
        run_interactive(['gh', 'auth', 'switch', '--hostname', 'github.com', '--user', target_login])
        return LoginResult(account=get_active_account(PLATFORM_GITHUB, 'github.com', command_runner=command_runner), newly_logged_in=False)

    before = {account.login for account in accounts}
    run_interactive(['gh', 'auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https', '--web', '--skip-ssh-key'])
    after_accounts = get_github_accounts(command_runner=command_runner)

    for account in after_accounts:
        if account.login not in before:
            if not account.active:
                run_interactive(['gh', 'auth', 'switch', '--hostname', 'github.com', '--user', account.login])
            return LoginResult(
                account=get_active_account(PLATFORM_GITHUB, 'github.com', command_runner=command_runner),
                newly_logged_in=True,
            )

    return LoginResult(account=get_active_account(PLATFORM_GITHUB, 'github.com', command_runner=command_runner), newly_logged_in=False)


def gitlab_login_or_switch_account(host: str, command_runner: CommandRunner = run_command) -> LoginResult:
    print_header('GitLab 账号')
    env = build_hostname_env(host)
    accounts = get_gitlab_accounts(host, command_runner=command_runner)

    if accounts:
        print('当前 glab 已登录账号：')
        for account in accounts:
            mark = ' [活动]' if account.active else ''
            print(f'- {account.login} @ {account.host}{mark}')
    else:
        print('当前 glab 尚未登录任何账号。')

    options = [
        '继续使用当前活动账号',
        '切换到已登录账号',
        '通过浏览器登录一个新账号',
    ]
    default_index = 0 if accounts else 2
    selected = prompt_choice('请选择账号操作方式：', options, default_index=default_index)

    if selected == 0:
        return LoginResult(account=get_active_account(PLATFORM_GITLAB, host, command_runner=command_runner), newly_logged_in=False)

    if selected == 1:
        if not accounts:
            print('当前没有可切换账号，将转为浏览器登录。')
            run_interactive(['glab', 'auth', 'login', '--hostname', host, '--web'], env=env)
            return LoginResult(account=get_active_account(PLATFORM_GITLAB, host, command_runner=command_runner), newly_logged_in=True)

        existing_options = [account.login for account in accounts if account.host == host]
        if not existing_options:
            print('当前主机没有可切换账号，将转为浏览器登录。')
            run_interactive(['glab', 'auth', 'login', '--hostname', host, '--web'], env=env)
            return LoginResult(account=get_active_account(PLATFORM_GITLAB, host, command_runner=command_runner), newly_logged_in=True)

        switch_index = prompt_choice('请选择要切换到的账号：', existing_options, default_index=0)
        target_login = existing_options[switch_index]
        run_interactive(['glab', 'auth', 'logout', '--hostname', host], env=env)
        run_interactive(['glab', 'auth', 'login', '--hostname', host, '--web'], env=env)
        return LoginResult(account=Account(login=target_login, active=True, host=host), newly_logged_in=False)

    before = {account.login for account in accounts if account.host == host}
    run_interactive(['glab', 'auth', 'login', '--hostname', host, '--web'], env=env)
    after_accounts = get_gitlab_accounts(host, command_runner=command_runner)

    for account in after_accounts:
        if account.host == host and account.login not in before:
            return LoginResult(account=account, newly_logged_in=True)

    return LoginResult(account=get_active_account(PLATFORM_GITLAB, host, command_runner=command_runner), newly_logged_in=False)


def login_or_switch_account(platform: str, host: str, command_runner: CommandRunner = run_command) -> LoginResult:
    if platform == PLATFORM_GITHUB:
        return github_login_or_switch_account(command_runner=command_runner)
    return gitlab_login_or_switch_account(host, command_runner=command_runner)


def get_github_profile(command_runner: CommandRunner = run_command) -> Profile:
    result = command_runner(['gh', 'api', 'user'])
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CommandError('无法解析 gh api user 的返回结果。') from exc

    login = payload['login']
    user_id = payload['id']
    return Profile(
        login=login,
        display_name=payload.get('name'),
        email=payload.get('email'),
        commit_email_fallback=f'{user_id}+{login}@users.noreply.github.com',
    )


def get_gitlab_profile(host: str, command_runner: CommandRunner = run_command) -> Profile:
    env = build_hostname_env(host)
    result = command_runner(['glab', 'api', 'user', '--hostname', host], env=env)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CommandError('无法解析 glab api user 的返回结果。') from exc

    return Profile(
        login=payload['username'],
        display_name=payload.get('name'),
        email=payload.get('public_email') or payload.get('email'),
        commit_email_fallback=None,
    )


def get_gitlab_namespaces(host: str, command_runner: CommandRunner = run_command) -> list[str]:
    records = get_gitlab_namespace_records(host, command_runner=command_runner)
    return [record['full_path'] for record in records]


def get_gitlab_namespace_records(host: str, command_runner: CommandRunner = run_command) -> list[dict[str, object]]:
    env = build_hostname_env(host)
    result = command_runner(
        ['glab', 'api', 'namespaces?per_page=100', '--hostname', host],
        env=env,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CommandError('无法解析 glab api namespaces 的返回结果。') from exc

    if not isinstance(payload, list):
        return []

    namespaces: list[dict[str, object]] = []
    seen_full_paths: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        full_path = str(item.get('full_path') or '').strip()
        if full_path and full_path not in seen_full_paths:
            namespaces.append(item)
            seen_full_paths.add(full_path)
    return namespaces


def get_gitlab_namespace_id(host: str, namespace: str, command_runner: CommandRunner = run_command) -> int:
    for record in get_gitlab_namespace_records(host, command_runner=command_runner):
        full_path = str(record.get('full_path') or '').strip()
        if full_path != namespace:
            continue
        namespace_id = record.get('id')
        if isinstance(namespace_id, int):
            return namespace_id
        if isinstance(namespace_id, str) and namespace_id.isdigit():
            return int(namespace_id)
    raise CommandError(f'未在当前 GitLab 账号可见范围内找到 namespace：{namespace}')


def gitlab_project_exists(
    host: str,
    namespace: str,
    repo_name: str,
    command_runner: CommandRunner = run_command,
) -> bool:
    env = build_hostname_env(host)
    encoded_path = f'{namespace}/{repo_name}'.replace('/', '%2F')
    result = command_runner(
        ['glab', 'api', f'projects/{encoded_path}', '--hostname', host],
        check=False,
        env=env,
    )
    if result.returncode != 0:
        return False

    raw_output = (result.stdout or '').strip()
    if not raw_output:
        return False

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return False

    if not isinstance(payload, dict):
        return False

    project_id = payload.get('id')
    project_path = str(payload.get('path_with_namespace') or '').strip()
    expected_path = f'{namespace}/{repo_name}'
    if isinstance(project_id, int) and project_path == expected_path:
        return True
    if isinstance(project_id, str) and project_id.isdigit() and project_path == expected_path:
        return True
    return False


def get_profile(platform: str, host: str, command_runner: CommandRunner = run_command) -> Profile:
    if platform == PLATFORM_GITHUB:
        return get_github_profile(command_runner=command_runner)
    return get_gitlab_profile(host, command_runner=command_runner)


def resolve_repo_path() -> Path:
    print_header('仓库路径')
    default_path = os.getcwd()
    while True:
        repo_path = Path(prompt_text('请输入需要初始化并推送的本地目录', default=default_path)).expanduser()
        if repo_path.exists() and repo_path.is_dir():
            return repo_path
        print('目录不存在，请输入有效目录。')


def is_git_repo(repo_path: Path, command_runner: CommandRunner = run_command) -> bool:
    result = command_runner(['git', 'rev-parse', '--is-inside-work-tree'], cwd=repo_path, check=False)
    return result.returncode == 0 and (result.stdout or '').strip() == 'true'


def init_repo_if_needed(repo_path: Path, command_runner: CommandRunner = run_command) -> None:
    if is_git_repo(repo_path, command_runner=command_runner):
        print('检测到目标目录已经是 Git 仓库。')
        return

    print('目标目录还不是 Git 仓库，开始初始化。')
    command_runner(['git', 'init', '--initial-branch=main'], cwd=repo_path, capture_output=False)


def read_git_config(
    repo_path: Path,
    config_args: list[str],
    command_runner: CommandRunner = run_command,
) -> str | None:
    result = command_runner(['git', 'config', *config_args], cwd=repo_path, check=False)
    value = (result.stdout or '').strip()
    return value or None


def resolve_gitlab_commit_email(
    profile: Profile,
    repo_path: Path,
    command_runner: CommandRunner = run_command,
    prompt_runner: PromptRunner = prompt_text,
) -> str:
    commit_email = profile.commit_email
    if commit_email:
        return commit_email

    local_email = read_git_config(repo_path, ['user.email'], command_runner=command_runner)
    if local_email:
        return local_email

    global_email = read_git_config(repo_path, ['--global', 'user.email'], command_runner=command_runner)
    if global_email:
        return global_email

    manual_email = prompt_runner('未能自动获取 GitLab 提交邮箱，请手动输入提交邮箱', allow_empty=True).strip()
    if manual_email:
        return manual_email
    raise CommandError('GitLab 提交邮箱不能为空。')


def configure_local_identity(
    repo_path: Path,
    profile: Profile,
    platform: str,
    command_runner: CommandRunner = run_command,
    prompt_runner: PromptRunner = prompt_text,
) -> str:
    command_runner(['git', 'config', 'user.name', profile.commit_name], cwd=repo_path, capture_output=False)
    commit_email = profile.commit_email
    if platform == PLATFORM_GITLAB:
        commit_email = resolve_gitlab_commit_email(
            profile,
            repo_path,
            command_runner=command_runner,
            prompt_runner=prompt_runner,
        )
    if not commit_email:
        raise CommandError('未能确定提交邮箱。')
    command_runner(['git', 'config', 'user.email', commit_email], cwd=repo_path, capture_output=False)
    return commit_email


def iter_large_files(repo_path: Path) -> Iterable[Path]:
    for path in repo_path.rglob('*'):
        if not path.is_file():
            continue
        if '.git' in path.parts:
            continue
        try:
            if path.stat().st_size > FILE_LIMIT_BYTES:
                yield path
        except OSError:
            continue


def build_lfs_patterns(repo_path: Path, files: list[Path]) -> list[str]:
    patterns: list[str] = []
    by_suffix: dict[str, list[Path]] = {}
    no_suffix: list[Path] = []

    for file_path in files:
        suffix = file_path.suffix.lower()
        if suffix:
            by_suffix.setdefault(suffix, []).append(file_path)
        else:
            no_suffix.append(file_path)

    for suffix in sorted(by_suffix):
        patterns.append(f'*{suffix}')

    for file_path in sorted(no_suffix):
        relative = file_path.relative_to(repo_path)
        patterns.append(str(relative).replace('\\', '/'))

    return patterns


def setup_lfs_if_needed(repo_path: Path, command_runner: CommandRunner = run_command) -> None:
    large_files = list(iter_large_files(repo_path))
    if not large_files:
        print('未检测到超过 100MB 的文件，无需启用 Git LFS。')
        return

    print('检测到超过 100MB 的文件，将使用 Git LFS 处理：')
    for file_path in large_files:
        print(f'- {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)')

    ensure_tool_exists('git-lfs')
    command_runner(['git', 'lfs', 'install', '--local'], cwd=repo_path, capture_output=False)
    for pattern in build_lfs_patterns(repo_path, large_files):
        command_runner(['git', 'lfs', 'track', pattern], cwd=repo_path, capture_output=False)


def get_status_porcelain(repo_path: Path, command_runner: CommandRunner = run_command) -> str:
    result = command_runner(['git', 'status', '--short'], cwd=repo_path)
    return result.stdout or ''


def ensure_commit(repo_path: Path, default_message: str, command_runner: CommandRunner = run_command) -> None:
    command_runner(['git', 'add', '.'], cwd=repo_path, capture_output=False)
    status = get_status_porcelain(repo_path, command_runner=command_runner)
    if not status.strip():
        print('当前没有可提交的变更，将跳过提交。')
        return

    print('检测到以下待提交变更：')
    print(status)
    commit_message = prompt_text('请输入提交信息', default=default_message)
    command_runner(['git', 'commit', '-m', commit_message], cwd=repo_path, capture_output=False)


def has_head_commit(repo_path: Path, command_runner: CommandRunner = run_command) -> bool:
    result = command_runner(['git', 'rev-parse', '--verify', 'HEAD'], cwd=repo_path, check=False)
    return result.returncode == 0


def get_current_branch(repo_path: Path, command_runner: CommandRunner = run_command) -> str:
    result = command_runner(['git', 'branch', '--show-current'], cwd=repo_path)
    branch = (result.stdout or '').strip()
    return branch or 'main'


def has_origin_remote(repo_path: Path, command_runner: CommandRunner = run_command) -> bool:
    result = command_runner(['git', 'remote', 'get-url', 'origin'], cwd=repo_path, check=False)
    return result.returncode == 0


def get_origin_remote_url(repo_path: Path, command_runner: CommandRunner = run_command) -> str | None:
    result = command_runner(['git', 'remote', 'get-url', 'origin'], cwd=repo_path, check=False)
    if result.returncode != 0:
        return None
    remote_url = (result.stdout or '').strip()
    return remote_url or None


def build_gitlab_https_remote_url(host: str, namespace: str, repo_name: str) -> str:
    return f'https://{host}/{namespace}/{repo_name}.git'


def normalize_gitlab_origin_to_https(
    repo_path: Path,
    host: str,
    namespace: str,
    repo_name: str,
    command_runner: CommandRunner = run_command,
) -> None:
    remote_url = get_origin_remote_url(repo_path, command_runner=command_runner)
    if not remote_url:
        command_runner(
            ['git', 'remote', 'add', 'origin', build_gitlab_https_remote_url(host, namespace, repo_name)],
            cwd=repo_path,
            capture_output=False,
        )
        return

    ssh_markers = [
        f'git@{host}:',
        f'ssh://git@{host}/',
    ]
    if any(remote_url.startswith(marker) for marker in ssh_markers):
        command_runner(
            ['git', 'remote', 'set-url', 'origin', build_gitlab_https_remote_url(host, namespace, repo_name)],
            cwd=repo_path,
            capture_output=False,
        )


def create_github_remote(repo_path: Path, repo_name: str, visibility: str, command_runner: CommandRunner = run_command) -> None:
    if not has_head_commit(repo_path, command_runner=command_runner):
        raise CommandError('当前仓库还没有任何提交，无法创建远程仓库并推送。')

    branch = get_current_branch(repo_path, command_runner=command_runner)
    if has_origin_remote(repo_path, command_runner=command_runner):
        print('检测到已存在 origin，直接推送当前分支。')
        command_runner(['git', 'push', '-u', 'origin', branch], cwd=repo_path, capture_output=False)
        return

    visibility_flag = f'--{visibility}'
    command_runner(
        [
            'gh',
            'repo',
            'create',
            repo_name,
            visibility_flag,
            '--source=.',
            '--remote=origin',
            '--push',
        ],
        cwd=repo_path,
        capture_output=False,
    )


def create_gitlab_remote(
    repo_path: Path,
    repo_name: str,
    visibility: str,
    host: str,
    namespace: str | None,
    command_runner: CommandRunner = run_command,
) -> None:
    if not has_head_commit(repo_path, command_runner=command_runner):
        raise CommandError('当前仓库还没有任何提交，无法创建远程仓库并推送。')

    branch = get_current_branch(repo_path, command_runner=command_runner)
    env = build_hostname_env(host)
    namespace_value = namespace or ''
    project_exists = gitlab_project_exists(host, namespace_value, repo_name, command_runner=command_runner)
    if has_origin_remote(repo_path, command_runner=command_runner):
        print('检测到已存在 origin，将检查远端项目并推送当前分支。')
        normalize_gitlab_origin_to_https(
            repo_path,
            host,
            namespace_value,
            repo_name,
            command_runner=command_runner,
        )
    else:
        remote_url = build_gitlab_https_remote_url(host, namespace_value, repo_name)
        command_runner(['git', 'remote', 'add', 'origin', remote_url], cwd=repo_path, capture_output=False)

    if not project_exists:
        namespace_id = get_gitlab_namespace_id(host, namespace_value, command_runner=command_runner)
        command_runner(
            [
                'glab',
                'api',
                'projects',
                '--hostname',
                host,
                '--method',
                'POST',
                '-f',
                f'name={repo_name}',
                '-f',
                f'path={repo_name}',
                '-F',
                f'namespace_id={namespace_id}',
                '-f',
                f'visibility={visibility}',
            ],
            cwd=repo_path,
            capture_output=True,
            env=env,
        )
    command_runner(['git', 'push', '-u', 'origin', branch], cwd=repo_path, capture_output=False)


def create_or_push_remote(
    platform: str,
    repo_path: Path,
    repo_name: str,
    visibility: str,
    host: str,
    namespace: str | None = None,
    command_runner: CommandRunner = run_command,
) -> None:
    if platform == PLATFORM_GITHUB:
        create_github_remote(repo_path, repo_name, visibility, command_runner=command_runner)
        return
    create_gitlab_remote(
        repo_path,
        repo_name,
        visibility,
        host,
        namespace,
        command_runner=command_runner,
    )


def get_visibility_options(platform: str) -> list[str]:
    if platform == PLATFORM_GITHUB:
        return ['public', 'private']
    return ['public', 'internal', 'private']


def prompt_platform() -> str:
    print_header('平台选择')
    platform_index = prompt_choice('请选择远程平台：', ['GitHub', 'GitLab'], default_index=0)
    return [PLATFORM_GITHUB, PLATFORM_GITLAB][platform_index]


def resolve_host(platform: str) -> str:
    if platform == PLATFORM_GITHUB:
        return 'github.com'
    print_header('GitLab 主机')
    return prompt_text('请输入 GitLab 主机', default=DEFAULT_GITLAB_HOST)


def resolve_namespace(
    platform: str,
    profile: Profile,
    host: str,
    command_runner: CommandRunner = run_command,
) -> str | None:
    if platform == PLATFORM_GITHUB:
        return None

    try:
        namespace_options = get_gitlab_namespaces(host, command_runner=command_runner)
    except CommandError:
        namespace_options = []

    default_namespace = profile.login
    if default_namespace not in namespace_options:
        namespace_options.append(default_namespace)

    namespace_options = [item for item in namespace_options if item]
    if not namespace_options:
        return prompt_text('请输入 GitLab namespace/group/subgroup', default=default_namespace)

    options = namespace_options + ['手动输入其他 namespace']
    selected_index = prompt_choice('请选择 GitLab namespace/group/subgroup：', options, default_index=0)
    selected_value = options[selected_index]
    if selected_value == '手动输入其他 namespace':
        return prompt_text('请输入 GitLab namespace/group/subgroup', default=default_namespace)
    return selected_value


def print_summary(
    repo_path: Path,
    platform: str,
    host: str,
    profile: Profile,
    repo_name: str,
    visibility: str,
    commit_email: str,
    namespace: str | None = None,
) -> None:
    print_header('执行摘要')
    print(f'目标目录: {repo_path}')
    print(f'平台: {platform}')
    print(f'主机: {host}')
    print(f'活动账号: {profile.login}')
    print(f'提交用户名: {profile.commit_name}')
    print(f'提交邮箱: {commit_email}')
    if platform == PLATFORM_GITHUB:
        print(f'远程仓库名: {repo_name}')
    else:
        print(f'远程项目路径: {namespace}/{repo_name}')
    print(f'远程仓库可见性: {visibility}')


def logout_new_account_if_requested(platform: str, host: str, new_login: str, original_active_login: str | None) -> None:
    print_header('账号清理')
    cli_name = 'gh' if platform == PLATFORM_GITHUB else 'glab'
    if not prompt_yes_no(f'是否删除本次新登录的 {cli_name} 账号信息：{new_login}', default=False):
        print('已保留本次登录的账号信息。')
        return

    accounts = get_accounts(platform, host)
    existing_logins = {account.login for account in accounts if account.host == host}
    if new_login not in existing_logins:
        print('未检测到该账号仍处于登录状态，跳过清理。')
        return

    if platform == PLATFORM_GITHUB:
        if original_active_login and original_active_login != new_login and original_active_login in existing_logins:
            run_interactive(['gh', 'auth', 'switch', '--hostname', 'github.com', '--user', original_active_login])
        run_interactive(['gh', 'auth', 'logout', '--hostname', 'github.com', '--user', new_login])
    else:
        env = build_hostname_env(host)
        run_interactive(['glab', 'auth', 'logout', '--hostname', host], env=env)
    print(f'已删除账号 {new_login} 的本地登录信息。')


def main() -> int:
    login_result: LoginResult | None = None
    original_active_login: str | None = None
    platform = PLATFORM_GITHUB
    host = 'github.com'
    try:
        print_header('环境检查')
        ensure_tool_exists('git')

        platform = prompt_platform()
        host = resolve_host(platform)
        ensure_tool_exists('gh' if platform == PLATFORM_GITHUB else 'glab')

        repo_path = resolve_repo_path()
        try:
            original_active_login = get_active_account(platform, host).login
        except CommandError:
            original_active_login = None

        login_result = login_or_switch_account(platform, host)
        account = login_result.account
        profile = get_profile(platform, host)
        if profile.login != account.login:
            print(f'警告：当前活动账号从 {account.login} 变为 {profile.login}，将以当前活动账号为准。')

        namespace = resolve_namespace(platform, profile, host)
        default_repo_name = repo_path.name
        repo_name = prompt_text('请输入远程仓库名', default=default_repo_name)
        visibility_options = get_visibility_options(platform)
        visibility_index = prompt_choice('请选择仓库可见性：', visibility_options, default_index=0)
        visibility = visibility_options[visibility_index]
        default_message = 'Initial commit'

        commit_email = profile.commit_email or (
            read_git_config(repo_path, ['user.email']) if platform == PLATFORM_GITLAB else ''
        ) or '(将在执行时确定)'
        print_summary(repo_path, platform, host, profile, repo_name, visibility, commit_email, namespace=namespace)
        if not prompt_yes_no('确认开始执行以上操作吗？', default=True):
            print('已取消。')
            return 0

        print_header('执行中')
        init_repo_if_needed(repo_path)
        commit_email = configure_local_identity(repo_path, profile, platform)
        setup_lfs_if_needed(repo_path)
        ensure_commit(repo_path, default_message)
        create_or_push_remote(platform, repo_path, repo_name, visibility, host, namespace=namespace)

        print_header('完成')
        print('仓库初始化、提交和推送已完成。')
        print(f'目录: {repo_path}')
        print(f'平台: {platform}')
        print(f'账号: {profile.login}')
        print(f'提交身份: {profile.commit_name} <{commit_email}>')
        return 0

    except KeyboardInterrupt:
        print('\n操作已被用户中断。')
        return 1
    except CommandError as exc:
        print(f'\n执行失败：\n{exc}')
        return 1
    except FileNotFoundError as exc:
        print(f'\n执行失败：未找到命令或文件：{exc}')
        return 1
    finally:
        if login_result and login_result.newly_logged_in:
            try:
                logout_new_account_if_requested(platform, host, login_result.account.login, original_active_login)
            except Exception as exc:  # noqa: BLE001
                print(f'\n账号清理失败：{exc}')


if __name__ == '__main__':
    sys.exit(main())

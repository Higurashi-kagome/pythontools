# -*- coding: utf-8 -*-
"""
交互式管理 github.com 上的 gh 本地登录账号。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable

try:
    import questionary
except ImportError:  # pragma: no cover - 依赖缺失路径由 main 测试覆盖
    questionary = None


HOSTNAME = 'github.com'

STATUS_COMMAND = ['gh', 'auth', 'status', '--hostname', HOSTNAME, '--json', 'hosts']
SWITCH_COMMAND = ['gh', 'auth', 'switch', '--hostname', HOSTNAME]
LOGOUT_COMMAND = ['gh', 'auth', 'logout', '--hostname', HOSTNAME]
LOGIN_COMMAND = [
    'gh',
    'auth',
    'login',
    '--hostname',
    HOSTNAME,
    '--git-protocol',
    'https',
    '--web',
    '--skip-ssh-key',
]


class CommandError(RuntimeError):
    """命令执行或依赖检查失败。"""


@dataclass(slots=True)
class Account:
    """gh 账号状态。"""

    login: str
    active: bool
    state: str
    token_source: str | None = None
    git_protocol: str | None = None
    scopes: str | None = None
    error: str | None = None

    def summary(self) -> str:
        tags: list[str] = []
        if self.active:
            tags.append('当前')
        tags.append(f'状态={self.state}')
        if self.token_source:
            tags.append(f'token={self.token_source}')
        if self.git_protocol:
            tags.append(f'git={self.git_protocol}')
        if self.error:
            tags.append(f'错误={self.error}')
        return f'{self.login} [{", ".join(tags)}]'


CommandRunner = Callable[[list[str], bool], subprocess.CompletedProcess[str]]
InteractiveRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def print_header(title: str) -> None:
    print(f'\n=== {title} ===')


def run_command(command: list[str], capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            text=True,
            encoding='utf-8',
            errors='replace',
            capture_output=capture_output,
        )
    except FileNotFoundError as exc:
        raise CommandError(f'未找到命令：{command[0]}，请先安装并加入 PATH。') from exc

    if result.returncode != 0:
        details = (result.stderr or result.stdout or '').strip()
        raise CommandError(f'命令执行失败：{" ".join(command)}\n{details}')
    return result


def run_interactive(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command)
    except FileNotFoundError as exc:
        raise CommandError(f'未找到命令：{command[0]}，请先安装并加入 PATH。') from exc

    if result.returncode != 0:
        raise CommandError(f'命令执行失败：{" ".join(command)}')
    return subprocess.CompletedProcess(command, result.returncode, '', '')


def ensure_tool_exists(name: str) -> None:
    if shutil.which(name) is None:
        raise CommandError(f'未找到命令：{name}，请先安装并加入 PATH。')


def ensure_questionary_available() -> Any:
    if questionary is None:
        raise CommandError('缺少依赖 questionary，请先执行 `pip install -r requirements.txt`。')
    return questionary


def parse_accounts_payload(payload: dict[str, Any]) -> list[Account]:
    hosts = payload.get('hosts')
    if not isinstance(hosts, dict):
        return []

    raw_accounts = hosts.get(HOSTNAME)
    if not isinstance(raw_accounts, list):
        return []

    accounts: list[Account] = []
    for raw_account in raw_accounts:
        if not isinstance(raw_account, dict):
            continue

        login = _string_or_none(raw_account.get('login'))
        if not login:
            continue

        accounts.append(
            Account(
                login=login,
                active=bool(raw_account.get('active', False)),
                state=_string_or_none(raw_account.get('state')) or 'unknown',
                token_source=_string_or_none(raw_account.get('tokenSource')),
                git_protocol=_string_or_none(raw_account.get('gitProtocol')),
                scopes=_string_or_none(raw_account.get('scopes')),
                error=_string_or_none(raw_account.get('error')),
            )
        )

    return sorted(accounts, key=lambda account: (not account.active, account.login.lower()))


def read_accounts(command_runner: CommandRunner = run_command) -> list[Account]:
    result = command_runner(STATUS_COMMAND, True)
    try:
        payload = json.loads(result.stdout or '{}')
    except json.JSONDecodeError as exc:
        raise CommandError('无法解析 gh auth status 的 JSON 输出。') from exc
    return parse_accounts_payload(payload)


def switch_account(login: str, command_runner: CommandRunner = run_command) -> None:
    command_runner([*SWITCH_COMMAND, '--user', login], True)


def logout_account(login: str, command_runner: CommandRunner = run_command) -> None:
    command_runner([*LOGOUT_COMMAND, '--user', login], True)


def login_account(command_runner: InteractiveRunner = run_interactive) -> None:
    command_runner(LOGIN_COMMAND)


def find_active_account(accounts: list[Account]) -> Account | None:
    for account in accounts:
        if account.active:
            return account
    return None


def build_status_lines(accounts: list[Account]) -> list[str]:
    if not accounts:
        return ['当前没有已登录的 gh 账号。']

    lines = []
    for index, account in enumerate(accounts, start=1):
        lines.append(f'{index}. {account.summary()}')
        if account.scopes:
            lines.append(f'   scopes: {account.scopes}')
    return lines


def prompt_main_action(accounts: list[Account]) -> str | None:
    q = ensure_questionary_available()
    active_account = find_active_account(accounts)
    active_text = active_account.login if active_account else '无'
    choices = [
        q.Choice(title=f'查看账号状态（当前：{active_text}）', value='status'),
        q.Choice(
            title='切换账号',
            value='switch',
            disabled='没有可切换的其他账号' if len(accounts) < 2 else None,
        ),
        q.Choice(title='登录新账号', value='login'),
        q.Choice(
            title='删除账号',
            value='delete',
            disabled='当前没有已登录账号' if not accounts else None,
        ),
        q.Choice(title='刷新状态', value='refresh'),
        q.Choice(title='退出', value='quit'),
    ]
    return q.select('请选择操作：', choices=choices, use_shortcuts=True).ask()


def prompt_account(accounts: list[Account], message: str, *, exclude_active: bool = False) -> Account | None:
    q = ensure_questionary_available()
    candidates = [account for account in accounts if not (exclude_active and account.active)]
    if not candidates:
        return None

    choice_map = {
        account.login: account
        for account in candidates
    }
    choices = [q.Choice(title=account.summary(), value=account.login) for account in candidates]
    login = q.select(message, choices=choices, use_shortcuts=True).ask()
    if login is None:
        return None
    return choice_map.get(login)


def confirm_logout(account: Account, total_count: int) -> bool:
    q = ensure_questionary_available()
    warning = '这只会删除本机保存的登录态，不会吊销 GitHub 上的 token。'
    if account.active and total_count == 1:
        message = f'即将删除最后一个账号 {account.login}。{warning} 是否继续？'
    elif account.active:
        message = f'即将删除当前活动账号 {account.login}。{warning} 是否继续？'
    else:
        message = f'即将删除账号 {account.login}。{warning} 是否继续？'

    confirmed = q.confirm(message, default=False).ask()
    return bool(confirmed)


def show_status(accounts: list[Account]) -> None:
    print_header('gh 账号状态')
    for line in build_status_lines(accounts):
        print(line)


def main() -> int:
    try:
        ensure_tool_exists('gh')
        ensure_questionary_available()
    except CommandError as exc:
        print(str(exc))
        return 1

    print('仅管理 github.com 的 gh 本地登录账号。')

    try:
        while True:
            try:
                accounts = read_accounts()
                action = prompt_main_action(accounts)

                if action in {None, 'quit'}:
                    print('已退出。')
                    return 0

                if action == 'status':
                    show_status(accounts)
                    continue

                if action == 'refresh':
                    continue

                if action == 'switch':
                    target = prompt_account(accounts, '请选择要切换到的账号：', exclude_active=True)
                    if target is None:
                        print('已取消切换。')
                        continue
                    switch_account(target.login)
                    print(f'已切换到账号：{target.login}')
                    continue

                if action == 'login':
                    print('即将打开浏览器完成 gh 登录。')
                    login_account()
                    print('登录流程已结束，返回主菜单。')
                    continue

                if action == 'delete':
                    target = prompt_account(accounts, '请选择要删除的账号：')
                    if target is None:
                        print('已取消删除。')
                        continue
                    if not confirm_logout(target, len(accounts)):
                        print('已取消删除。')
                        continue
                    logout_account(target.login)
                    print(f'已删除本地 gh 账号：{target.login}')
                    continue

                print('未识别的操作，已返回主菜单。')
            except CommandError as exc:
                print(str(exc))
    except KeyboardInterrupt:
        print('\n操作已取消。')
        return 130


if __name__ == '__main__':
    sys.exit(main())

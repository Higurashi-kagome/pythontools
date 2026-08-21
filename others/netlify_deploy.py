# -*- coding: utf-8 -*-
"""通过 Netlify CLI 将指定目录发布到当前站点的生产环境。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess
from typing import Callable, Sequence


class CommandError(RuntimeError):
    """Netlify CLI 不可用或无法启动。"""


CommandRunner = Callable[..., CompletedProcess[str]]


@dataclass(frozen=True)
class DeployDetails:
    """部署成功后从 Netlify CLI 状态中读取的站点信息。"""

    site_url: str
    project_url: str | None
    site_name: str | None
    account_email: str | None
    team_slug: str | None


def find_netlify_command() -> str:
    """查找可执行的 Netlify CLI 命令。

    返回：
        可传给 `subprocess.run` 的 Netlify CLI 路径。

    异常：
        找不到 Netlify CLI 时抛出 `CommandError`。
    """
    for name in ('netlify.cmd', 'netlify'):
        command = shutil.which(name)
        if command:
            return command
    raise CommandError('未找到 Netlify CLI，请先执行 `npm install -g netlify-cli`。')


def run_netlify(
    args: Sequence[str],
    *,
    capture_output: bool = False,
    cwd: Path | None = None,
) -> CompletedProcess[str]:
    """运行 Netlify CLI 子命令。

    参数：
        args：Netlify CLI 子命令及其参数。
        capture_output：是否捕获输出，交互式命令应保持为 `False`。
        cwd：CLI 的工作目录；未指定时沿用当前终端目录。

    返回：
        Netlify CLI 的进程结果。

    异常：
        找不到 Netlify CLI 时抛出 `CommandError`。
    """
    command = [find_netlify_command(), *args]
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=False,
            text=True,
            encoding='utf-8',
            errors='replace',
            capture_output=capture_output,
        )
    except OSError as exc:
        raise CommandError(f'无法启动 Netlify CLI：{exc}') from exc


def prepare_account(
    *,
    command_runner: CommandRunner = run_netlify,
) -> bool:
    """确认部署使用的 Netlify 账号。

    参数：
        command_runner：运行 Netlify CLI 的函数，便于测试命令调用。

    返回：
        用户完成账号选择或登录并应继续部署时返回 `True`，取消或失败时返回 `False`。
    """
    print('请在接下来的 Netlify CLI 菜单中选择账号，或选择登录新账号：')
    result = command_runner(['switch'])
    return result.returncode == 0


def build_deploy_args(directory: Path) -> list[str]:
    """构造生产环境部署参数。

    参数：
        directory：待上传的静态网站目录。

    返回：
        Netlify CLI `deploy` 子命令参数。
    """
    return ['deploy', '--prod', '--no-build', '--dir', str(directory)]


def extract_status_value(status_text: str, label: str) -> str | None:
    """从 `netlify status` 文本中读取指定字段。

    参数：
        status_text：Netlify CLI 输出的状态文本。
        label：要读取的字段名。

    返回：
        字段值；找不到时返回 `None`。
    """
    pattern = rf'^\s*{re.escape(label)}\s*:\s*(\S+)'
    match = re.search(pattern, status_text, re.MULTILINE)
    return match.group(1).strip('<>') if match else None


def parse_team_slug(teams_json: str) -> str | None:
    """从 `netlify teams:list --json` 结果中读取默认团队 slug。

    参数：
        teams_json：Netlify CLI 输出的团队 JSON。

    返回：
        默认团队或第一个团队的 slug；无法解析时返回 `None`。
    """
    try:
        teams = json.loads(teams_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(teams, list):
        return None

    valid_teams = [team for team in teams if isinstance(team, dict) and team.get('slug')]
    if not valid_teams:
        return None
    team = next((team for team in valid_teams if team.get('default')), valid_teams[0])
    return str(team['slug'])


def read_deploy_details(command_runner: CommandRunner = run_netlify) -> DeployDetails | None:
    """读取部署成功后的站点、账号和团队信息。

    参数：
        command_runner：运行 Netlify CLI 的函数。

    返回：
        读取成功后的部署信息；CLI 查询失败时返回 `None`。
    """
    status = command_runner(['status'], capture_output=True)
    if status.returncode != 0:
        return None

    status_text = status.stdout or ''
    site_url = extract_status_value(status_text, 'Project URL')
    if not site_url:
        return None

    teams = command_runner(['teams:list', '--json'], capture_output=True)
    team_slug = parse_team_slug(teams.stdout or '') if teams.returncode == 0 else None
    site_name = extract_status_value(status_text, 'Current project')
    project_url = extract_status_value(status_text, 'Admin URL')
    if not project_url and site_name:
        project_url = f'https://app.netlify.com/projects/{site_name}/overview'

    return DeployDetails(
        site_url=site_url,
        project_url=project_url,
        site_name=site_name,
        account_email=extract_status_value(status_text, 'Email'),
        team_slug=team_slug,
    )


def build_post_deploy_notice(details: DeployDetails) -> str:
    """生成部署成功后的后续操作说明。

    参数：
        details：部署成功后的站点信息。

    返回：
        要打印给用户的说明文本。
    """
    project_url = details.project_url or '当前 Netlify 项目页面'
    account_email = details.account_email or '当前 Netlify 账号'
    billing_url = (
        f'https://app.netlify.com/teams/{details.team_slug}/billing/general'
        if details.team_slug
        else '当前 Netlify 团队的账单页面'
    )
    return (
        f'已部署：{details.site_url}\n\n'
        f'后续更新访问 {project_url} 将网页文件夹拖拽到图中位置即可，账号 {account_email}\n\n'
        f'每月有 100G 免费额度，重新部署会消耗额度（最好不要太频繁部署），剩余额度可在 {billing_url} 查看。'
    )


def print_post_deploy_notice(command_runner: CommandRunner = run_netlify) -> None:
    """打印部署成功后的站点访问和额度说明。

    参数：
        command_runner：运行 Netlify CLI 的函数。
    """
    try:
        details = read_deploy_details(command_runner)
    except CommandError:
        details = None

    if details is None:
        print('部署已成功，但未能读取站点详情，请查看上方 Netlify CLI 输出中的 Production URL。')
        return
    print()
    print(build_post_deploy_notice(details))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。

    参数：
        argv：待解析的参数；为 `None` 时读取进程参数。

    返回：
        解析后的命令行参数。
    """
    parser = argparse.ArgumentParser(
        description='将指定的静态网站目录发布到当前 Netlify 站点的生产环境。',
    )
    parser.add_argument('directory', type=Path, help='静态网站目录路径')
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    command_runner: CommandRunner = run_netlify,
) -> int:
    """校验目录、确认账号并执行生产部署。

    参数：
        argv：命令行参数；为 `None` 时读取进程参数。
        command_runner：运行 Netlify CLI 的函数。

    返回：
        成功返回 `0`，参数、账号或部署失败时返回非零值。
    """
    args = parse_args(argv)
    directory = args.directory.expanduser().resolve()
    if not directory.is_dir():
        print(f'目录不存在或不是目录：{directory}', file=sys.stderr)
        return 2

    print(f'待部署目录：{directory}')
    try:
        if not prepare_account(command_runner=command_runner):
            return 1

        print('开始发布到 Netlify 生产环境，上传进度由 Netlify CLI 输出：')
        result = command_runner(build_deploy_args(directory))
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(f'部署失败，退出码：{result.returncode}', file=sys.stderr)
    else:
        print_post_deploy_notice(command_runner)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())

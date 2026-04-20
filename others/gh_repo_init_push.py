# -*- coding: utf-8 -*-
"""
使用 gh 交互式登录/切换 GitHub 账号，并完成仓库初始化、提交与推送。

特点：
1. 交互式输入，不依赖命令行参数。
2. 只写入当前仓库的本地 Git 用户信息，不污染全局配置。
3. 自动识别超过 GitHub 普通限制的大文件，并使用 Git LFS 处理。
4. 优先使用当前 gh 活动账号信息；如账号未公开邮箱，则自动回退到 noreply 邮箱。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


GITHUB_FILE_LIMIT_BYTES = 100 * 1024 * 1024


@dataclass
class Account:
    """gh 当前登录账号信息。"""

    login: str
    active: bool


@dataclass
class LoginResult:
    """账号选择/登录的返回结果。"""

    account: Account
    newly_logged_in: bool


@dataclass
class GitHubProfile:
    """GitHub 用户公开资料。"""

    login: str
    user_id: int
    name: str | None
    email: str | None

    @property
    def commit_name(self) -> str:
        """提交作者名优先使用公开 name，否则回退到登录名。"""
        return (self.name or "").strip() or self.login

    @property
    def commit_email(self) -> str:
        """
        提交邮箱优先使用公开邮箱。
        如 gh token 没有 user scope 或账号未公开邮箱，则回退到 GitHub noreply。
        """
        public_email = (self.email or "").strip()
        if public_email:
            return public_email
        return f"{self.user_id}+{self.login}@users.noreply.github.com"


class CommandError(RuntimeError):
    """外部命令执行失败。"""


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def prompt_text(message: str, default: str | None = None, allow_empty: bool = False) -> str:
    """读取用户输入。"""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{message}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if allow_empty:
            return ""
        print("输入不能为空，请重新输入。")


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """读取是/否选择。"""
    default_text = "Y/n" if default else "y/N"
    while True:
        value = input(f"{message} [{default_text}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("请输入 y 或 n。")


def prompt_choice(message: str, options: list[str], default_index: int = 0) -> int:
    """读取编号选择。"""
    print(message)
    for index, option in enumerate(options, start=1):
        default_mark = " (默认)" if index - 1 == default_index else ""
        print(f"{index}. {option}{default_mark}")

    while True:
        value = input("请输入选项编号: ").strip()
        if not value:
            return default_index
        if value.isdigit():
            selected = int(value) - 1
            if 0 <= selected < len(options):
                return selected
        print("编号无效，请重新输入。")


def run_command(
    command: list[str],
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """执行命令，默认捕获输出用于解析。"""
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture_output,
    )
    if check and result.returncode != 0:
        command_text = " ".join(command)
        stderr = (result.stderr or result.stdout or "").strip()
        raise CommandError(f"命令执行失败：{command_text}\n{stderr}")
    return result


def run_interactive(command: list[str], cwd: Path | None = None) -> None:
    """执行需要直接把输出展示给用户的命令。"""
    result = subprocess.run(command, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise CommandError(f"命令执行失败：{' '.join(command)}")


def ensure_tool_exists(name: str) -> None:
    """确保依赖工具存在。"""
    try:
        run_command([name, "--version"])
    except FileNotFoundError as exc:
        raise CommandError(f"未找到命令：{name}，请先安装并加入 PATH。") from exc


def parse_accounts(text: str) -> list[Account]:
    """解析 gh auth status 输出中的账号列表。"""
    accounts: list[Account] = []
    current_login: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "Logged in to github.com account " in line:
            current_login = line.split("Logged in to github.com account ", 1)[1].split(" ", 1)[0]
        elif current_login and line.startswith("- Active account:"):
            active = line.endswith("true")
            accounts.append(Account(login=current_login, active=active))
            current_login = None

    return accounts


def get_accounts() -> list[Account]:
    """获取 gh 当前已登录账号列表。"""
    result = run_command(["gh", "auth", "status"], capture_output=True)
    status_text = (result.stdout or "") + (result.stderr or "")
    return parse_accounts(status_text)


def get_active_account() -> Account:
    """获取 gh 当前活动账号。"""
    accounts = get_accounts()
    for account in accounts:
        if account.active:
            return account
    raise CommandError("未检测到 gh 活动账号，请先登录。")


def login_or_switch_account() -> LoginResult:
    """登录新账号或切换现有账号。"""
    print_header("GitHub 账号")
    accounts = get_accounts()

    if accounts:
        print("当前 gh 已登录账号：")
        for account in accounts:
            mark = " [活动]" if account.active else ""
            print(f"- {account.login}{mark}")
    else:
        print("当前 gh 尚未登录任何账号。")

    options = [
        "继续使用当前活动账号",
        "切换到已登录账号",
        "通过浏览器登录一个新账号",
    ]
    default_index = 0 if accounts else 2
    selected = prompt_choice("请选择账号操作方式：", options, default_index=default_index)

    if selected == 0:
        return LoginResult(account=get_active_account(), newly_logged_in=False)

    if selected == 1:
        if not accounts:
            print("当前没有可切换账号，将转为浏览器登录。")
            run_interactive(["gh", "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web", "--skip-ssh-key"])
            return LoginResult(account=get_active_account(), newly_logged_in=True)

        existing_options = [account.login for account in accounts]
        switch_index = prompt_choice("请选择要切换到的账号：", existing_options, default_index=0)
        target_login = existing_options[switch_index]
        run_interactive(["gh", "auth", "switch", "--hostname", "github.com", "--user", target_login])
        return LoginResult(account=get_active_account(), newly_logged_in=False)

    before = {account.login for account in accounts}
    run_interactive(["gh", "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web", "--skip-ssh-key"])
    after_accounts = get_accounts()

    for account in after_accounts:
        if account.login not in before:
            if not account.active:
                run_interactive(["gh", "auth", "switch", "--hostname", "github.com", "--user", account.login])
            return LoginResult(account=get_active_account(), newly_logged_in=True)

    return LoginResult(account=get_active_account(), newly_logged_in=False)


def get_profile() -> GitHubProfile:
    """获取当前活动账号资料。"""
    result = run_command(["gh", "api", "user"])
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CommandError("无法解析 gh api user 的返回结果。") from exc

    return GitHubProfile(
        login=payload["login"],
        user_id=payload["id"],
        name=payload.get("name"),
        email=payload.get("email"),
    )


def resolve_repo_path() -> Path:
    """交互式读取目标仓库路径。"""
    print_header("仓库路径")
    default_path = os.getcwd()
    while True:
        repo_path = Path(prompt_text("请输入需要初始化并推送的本地目录", default=default_path)).expanduser()
        if repo_path.exists() and repo_path.is_dir():
            return repo_path
        print("目录不存在，请输入有效目录。")


def is_git_repo(repo_path: Path) -> bool:
    """判断目录是否为 Git 仓库。"""
    result = run_command(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_path,
        check=False,
    )
    return result.returncode == 0 and (result.stdout or "").strip() == "true"


def init_repo_if_needed(repo_path: Path) -> None:
    """初始化 Git 仓库。"""
    if is_git_repo(repo_path):
        print("检测到目标目录已经是 Git 仓库。")
        return

    print("目标目录还不是 Git 仓库，开始初始化。")
    run_command(["git", "init", "--initial-branch=main"], cwd=repo_path, capture_output=False)


def configure_local_identity(repo_path: Path, profile: GitHubProfile) -> None:
    """只设置当前仓库的本地提交身份。"""
    run_command(["git", "config", "user.name", profile.commit_name], cwd=repo_path, capture_output=False)
    run_command(["git", "config", "user.email", profile.commit_email], cwd=repo_path, capture_output=False)


def iter_large_files(repo_path: Path) -> Iterable[Path]:
    """遍历超过 GitHub 普通文件大小限制的文件。"""
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        try:
            if path.stat().st_size > GITHUB_FILE_LIMIT_BYTES:
                yield path
        except OSError:
            continue


def build_lfs_patterns(repo_path: Path, files: list[Path]) -> list[str]:
    """根据大文件生成较稳妥的 Git LFS 跟踪规则。"""
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
        patterns.append(f"*{suffix}")

    for file_path in sorted(no_suffix):
        relative = file_path.relative_to(repo_path)
        patterns.append(str(relative).replace("\\", "/"))

    return patterns


def setup_lfs_if_needed(repo_path: Path) -> None:
    """如检测到超大文件，则启用 Git LFS。"""
    large_files = list(iter_large_files(repo_path))
    if not large_files:
        print("未检测到超过 100MB 的文件，无需启用 Git LFS。")
        return

    print("检测到超过 100MB 的文件，将使用 Git LFS 处理：")
    for file_path in large_files:
        print(f"- {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")

    ensure_tool_exists("git-lfs")
    run_command(["git", "lfs", "install", "--local"], cwd=repo_path, capture_output=False)
    for pattern in build_lfs_patterns(repo_path, large_files):
        run_command(["git", "lfs", "track", pattern], cwd=repo_path, capture_output=False)


def get_status_porcelain(repo_path: Path) -> str:
    """获取简洁版 git status。"""
    result = run_command(["git", "status", "--short"], cwd=repo_path)
    return result.stdout or ""


def ensure_commit(repo_path: Path, default_message: str) -> None:
    """添加并提交变更。"""
    run_command(["git", "add", "."], cwd=repo_path, capture_output=False)
    status = get_status_porcelain(repo_path)
    if not status.strip():
        print("当前没有可提交的变更，将跳过提交。")
        return

    print("检测到以下待提交变更：")
    print(status)
    commit_message = prompt_text("请输入提交信息", default=default_message)
    run_command(["git", "commit", "-m", commit_message], cwd=repo_path, capture_output=False)


def has_head_commit(repo_path: Path) -> bool:
    """判断仓库是否至少已有一个提交。"""
    result = run_command(["git", "rev-parse", "--verify", "HEAD"], cwd=repo_path, check=False)
    return result.returncode == 0


def get_current_branch(repo_path: Path) -> str:
    """获取当前分支名。"""
    result = run_command(["git", "branch", "--show-current"], cwd=repo_path)
    branch = (result.stdout or "").strip()
    return branch or "main"


def has_origin_remote(repo_path: Path) -> bool:
    """判断是否已配置 origin。"""
    result = run_command(["git", "remote", "get-url", "origin"], cwd=repo_path, check=False)
    return result.returncode == 0


def logout_new_account_if_requested(new_login: str, original_active_login: str | None) -> None:
    """脚本结束后按用户选择退出本次新登录账号。"""
    print_header("账号清理")
    if not prompt_yes_no(f"是否删除本次新登录的 gh 账号信息：{new_login}", default=False):
        print("已保留本次登录的账号信息。")
        return

    accounts = get_accounts()
    existing_logins = {account.login for account in accounts}
    if new_login not in existing_logins:
        print("未检测到该账号仍处于登录状态，跳过清理。")
        return

    if original_active_login and original_active_login != new_login and original_active_login in existing_logins:
        run_interactive(["gh", "auth", "switch", "--hostname", "github.com", "--user", original_active_login])

    run_interactive(["gh", "auth", "logout", "--hostname", "github.com", "--user", new_login])
    print(f"已删除账号 {new_login} 的本地 gh 登录信息。")


def create_or_push_remote(repo_path: Path, repo_name: str, visibility: str) -> None:
    """创建远程仓库或直接推送到现有 origin。"""
    if not has_head_commit(repo_path):
        raise CommandError("当前仓库还没有任何提交，无法创建远程仓库并推送。")

    branch = get_current_branch(repo_path)
    if has_origin_remote(repo_path):
        print("检测到已存在 origin，直接推送当前分支。")
        run_command(["git", "push", "-u", "origin", branch], cwd=repo_path, capture_output=False)
        return

    visibility_flag = f"--{visibility}"
    run_command(
        [
            "gh",
            "repo",
            "create",
            repo_name,
            visibility_flag,
            "--source=.",
            "--remote=origin",
            "--push",
        ],
        cwd=repo_path,
        capture_output=False,
    )


def print_summary(repo_path: Path, profile: GitHubProfile, repo_name: str, visibility: str) -> None:
    """执行前汇总关键参数。"""
    print_header("执行摘要")
    print(f"目标目录: {repo_path}")
    print(f"活动账号: {profile.login}")
    print(f"提交用户名: {profile.commit_name}")
    print(f"提交邮箱: {profile.commit_email}")
    print(f"远程仓库名: {repo_name}")
    print(f"远程仓库可见性: {visibility}")


def main() -> int:
    """主流程。"""
    login_result: LoginResult | None = None
    original_active_login: str | None = None
    try:
        print_header("环境检查")
        ensure_tool_exists("git")
        ensure_tool_exists("gh")

        repo_path = resolve_repo_path()
        try:
            original_active_login = get_active_account().login
        except CommandError:
            original_active_login = None

        login_result = login_or_switch_account()
        account = login_result.account
        profile = get_profile()
        if profile.login != account.login:
            print(f"警告：gh 活动账号从 {account.login} 变为 {profile.login}，将以当前活动账号为准。")

        default_repo_name = repo_path.name
        repo_name = prompt_text("请输入远程仓库名", default=default_repo_name)
        visibility_index = prompt_choice("请选择仓库可见性：", ["public", "private"], default_index=0)
        visibility = ["public", "private"][visibility_index]
        default_message = "Initial commit"

        print_summary(repo_path, profile, repo_name, visibility)
        if not prompt_yes_no("确认开始执行以上操作吗？", default=True):
            print("已取消。")
            return 0

        print_header("执行中")
        init_repo_if_needed(repo_path)
        configure_local_identity(repo_path, profile)
        setup_lfs_if_needed(repo_path)
        ensure_commit(repo_path, default_message)
        create_or_push_remote(repo_path, repo_name, visibility)

        print_header("完成")
        print("仓库初始化、提交和推送已完成。")
        print(f"目录: {repo_path}")
        print(f"账号: {profile.login}")
        print(f"提交身份: {profile.commit_name} <{profile.commit_email}>")
        return 0

    except KeyboardInterrupt:
        print("\n操作已被用户中断。")
        return 1
    except CommandError as exc:
        print(f"\n执行失败：\n{exc}")
        return 1
    except FileNotFoundError as exc:
        print(f"\n执行失败：未找到命令或文件：{exc}")
        return 1
    finally:
        if login_result and login_result.newly_logged_in:
            try:
                logout_new_account_if_requested(login_result.account.login, original_active_login)
            except Exception as exc:  # noqa: BLE001
                print(f"\n账号清理失败：{exc}")


if __name__ == "__main__":
    sys.exit(main())

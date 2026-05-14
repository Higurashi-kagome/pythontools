from __future__ import annotations

import ctypes
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path


OPENSSH_CAPABILITY_NAME = 'OpenSSH.Server~~~~0.0.1.0'


class CommandError(RuntimeError):
    pass


@dataclass
class AuthorizedKeyResult:
    added: bool
    path: Path | None
    reason: str


def run_command(
    command: list[str],
    *,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        text=True,
        encoding='utf-8',
        errors='replace',
        capture_output=capture_output,
    )
    if check and result.returncode != 0:
        stderr = (result.stderr or result.stdout or '').strip()
        raise CommandError(f'命令执行失败：{" ".join(command)}\n{stderr}')
    return result


def run_powershell(
    script: str,
    *,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        ['powershell', '-NoLogo', '-NoProfile', '-Command', script],
        capture_output=capture_output,
    )


def add_authorized_key_if_missing(
    public_key: str,
    home_directory: Path | None = None,
) -> AuthorizedKeyResult:
    normalized_public_key = public_key.strip()
    if not normalized_public_key:
        return AuthorizedKeyResult(added=False, path=None, reason='EmptyInput')

    resolved_home_directory = home_directory or Path.home()
    ssh_directory_path = resolved_home_directory / '.ssh'
    authorized_keys_path = ssh_directory_path / 'authorized_keys'

    ssh_directory_path.mkdir(parents=True, exist_ok=True)
    if not authorized_keys_path.exists():
        authorized_keys_path.touch()

    existing_lines: list[str] = []
    if authorized_keys_path.stat().st_size > 0:
        existing_lines = [
            line.strip()
            for line in authorized_keys_path.read_text(encoding='utf-8').splitlines()
            if line.strip()
        ]

    if normalized_public_key in existing_lines:
        return AuthorizedKeyResult(added=False, path=authorized_keys_path, reason='AlreadyExists')

    with authorized_keys_path.open('a', encoding='utf-8', newline='\n') as file:
        file.write(f'{normalized_public_key}\n')

    return AuthorizedKeyResult(added=True, path=authorized_keys_path, reason='Added')


def has_cpolar_tcp_22_process() -> bool:
    script = """
    $process = Get-CimInstance -ClassName Win32_Process |
        Where-Object {
            $_.Name -match '^cpolar(\\.exe)?$' -and
            $_.CommandLine -match '(?i)\\btcp\\s+22\\b'
        } |
        Select-Object -First 1
    if ($process) { 'True' } else { 'False' }
    """
    result = run_powershell(script)
    return (result.stdout or '').strip().lower() == 'true'


def ensure_cpolar_tunnel() -> None:
    cpolar_path = shutil.which('cpolar')
    if not cpolar_path:
        webbrowser.open('https://www.cpolar.com/')
        return

    if has_cpolar_tcp_22_process():
        return

    run_command([cpolar_path, 'tcp', '22'], capture_output=False)


def is_running_as_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def ensure_openssh_server_installed() -> None:
    state_result = run_powershell(
        f"(Get-WindowsCapability -Online -Name '{OPENSSH_CAPABILITY_NAME}').State",
    )
    if (state_result.stdout or '').strip() == 'Installed':
        return

    run_powershell(
        f"Add-WindowsCapability -Online -Name '{OPENSSH_CAPABILITY_NAME}'",
        capture_output=False,
    )


def ensure_sshd_service() -> None:
    service_status_result = run_powershell("(Get-Service -Name 'sshd').Status")
    if (service_status_result.stdout or '').strip() != 'Running':
        run_powershell("Start-Service -Name 'sshd'", capture_output=False)

    run_powershell("Set-Service -Name 'sshd' -StartupType Automatic", capture_output=False)


def ensure_sshd_firewall_rule() -> None:
    firewall_rule_result = run_powershell(
        "if (Get-NetFirewallRule -Name 'sshd' -ErrorAction SilentlyContinue) { 'True' } else { 'False' }",
    )
    if (firewall_rule_result.stdout or '').strip() == 'True':
        return

    run_powershell(
        "New-NetFirewallRule -Name 'sshd' -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22",
        capture_output=False,
    )


def main() -> int:
    try:
        if not is_running_as_admin():
            print('请以管理员身份运行此脚本。')
            return 1

        ensure_openssh_server_installed()
        ensure_sshd_service()
        ensure_sshd_firewall_rule()

        public_key = input('请输入要授权的 SSH 公钥，直接回车可跳过: ')
        authorized_key_result = add_authorized_key_if_missing(public_key)
        if authorized_key_result.reason == 'Added':
            print(f'公钥已写入：{authorized_key_result.path}')
        elif authorized_key_result.reason == 'AlreadyExists':
            print(f'公钥已存在，无需重复写入：{authorized_key_result.path}')
        else:
            print('未输入公钥，跳过 authorized_keys 写入。')

        ensure_cpolar_tunnel()
        print('SSH 服务配置完成。')
        return 0
    except CommandError as exc:
        print(f'执行失败：\n{exc}')
        return 1
    except KeyboardInterrupt:
        print('\n操作已取消。')
        return 1


if __name__ == '__main__':
    sys.exit(main())

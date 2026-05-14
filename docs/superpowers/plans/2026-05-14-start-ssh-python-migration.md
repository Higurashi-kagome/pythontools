# Start SSH Python Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在`others/start_ssh.py`中实现 PowerShell 版 Windows SSH 开通脚本的 Python 等价迁移，并补上可自动化验证的核心测试。

**Architecture:** 使用单文件 Python 脚本作为编排层，所有 Windows 系统配置操作通过`subprocess`调用 PowerShell 或系统命令执行。把最稳定的公钥文件逻辑和大部分流程分支提取为可单测函数，通过`unittest.mock`隔离系统副作用。README 只补充一条工具说明，不做额外产品化扩展。

**Tech Stack:** Python 标准库，`subprocess`，`pathlib`，`tempfile`，`ctypes`，`shutil`，`webbrowser`，`unittest`

---

### 文件结构

- Create: `others/start_ssh.py`
  责任：实现管理员检查、PowerShell 命令执行、OpenSSH 安装、`sshd` 服务配置、防火墙规则、公钥写入、`cpolar` 处理和主流程。

- Create: `tests/others/test_start_ssh.py`
  责任：覆盖公钥写入逻辑、命令执行错误分支、`cpolar` 分支行为和主流程编排顺序。

- Modify: `README.md`
  责任：补充 `others/start_ssh.py` 的用途说明，保持根目录工具索引完整。

### Task 1: 搭建公钥写入测试与最小脚本骨架

**Files:**

- Create: `tests/others/test_start_ssh.py`

- Create: `others/start_ssh.py`

- [ ] **Step 1: 先写公钥写入的失败测试**

    ```python
    import tempfile
    import unittest
    from pathlib import Path

    from others.start_ssh import add_authorized_key_if_missing


    class TestAuthorizedKeys(unittest.TestCase):
        def test_adds_new_key_and_creates_authorized_keys_file(self) -> None:
            public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey comment@example'
            with tempfile.TemporaryDirectory() as temp_dir:
                home_directory = Path(temp_dir)
                result = add_authorized_key_if_missing(public_key, home_directory)
                authorized_keys_path = home_directory / '.ssh' / 'authorized_keys'

                self.assertTrue(result.added)
                self.assertEqual(result.reason, 'Added')
                self.assertEqual(result.path, authorized_keys_path)
                self.assertTrue(authorized_keys_path.exists())
                self.assertEqual(authorized_keys_path.read_text(encoding='utf-8').strip(), public_key)

        def test_returns_empty_input_for_blank_key(self) -> None:
            with tempfile.TemporaryDirectory() as temp_dir:
                result = add_authorized_key_if_missing('   ', Path(temp_dir))

            self.assertFalse(result.added)
            self.assertEqual(result.reason, 'EmptyInput')
            self.assertIsNone(result.path)


    if __name__ == '__main__':
        unittest.main()
    ```

- [ ] **Step 2: 运行测试，确认当前必然失败**

    Run: `python -m unittest tests.others.test_start_ssh -v`

    Expected: FAIL，提示`ModuleNotFoundError`或`ImportError`，因为`others/start_ssh.py`尚未存在。

- [ ] **Step 3: 写最小实现，让基础测试通过**

    ```python
    from __future__ import annotations

    from dataclasses import dataclass
    from pathlib import Path


    @dataclass
    class AuthorizedKeyResult:
        added: bool
        path: Path | None
        reason: str


    def add_authorized_key_if_missing(public_key: str, home_directory: Path | None = None) -> AuthorizedKeyResult:
        normalized_public_key = public_key.strip()
        if not normalized_public_key:
            return AuthorizedKeyResult(added=False, path=None, reason='EmptyInput')

        resolved_home = home_directory or Path.home()
        ssh_directory = resolved_home / '.ssh'
        authorized_keys_path = ssh_directory / 'authorized_keys'

        ssh_directory.mkdir(parents=True, exist_ok=True)
        if not authorized_keys_path.exists():
            authorized_keys_path.touch()

        existing_lines = []
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
    ```

- [ ] **Step 4: 再次运行测试，确认基础行为通过**

    Run: `python -m unittest tests.others.test_start_ssh -v`

    Expected: PASS，`test_adds_new_key_and_creates_authorized_keys_file`和`test_returns_empty_input_for_blank_key`通过。

- [ ] **Step 5: 提交这一小步**

    ```bash
    git add others/start_ssh.py tests/others/test_start_ssh.py
    git commit -m "feat(others): scaffold start ssh key writer"
    ```

### Task 2: 完成公钥去重与首尾空白处理

**Files:**

- Modify: `tests/others/test_start_ssh.py`

- Modify: `others/start_ssh.py`

- [ ] **Step 1: 增加重复公钥不重复写入的失败测试**

    ```python
    def test_does_not_write_duplicate_key_after_trimming(self) -> None:
        public_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey comment@example'
        with tempfile.TemporaryDirectory() as temp_dir:
            home_directory = Path(temp_dir)
            first_result = add_authorized_key_if_missing(public_key, home_directory)
            second_result = add_authorized_key_if_missing(f'  {public_key}  ', home_directory)
            authorized_keys_path = home_directory / '.ssh' / 'authorized_keys'
            file_lines = authorized_keys_path.read_text(encoding='utf-8').splitlines()

        self.assertTrue(first_result.added)
        self.assertFalse(second_result.added)
        self.assertEqual(second_result.reason, 'AlreadyExists')
        self.assertEqual(file_lines, [public_key])
    ```

- [ ] **Step 2: 运行新增测试，确认它先失败**

    Run: `python -m unittest tests.others.test_start_ssh.TestAuthorizedKeys.test_does_not_write_duplicate_key_after_trimming -v`

    Expected: 如果当前实现还没有稳定去重，会 FAIL，表现为文件中有两行相同 key 或返回值不符合预期。

- [ ] **Step 3: 将公钥处理函数整理为稳定的去重实现**

    ```python
    def _read_existing_keys(authorized_keys_path: Path) -> list[str]:
        if not authorized_keys_path.exists() or authorized_keys_path.stat().st_size == 0:
            return []

        return [
            line.strip()
            for line in authorized_keys_path.read_text(encoding='utf-8').splitlines()
            if line.strip()
        ]


    def add_authorized_key_if_missing(public_key: str, home_directory: Path | None = None) -> AuthorizedKeyResult:
        normalized_public_key = public_key.strip()
        if not normalized_public_key:
            return AuthorizedKeyResult(added=False, path=None, reason='EmptyInput')

        resolved_home = home_directory or Path.home()
        ssh_directory = resolved_home / '.ssh'
        authorized_keys_path = ssh_directory / 'authorized_keys'

        ssh_directory.mkdir(parents=True, exist_ok=True)
        authorized_keys_path.touch(exist_ok=True)

        existing_keys = _read_existing_keys(authorized_keys_path)
        if normalized_public_key in existing_keys:
            return AuthorizedKeyResult(added=False, path=authorized_keys_path, reason='AlreadyExists')

        with authorized_keys_path.open('a', encoding='utf-8', newline='\n') as file:
            file.write(f'{normalized_public_key}\n')

        return AuthorizedKeyResult(added=True, path=authorized_keys_path, reason='Added')
    ```

- [ ] **Step 4: 运行全部公钥测试，确认现在都通过**

    Run: `python -m unittest tests.others.test_start_ssh.TestAuthorizedKeys -v`

    Expected: PASS，三个公钥相关测试全部通过。

- [ ] **Step 5: 提交这一小步**

    ```bash
    git add others/start_ssh.py tests/others/test_start_ssh.py
    git commit -m "test(others): cover authorized_keys deduplication"
    ```

### Task 3: 增加命令封装和 cpolar 分支测试

**Files:**

- Modify: `tests/others/test_start_ssh.py`

- Modify: `others/start_ssh.py`

- [ ] **Step 1: 先写命令封装与 cpolar 的失败测试**

    ```python
    from subprocess import CompletedProcess
    from unittest.mock import patch

    from others.start_ssh import CommandError, ensure_cpolar_tunnel, run_powershell


    class TestCommandAndCpolar(unittest.TestCase):
        def test_run_powershell_raises_command_error_when_command_fails(self) -> None:
            with patch('others.start_ssh.subprocess.run') as mock_run:
                mock_run.return_value = CompletedProcess(
                    args=['powershell', '-Command', 'broken'],
                    returncode=1,
                    stdout='',
                    stderr='boom',
                )

                with self.assertRaises(CommandError) as context:
                    run_powershell('broken')

            self.assertIn('boom', str(context.exception))

        def test_ensure_cpolar_tunnel_opens_website_when_command_missing(self) -> None:
            with patch('others.start_ssh.shutil.which', return_value=None), patch('others.start_ssh.webbrowser.open') as mock_open:
                ensure_cpolar_tunnel()

            mock_open.assert_called_once_with('https://www.cpolar.com/')

        def test_ensure_cpolar_tunnel_starts_tcp_22_when_not_running(self) -> None:
            with patch('others.start_ssh.shutil.which', return_value='C:/Tools/cpolar.exe'), \
                 patch('others.start_ssh.has_cpolar_tcp_22_process', return_value=False), \
                 patch('others.start_ssh.run_command') as mock_run_command:
                ensure_cpolar_tunnel()

            mock_run_command.assert_called_once_with(['C:/Tools/cpolar.exe', 'tcp', '22'], capture_output=False)
    ```

- [ ] **Step 2: 运行这一组测试，确认它们先失败**

    Run: `python -m unittest tests.others.test_start_ssh.TestCommandAndCpolar -v`

    Expected: FAIL，提示`run_powershell`、`ensure_cpolar_tunnel`、`CommandError`或相关依赖尚未定义。

- [ ] **Step 3: 实现命令封装与 cpolar 逻辑**

    ```python
    import shutil
    import subprocess
    import webbrowser


    class CommandError(RuntimeError):
        pass


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


    def run_powershell(script: str, *, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
        return run_command(
            ['powershell', '-NoLogo', '-NoProfile', '-Command', script],
            capture_output=capture_output,
        )


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
    ```

- [ ] **Step 4: 重新运行测试，确认命令层和 cpolar 行为通过**

    Run: `python -m unittest tests.others.test_start_ssh.TestCommandAndCpolar -v`

    Expected: PASS，三个测试都通过。

- [ ] **Step 5: 提交这一小步**

    ```bash
    git add others/start_ssh.py tests/others/test_start_ssh.py
    git commit -m "feat(others): add command wrapper and cpolar flow"
    ```

### Task 4: 实现 Windows SSH 配置流程和主入口

**Files:**

- Modify: `tests/others/test_start_ssh.py`

- Modify: `others/start_ssh.py`

- [ ] **Step 1: 先写主流程编排和管理员分支的失败测试**

    ```python
    from unittest.mock import MagicMock, patch

    from others.start_ssh import main


    class TestMainFlow(unittest.TestCase):
        def test_main_returns_non_zero_when_not_running_as_admin(self) -> None:
            with patch('others.start_ssh.is_running_as_admin', return_value=False), patch('builtins.print') as mock_print:
                exit_code = main()

            self.assertEqual(exit_code, 1)
            mock_print.assert_any_call('请以管理员身份运行此脚本。')

        def test_main_runs_setup_sequence_in_order(self) -> None:
            with patch('others.start_ssh.is_running_as_admin', return_value=True), \
                 patch('others.start_ssh.ensure_openssh_server_installed') as mock_capability, \
                 patch('others.start_ssh.ensure_sshd_service') as mock_service, \
                 patch('others.start_ssh.ensure_sshd_firewall_rule') as mock_firewall, \
                 patch('others.start_ssh.add_authorized_key_if_missing', return_value=MagicMock(reason='EmptyInput', path=None)) as mock_add_key, \
                 patch('others.start_ssh.ensure_cpolar_tunnel') as mock_cpolar, \
                 patch('builtins.input', return_value=''), \
                 patch('builtins.print'):
                exit_code = main()

            self.assertEqual(exit_code, 0)
            mock_capability.assert_called_once_with()
            mock_service.assert_called_once_with()
            mock_firewall.assert_called_once_with()
            mock_add_key.assert_called_once()
            mock_cpolar.assert_called_once_with()
    ```

- [ ] **Step 2: 运行主流程测试，确认它先失败**

    Run: `python -m unittest tests.others.test_start_ssh.TestMainFlow -v`

    Expected: FAIL，提示管理员检查、SSH 配置函数或 `main()` 尚未完整实现。

- [ ] **Step 3: 完成系统配置函数和主流程**

    ```python
    import ctypes
    import sys


    OPENSSH_CAPABILITY_NAME = 'OpenSSH.Server~~~~0.0.1.0'


    def is_running_as_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except OSError:
            return False


    def ensure_openssh_server_installed() -> None:
        state_script = f"(Get-WindowsCapability -Online -Name '{OPENSSH_CAPABILITY_NAME}').State"
        result = run_powershell(state_script)
        if (result.stdout or '').strip() == 'Installed':
            return

        run_powershell(
            f"Add-WindowsCapability -Online -Name '{OPENSSH_CAPABILITY_NAME}'",
            capture_output=False,
        )


    def ensure_sshd_service() -> None:
        status_result = run_powershell("(Get-Service -Name 'sshd').Status")
        if (status_result.stdout or '').strip() != 'Running':
            run_powershell("Start-Service -Name 'sshd'", capture_output=False)

        run_powershell("Set-Service -Name 'sshd' -StartupType Automatic", capture_output=False)


    def ensure_sshd_firewall_rule() -> None:
        check_script = "if (Get-NetFirewallRule -Name 'sshd' -ErrorAction SilentlyContinue) { 'True' } else { 'False' }"
        result = run_powershell(check_script)
        if (result.stdout or '').strip() == 'True':
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
            result = add_authorized_key_if_missing(public_key)
            if result.reason == 'Added':
                print(f'公钥已写入：{result.path}')
            elif result.reason == 'AlreadyExists':
                print(f'公钥已存在，无需重复写入：{result.path}')
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
    ```

- [ ] **Step 4: 运行完整测试集，确认当前脚本流程通过**

    Run: `python -m unittest tests.others.test_start_ssh -v`

    Expected: PASS，公钥逻辑、命令层、`cpolar` 分支和主流程测试全部通过。

- [ ] **Step 5: 提交这一小步**

    ```bash
    git add others/start_ssh.py tests/others/test_start_ssh.py
    git commit -m "feat(others): port windows ssh bootstrap to python"
    ```

### Task 5: 补充 README 说明并完成人工验证

**Files:**

- Modify: `README.md`

- [ ] **Step 1: 在 README 的工具列表中补充新脚本条目**

    ```markdown
    | [Windows SSH 开通脚本](others/start_ssh.py)                    | 交互式安装并启动 OpenSSH Server、配置 `sshd` 服务和防火墙、写入授权公钥，并在可用时自动启动 `cpolar tcp 22` |
    ```

- [ ] **Step 2: 运行完整自动化验证**

    Run: `python -m unittest tests.others.test_start_ssh -v`

    Expected: PASS，测试输出为 0 failed。

- [ ] **Step 3: 以管理员身份做一次手工验证**

    Run: `python others/start_ssh.py`

    Expected:

    - 非管理员场景：提示“请以管理员身份运行此脚本。”

    - 管理员场景：能顺序完成 OpenSSH 检查、`sshd` 启动、防火墙规则检查、公钥写入和 `cpolar` 处理

    - 如果本机未安装 `cpolar`：默认浏览器打开`https://www.cpolar.com/`

- [ ] **Step 4: 提交这一小步**

    ```bash
    git add README.md others/start_ssh.py tests/others/test_start_ssh.py
    git commit -m "docs: add start ssh tool entry"
    ```

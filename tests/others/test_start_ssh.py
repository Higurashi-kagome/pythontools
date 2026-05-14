import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

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


class TestCommandAndCpolar(unittest.TestCase):
    def test_run_powershell_raises_command_error_when_command_fails(self) -> None:
        from others.start_ssh import CommandError, run_powershell

        with patch('others.start_ssh.subprocess.run') as mock_run:
            mock_run.return_value = CompletedProcess(
                args=['powershell', '-NoLogo', '-NoProfile', '-Command', 'broken'],
                returncode=1,
                stdout='',
                stderr='boom',
            )

            with self.assertRaises(CommandError) as context:
                run_powershell('broken')

        self.assertIn('boom', str(context.exception))

    def test_ensure_cpolar_tunnel_opens_website_when_command_missing(self) -> None:
        from others.start_ssh import ensure_cpolar_tunnel

        with patch('others.start_ssh.shutil.which', return_value=None), patch('others.start_ssh.webbrowser.open') as mock_open:
            ensure_cpolar_tunnel()

        mock_open.assert_called_once_with('https://www.cpolar.com/')

    def test_ensure_cpolar_tunnel_starts_tcp_22_when_not_running(self) -> None:
        from others.start_ssh import ensure_cpolar_tunnel

        with patch('others.start_ssh.shutil.which', return_value='C:/Tools/cpolar.exe'), \
             patch('others.start_ssh.has_cpolar_tcp_22_process', return_value=False), \
             patch('others.start_ssh.run_command') as mock_run_command:
            ensure_cpolar_tunnel()

        mock_run_command.assert_called_once_with(['C:/Tools/cpolar.exe', 'tcp', '22'], capture_output=False)


class TestMainFlow(unittest.TestCase):
    def test_main_returns_non_zero_when_not_running_as_admin(self) -> None:
        from others.start_ssh import main

        with patch('others.start_ssh.is_running_as_admin', return_value=False), patch('builtins.print') as mock_print:
            exit_code = main()

        self.assertEqual(exit_code, 1)
        mock_print.assert_any_call('请以管理员身份运行此脚本。')

    def test_main_runs_setup_sequence_in_order(self) -> None:
        from others.start_ssh import main

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
        mock_add_key.assert_called_once_with('')
        mock_cpolar.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()

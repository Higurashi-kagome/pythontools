import unittest
from subprocess import CompletedProcess
from unittest.mock import patch

from others.gh_account_manager import (
    CommandError,
    login_account,
    main,
    parse_accounts_payload,
    read_accounts,
    switch_account,
    logout_account,
)


class TestAccountParsing(unittest.TestCase):
    def test_parse_accounts_payload_reads_github_accounts(self) -> None:
        payload = {
            'hosts': {
                'github.com': [
                    {
                        'login': 'alice',
                        'active': True,
                        'state': 'success',
                        'tokenSource': 'keyring',
                        'gitProtocol': 'https',
                        'scopes': 'repo',
                    },
                    {
                        'login': 'bob',
                        'active': False,
                        'state': 'expired',
                        'error': 'token invalid',
                    },
                ],
                'github.example.com': [
                    {'login': 'ignored', 'active': True, 'state': 'success'},
                ],
            },
        }

        accounts = parse_accounts_payload(payload)

        self.assertEqual([account.login for account in accounts], ['alice', 'bob'])
        self.assertTrue(accounts[0].active)
        self.assertEqual(accounts[1].error, 'token invalid')

    def test_read_accounts_requests_github_status_json(self) -> None:
        status_json = '{"hosts":{"github.com":[{"login":"alice","active":true,"state":"success"}]}}'

        def fake_runner(command: list[str], capture_output: bool = True) -> CompletedProcess[str]:
            self.assertEqual(
                command,
                ['gh', 'auth', 'status', '--hostname', 'github.com', '--json', 'hosts'],
            )
            self.assertTrue(capture_output)
            return CompletedProcess(command, 0, stdout=status_json, stderr='')

        accounts = read_accounts(command_runner=fake_runner)

        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].login, 'alice')


class TestGhCommands(unittest.TestCase):
    def test_switch_account_calls_gh_auth_switch(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(command: list[str], capture_output: bool = True) -> CompletedProcess[str]:
            calls.append(command)
            return CompletedProcess(command, 0, stdout='', stderr='')

        switch_account('alice', command_runner=fake_runner)

        self.assertEqual(
            calls,
            [['gh', 'auth', 'switch', '--hostname', 'github.com', '--user', 'alice']],
        )

    def test_logout_account_calls_gh_auth_logout(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(command: list[str], capture_output: bool = True) -> CompletedProcess[str]:
            calls.append(command)
            return CompletedProcess(command, 0, stdout='', stderr='')

        logout_account('alice', command_runner=fake_runner)

        self.assertEqual(
            calls,
            [['gh', 'auth', 'logout', '--hostname', 'github.com', '--user', 'alice']],
        )

    def test_login_account_uses_browser_login_flow(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(command: list[str]) -> CompletedProcess[str]:
            calls.append(command)
            return CompletedProcess(command, 0, stdout='', stderr='')

        login_account(command_runner=fake_runner)

        self.assertEqual(
            calls,
            [[
                'gh',
                'auth',
                'login',
                '--hostname',
                'github.com',
                '--git-protocol',
                'https',
                '--web',
                '--skip-ssh-key',
            ]],
        )


class TestMain(unittest.TestCase):
    def test_main_returns_non_zero_when_questionary_missing(self) -> None:
        with patch('others.gh_account_manager.ensure_tool_exists'), \
             patch('others.gh_account_manager.questionary', None), \
             patch('builtins.print') as mock_print:
            exit_code = main()

        self.assertEqual(exit_code, 1)
        mock_print.assert_any_call('缺少依赖 questionary，请先执行 `pip install -r requirements.txt`。')

    def test_read_accounts_raises_command_error_for_invalid_json(self) -> None:
        def fake_runner(command: list[str], capture_output: bool = True) -> CompletedProcess[str]:
            return CompletedProcess(command, 0, stdout='not-json', stderr='')

        with self.assertRaises(CommandError):
            read_accounts(command_runner=fake_runner)


if __name__ == '__main__':
    unittest.main()

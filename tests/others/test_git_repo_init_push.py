import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from others.git_repo_init_push import (
    Account,
    CommandError,
    Profile,
    build_lfs_patterns,
    create_gitlab_remote,
    ensure_commit,
    gitlab_project_exists,
    get_gitlab_namespace_id,
    get_gitlab_namespaces,
    get_visibility_options,
    parse_github_accounts,
    parse_gitlab_accounts,
    resolve_repo_path,
    resolve_namespace,
    resolve_gitlab_commit_email,
)


class TestPureHelpers(unittest.TestCase):
    def test_resolve_repo_path_uses_argument_without_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('others.git_repo_init_push.prompt_text') as mock_prompt:
                repo_path = resolve_repo_path(temp_dir)

        self.assertEqual(repo_path, Path(temp_dir))
        mock_prompt.assert_not_called()

    def test_resolve_repo_path_rejects_invalid_argument(self) -> None:
        with self.assertRaises(CommandError):
            resolve_repo_path('missing-repository-directory')

    def test_ensure_commit_can_skip_workspace_changes(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            calls.append(command)
            if command == ['git', 'status', '--short']:
                return CompletedProcess(command, 0, stdout=' M file.txt\n', stderr='')
            return CompletedProcess(command, 0, stdout='', stderr='')

        with patch('others.git_repo_init_push.prompt_yes_no', return_value=False) as mock_prompt:
            ensure_commit(Path('.'), 'Initial commit', command_runner=fake_runner)

        mock_prompt.assert_called_once_with('是否提交当前工作区改动？', default=True)
        self.assertEqual(calls, [['git', 'status', '--short']])

    def test_build_lfs_patterns_groups_suffixes_and_plain_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            zip_file = repo_path / 'archive.zip'
            nested_plain = repo_path / 'assets' / 'bundle'
            nested_plain.parent.mkdir(parents=True, exist_ok=True)
            zip_file.write_text('zip', encoding='utf-8')
            nested_plain.write_text('plain', encoding='utf-8')

            patterns = build_lfs_patterns(repo_path, [nested_plain, zip_file])

        self.assertEqual(patterns, ['*.zip', 'assets/bundle'])

    def test_get_visibility_options_returns_internal_for_gitlab(self) -> None:
        self.assertEqual(get_visibility_options('github'), ['public', 'private'])
        self.assertEqual(get_visibility_options('gitlab'), ['public', 'internal', 'private'])

    def test_parse_github_accounts_reads_active_login(self) -> None:
        status_text = '''
Logged in to github.com account alice (keyring)
  - Active account: true
Logged in to github.com account bob (keyring)
  - Active account: false
'''

        accounts = parse_github_accounts(status_text)

        self.assertEqual([account.login for account in accounts], ['alice', 'bob'])
        self.assertTrue(accounts[0].active)
        self.assertFalse(accounts[1].active)
        self.assertEqual(accounts[0].host, 'github.com')

    def test_parse_gitlab_accounts_reads_hostname_and_active_flag(self) -> None:
        status_text = '''
gitlab.com
  x gitlab.com: api call failed
  ✓ Logged in to gitlab.com as alice
  ✓ API calls for gitlab.com are made as alice
self.example.com
  ✓ Logged in to self.example.com as bob
  ✓ API calls for self.example.com are made as bob
'''

        accounts = parse_gitlab_accounts(status_text, 'self.example.com')

        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0], Account(login='alice', active=False, host='gitlab.com'))
        self.assertEqual(accounts[1], Account(login='bob', active=True, host='self.example.com'))


class TestGitLabRemote(unittest.TestCase):
    def test_gitlab_project_exists_checks_project_endpoint(self) -> None:
        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            self.assertEqual(command, ['glab', 'api', 'projects/goofish-code%2Ftripbook-portfolio', '--hostname', 'gitlab.com'])
            self.assertFalse(check)
            return CompletedProcess(
                command,
                0,
                stdout='{"id": 123, "path_with_namespace": "goofish-code/tripbook-portfolio"}',
                stderr='',
            )

        exists = gitlab_project_exists('gitlab.com', 'goofish-code', 'tripbook-portfolio', command_runner=fake_runner)

        self.assertTrue(exists)

    def test_gitlab_project_exists_returns_false_for_non_project_json(self) -> None:
        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            return CompletedProcess(command, 0, stdout='{"message":"404 Project Not Found"}', stderr='')

        exists = gitlab_project_exists('gitlab.com', 'goofish-code', 'tripbook-portfolio', command_runner=fake_runner)

        self.assertFalse(exists)

    def test_get_gitlab_namespace_id_reads_matching_full_path(self) -> None:
        payload = '''
[
  {"id": 1, "full_path": "alice"},
  {"id": 2, "full_path": "goofish-code"},
  {"id": 3, "full_path": "team/backend"}
]
'''

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            self.assertEqual(command, ['glab', 'api', 'namespaces?per_page=100', '--hostname', 'gitlab.com'])
            return CompletedProcess(command, 0, stdout=payload, stderr='')

        namespace_id = get_gitlab_namespace_id('gitlab.com', 'goofish-code', command_runner=fake_runner)

        self.assertEqual(namespace_id, 2)

    def test_gitlab_create_remote_uses_hostname_and_namespace(self) -> None:
        calls: list[tuple[list[str], dict[str, str] | None]] = []

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            calls.append((command, env))
            if command == ['glab', 'api', 'projects/team%2Fbackend%2Fdemo', '--hostname', 'self.example.com']:
                return CompletedProcess(command, 1, stdout='', stderr='404')
            return CompletedProcess(command, 0, stdout='', stderr='')

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            with patch('others.git_repo_init_push.has_head_commit', return_value=True), \
                 patch('others.git_repo_init_push.has_origin_remote', return_value=False), \
                 patch('others.git_repo_init_push.get_current_branch', return_value='main'), \
                 patch('others.git_repo_init_push.get_gitlab_namespace_id', return_value=77):
                create_gitlab_remote(
                    repo_path=repo_path,
                    repo_name='demo',
                    visibility='internal',
                    host='self.example.com',
                    namespace='team/backend',
                    command_runner=fake_runner,
                )

        self.assertEqual(len(calls), 4)
        self.assertEqual(
            calls[0][0],
            ['glab', 'api', 'projects/team%2Fbackend%2Fdemo', '--hostname', 'self.example.com'],
        )
        self.assertEqual(calls[0][1], {'GITLAB_HOST': 'self.example.com'})
        self.assertEqual(
            calls[1][0],
            ['git', 'remote', 'add', 'origin', 'https://self.example.com/team/backend/demo.git'],
        )
        self.assertEqual(
            calls[2][0],
            [
                'glab',
                'api',
                'projects',
                '--hostname',
                'self.example.com',
                '--method',
                'POST',
                '-f',
                'name=demo',
                '-f',
                'path=demo',
                '-F',
                'namespace_id=77',
                '-f',
                'visibility=internal',
            ],
        )
        self.assertEqual(calls[2][1], {'GITLAB_HOST': 'self.example.com'})
        self.assertEqual(calls[3][0], ['git', 'push', '-u', 'origin', 'main'])

    def test_gitlab_existing_ssh_origin_is_rewritten_to_https_before_push(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            calls.append(command)
            if command == ['glab', 'api', 'projects/goofish-code%2Ftripbook-portfolio', '--hostname', 'gitlab.com']:
                return CompletedProcess(
                    command,
                    0,
                    stdout='{"id": 123, "path_with_namespace": "goofish-code/tripbook-portfolio"}',
                    stderr='',
                )
            if command == ['git', 'remote', 'get-url', 'origin']:
                return CompletedProcess(command, 0, stdout='git@gitlab.com:goofish-code/tripbook-portfolio.git\n', stderr='')
            return CompletedProcess(command, 0, stdout='', stderr='')

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            with patch('others.git_repo_init_push.has_head_commit', return_value=True), \
                 patch('others.git_repo_init_push.has_origin_remote', return_value=True), \
                 patch('others.git_repo_init_push.get_current_branch', return_value='master'):
                create_gitlab_remote(
                    repo_path=repo_path,
                    repo_name='tripbook-portfolio',
                    visibility='private',
                    host='gitlab.com',
                    namespace='goofish-code',
                    command_runner=fake_runner,
                )

        self.assertEqual(
            calls,
            [
                ['glab', 'api', 'projects/goofish-code%2Ftripbook-portfolio', '--hostname', 'gitlab.com'],
                ['git', 'remote', 'get-url', 'origin'],
                ['git', 'remote', 'set-url', 'origin', 'https://gitlab.com/goofish-code/tripbook-portfolio.git'],
                ['git', 'push', '-u', 'origin', 'master'],
            ],
        )

    def test_gitlab_existing_origin_creates_missing_project_before_push(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            calls.append(command)
            if command == ['glab', 'api', 'projects/goofish-code%2Ftripbook-portfolio', '--hostname', 'gitlab.com']:
                return CompletedProcess(command, 1, stdout='', stderr='404')
            if command == ['git', 'remote', 'get-url', 'origin']:
                return CompletedProcess(command, 0, stdout='https://gitlab.com/goofish-code/tripbook-portfolio.git\n', stderr='')
            return CompletedProcess(command, 0, stdout='', stderr='')

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            with patch('others.git_repo_init_push.has_head_commit', return_value=True), \
                 patch('others.git_repo_init_push.has_origin_remote', return_value=True), \
                 patch('others.git_repo_init_push.get_current_branch', return_value='master'), \
                 patch('others.git_repo_init_push.get_gitlab_namespace_id', return_value=88):
                create_gitlab_remote(
                    repo_path=repo_path,
                    repo_name='tripbook-portfolio',
                    visibility='private',
                    host='gitlab.com',
                    namespace='goofish-code',
                    command_runner=fake_runner,
                )

        self.assertEqual(
            calls,
            [
                ['glab', 'api', 'projects/goofish-code%2Ftripbook-portfolio', '--hostname', 'gitlab.com'],
                ['git', 'remote', 'get-url', 'origin'],
                [
                    'glab',
                    'api',
                    'projects',
                    '--hostname',
                    'gitlab.com',
                    '--method',
                    'POST',
                    '-f',
                    'name=tripbook-portfolio',
                    '-f',
                    'path=tripbook-portfolio',
                    '-F',
                    'namespace_id=88',
                    '-f',
                    'visibility=private',
                ],
                ['git', 'push', '-u', 'origin', 'master'],
            ],
        )

    def test_get_gitlab_namespaces_reads_full_paths(self) -> None:
        payload = '''
[
  {"id": 1, "full_path": "alice"},
  {"id": 2, "full_path": "goofish-code"},
  {"id": 3, "full_path": "team/backend"}
]
'''

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            self.assertEqual(command, ['glab', 'api', 'namespaces?per_page=100', '--hostname', 'gitlab.com'])
            return CompletedProcess(command, 0, stdout=payload, stderr='')

        namespaces = get_gitlab_namespaces('gitlab.com', command_runner=fake_runner)

        self.assertEqual(namespaces, ['alice', 'goofish-code', 'team/backend'])

    def test_resolve_namespace_prefers_selectable_options(self) -> None:
        profile = Profile(
            login='alice',
            display_name='Alice',
            email='alice@example.com',
            commit_email_fallback=None,
        )

        with patch('others.git_repo_init_push.get_gitlab_namespaces', return_value=['goofish-code', 'team/backend']), \
             patch('others.git_repo_init_push.prompt_choice', return_value=0), \
             patch('others.git_repo_init_push.prompt_text') as mock_prompt_text:
            namespace = resolve_namespace('gitlab', profile, 'gitlab.com')

        self.assertEqual(namespace, 'goofish-code')
        mock_prompt_text.assert_not_called()


class TestGitLabCommitEmail(unittest.TestCase):
    def test_gitlab_commit_email_prefers_profile_email(self) -> None:
        profile = Profile(
            login='alice',
            display_name='Alice',
            email='alice@example.com',
            commit_email_fallback=None,
        )

        email = resolve_gitlab_commit_email(profile, Path('.'))

        self.assertEqual(email, 'alice@example.com')

    def test_gitlab_commit_email_falls_back_to_git_config_then_prompt(self) -> None:
        profile = Profile(
            login='alice',
            display_name='Alice',
            email=None,
            commit_email_fallback=None,
        )

        responses = {
            ('git', 'config', 'user.email'): CompletedProcess(['git'], 0, stdout='', stderr=''),
            ('git', 'config', '--global', 'user.email'): CompletedProcess(['git'], 0, stdout='global@example.com\n', stderr=''),
        }

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            key = tuple(command)
            result = responses.get(key)
            if result is None:
                raise AssertionError(f'Unexpected command: {command}')
            return result

        with tempfile.TemporaryDirectory() as temp_dir:
            email = resolve_gitlab_commit_email(
                profile,
                Path(temp_dir),
                command_runner=fake_runner,
                prompt_runner=lambda message, default=None, allow_empty=False: 'manual@example.com',
            )

        self.assertEqual(email, 'global@example.com')

    def test_gitlab_commit_email_prompts_when_git_config_missing(self) -> None:
        profile = Profile(
            login='alice',
            display_name='Alice',
            email=None,
            commit_email_fallback=None,
        )

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            return CompletedProcess(command, 1, stdout='', stderr='')

        with tempfile.TemporaryDirectory() as temp_dir:
            email = resolve_gitlab_commit_email(
                profile,
                Path(temp_dir),
                command_runner=fake_runner,
                prompt_runner=lambda message, default=None, allow_empty=False: 'manual@example.com',
            )

        self.assertEqual(email, 'manual@example.com')

    def test_gitlab_commit_email_raises_for_blank_manual_input(self) -> None:
        profile = Profile(
            login='alice',
            display_name='Alice',
            email=None,
            commit_email_fallback=None,
        )

        def fake_runner(
            command: list[str],
            cwd: Path | None = None,
            check: bool = True,
            capture_output: bool = True,
            env: dict[str, str] | None = None,
        ) -> CompletedProcess[str]:
            return CompletedProcess(command, 1, stdout='', stderr='')

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(CommandError):
                resolve_gitlab_commit_email(
                    profile,
                    Path(temp_dir),
                    command_runner=fake_runner,
                    prompt_runner=lambda message, default=None, allow_empty=False: '',
                )


if __name__ == '__main__':
    unittest.main()

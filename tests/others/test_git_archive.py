import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

from others.git_archive import archive_git_sources, main


class TestGitArchive(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ['git', '-C', str(repo), *args],
            check=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
        )

    def init_repo(self, repo: Path) -> None:
        repo.mkdir(parents=True, exist_ok=True)
        self.run_git(repo, 'init')
        self.run_git(repo, 'config', 'user.email', 'codex@example.invalid')
        self.run_git(repo, 'config', 'user.name', 'Codex')

    def commit_all(self, repo: Path, message: str) -> None:
        self.run_git(repo, 'add', '--all')
        self.run_git(repo, 'commit', '-m', message)

    def archive_names(self, archive_path: Path) -> set[str]:
        with ZipFile(archive_path) as archive:
            return set(archive.namelist())

    def test_untracked_files_are_opt_in_and_ignored_files_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            repo = base / 'repo'
            self.init_repo(repo)
            (repo / '.gitignore').write_text('ignored.txt\n', encoding='utf-8')
            (repo / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(repo, 'initial')
            (repo / 'untracked.txt').write_text('untracked', encoding='utf-8')
            (repo / 'ignored.txt').write_text('ignored', encoding='utf-8')

            tracked_archive = base / 'tracked.zip'
            archive_git_sources(repo, tracked_archive, include_git=False)
            tracked_names = self.archive_names(tracked_archive)
            self.assertIn('tracked.txt', tracked_names)
            self.assertNotIn('untracked.txt', tracked_names)

            complete_archive = base / 'complete.zip'
            archive_git_sources(
                repo,
                complete_archive,
                include_git=False,
                include_untracked=True,
            )
            complete_names = self.archive_names(complete_archive)
            self.assertIn('untracked.txt', complete_names)
            self.assertNotIn('ignored.txt', complete_names)

    def test_default_output_path_uses_repository_name_and_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            repo = base / 'project'
            self.init_repo(repo)
            (repo / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(repo, 'initial')
            (base / 'project.zip').write_text('existing', encoding='utf-8')
            (base / 'project-2.zip').write_text('existing', encoding='utf-8')

            archive_path = archive_git_sources(repo, include_git=False)

            self.assertEqual(archive_path, base / 'project-3.zip')
            self.assertIn('tracked.txt', self.archive_names(archive_path))

    def test_progress_callback_reports_archive_stages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            repo = base / 'repo'
            self.init_repo(repo)
            (repo / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(repo, 'initial')
            (repo / 'untracked.txt').write_text('untracked', encoding='utf-8')

            messages = []
            archive_path = base / 'progress.zip'
            archive_git_sources(
                repo,
                archive_path,
                include_untracked=True,
                on_progress=messages.append,
            )

            self.assertEqual(messages[0], '已发现 1 个待打包工作目录')
            self.assertTrue(any('复制 1 个已跟踪文件' in message for message in messages))
            self.assertTrue(any('复制 1 个未跟踪文件' in message for message in messages))
            self.assertTrue(any('复制 Git 元数据' in message for message in messages))
            self.assertEqual(messages[-1], f'打包完成: {archive_path}')

    def test_progress_option_passes_print_callback_to_archive(self) -> None:
        with mock.patch('others.git_archive.archive_git_sources') as archive:
            with mock.patch('builtins.print') as print_mock:
                with mock.patch(
                    'sys.argv',
                    ['git_archive.py', 'project'],
                ):
                    archive.return_value = Path('project.zip')
                    main()

        self.assertIs(archive.call_args.args[-1], print_mock)
        print_mock.assert_not_called()

    def test_no_progress_option_disables_print_callback(self) -> None:
        with mock.patch('others.git_archive.archive_git_sources') as archive:
            with mock.patch('builtins.print') as print_mock:
                with mock.patch(
                    'sys.argv',
                    ['git_archive.py', 'project', '--no-progress'],
                ):
                    archive.return_value = Path('project.zip')
                    main()

        self.assertIsNone(archive.call_args.args[-1])
        print_mock.assert_not_called()

    def test_nested_repositories_share_one_archive_without_crossing_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / 'root'
            nested = root / 'nested'
            self.init_repo(root)
            (root / 'root.txt').write_text('root', encoding='utf-8')
            self.commit_all(root, 'root')

            self.init_repo(nested)
            (nested / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(nested, 'nested')
            (nested / 'untracked.txt').write_text('untracked', encoding='utf-8')

            archive_path = base / 'nested.zip'
            archive_git_sources(
                root,
                archive_path,
                include_git=False,
                include_untracked=True,
            )
            names = self.archive_names(archive_path)
            self.assertIn('root.txt', names)
            self.assertIn('nested/tracked.txt', names)
            self.assertIn('nested/untracked.txt', names)
            self.assertNotIn('nested/.git/config', names)

    def test_external_worktree_is_archived_only_with_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / 'repo'
            worktree = base / 'outside' / 'feature'
            self.init_repo(root)
            (root / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(root, 'initial')
            worktree.parent.mkdir(parents=True)
            self.run_git(root, 'worktree', 'add', '-b', 'feature', str(worktree))
            (worktree / 'feature.txt').write_text('feature', encoding='utf-8')
            self.commit_all(worktree, 'feature')
            (root / 'root-untracked.txt').write_text('root', encoding='utf-8')
            (worktree / 'worktree-untracked.txt').write_text('worktree', encoding='utf-8')

            archive_path = base / 'with-worktree.zip'
            archive_git_sources(root, archive_path, include_untracked=True)
            names = self.archive_names(archive_path)
            prefix = f'__worktrees__/{root.name}/{worktree.name}/'
            self.assertIn(f'{prefix}tracked.txt', names)
            self.assertIn(f'{prefix}worktree-untracked.txt', names)
            self.assertIn(f'{prefix}.git', names)

            no_git_archive = base / 'without-worktree.zip'
            archive_git_sources(
                root,
                no_git_archive,
                include_git=False,
                include_untracked=True,
            )
            no_git_names = self.archive_names(no_git_archive)
            self.assertIn('root-untracked.txt', no_git_names)
            self.assertFalse(any(name.startswith('__worktrees__/') for name in no_git_names))

    def test_merged_external_worktree_is_skipped_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / 'repo'
            worktree = base / 'outside' / 'merged'
            self.init_repo(root)
            (root / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(root, 'initial')
            worktree.parent.mkdir(parents=True)
            self.run_git(root, 'worktree', 'add', '-b', 'merged', str(worktree))

            archive_path = base / 'default.zip'
            archive_git_sources(root, archive_path)
            names = self.archive_names(archive_path)
            prefix = f'__worktrees__/{root.name}/{worktree.name}/'
            self.assertFalse(any(name.startswith(prefix) for name in names))

            complete_archive = base / 'complete.zip'
            archive_git_sources(
                root,
                complete_archive,
                include_merged_worktrees=True,
            )
            complete_names = self.archive_names(complete_archive)
            self.assertIn(f'{prefix}tracked.txt', complete_names)

    def test_merged_worktree_inside_project_is_skipped_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / 'repo'
            worktree = root / 'worktrees' / 'merged'
            self.init_repo(root)
            (root / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(root, 'initial')
            worktree.parent.mkdir(parents=True)
            self.run_git(root, 'worktree', 'add', '-b', 'merged', str(worktree))

            archive_path = base / 'default.zip'
            archive_git_sources(root, archive_path)
            names = self.archive_names(archive_path)
            prefix = 'worktrees/merged/'
            self.assertFalse(any(name.startswith(prefix) for name in names))

            complete_archive = base / 'complete.zip'
            archive_git_sources(
                root,
                complete_archive,
                include_merged_worktrees=True,
            )
            complete_names = self.archive_names(complete_archive)
            self.assertIn(f'{prefix}tracked.txt', complete_names)

    def test_linked_worktree_as_project_root_remains_archivable_with_no_git(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            main_repo = base / 'main'
            worktree = base / 'worktree'
            self.init_repo(main_repo)
            (main_repo / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(main_repo, 'initial')
            self.run_git(main_repo, 'worktree', 'add', '-b', 'feature', str(worktree))
            (worktree / 'untracked.txt').write_text('untracked', encoding='utf-8')

            archive_path = base / 'worktree.zip'
            archive_git_sources(
                worktree,
                archive_path,
                include_git=False,
                include_untracked=True,
            )
            names = self.archive_names(archive_path)
            self.assertIn('tracked.txt', names)
            self.assertIn('untracked.txt', names)
            self.assertFalse(any(name.startswith('__worktrees__/') for name in names))

    def test_linked_worktree_uses_main_repository_name_for_external_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            main_repo = base / 'repository'
            first_worktree = base / 'outside-a' / 'checkout'
            second_worktree = base / 'outside-b' / 'checkout'
            third_worktree = base / 'outside-c' / 'checkout'
            self.init_repo(main_repo)
            (main_repo / 'tracked.txt').write_text('tracked', encoding='utf-8')
            self.commit_all(main_repo, 'initial')
            first_worktree.parent.mkdir(parents=True)
            second_worktree.parent.mkdir(parents=True)
            third_worktree.parent.mkdir(parents=True)
            self.run_git(main_repo, 'worktree', 'add', '-b', 'feature-a', str(first_worktree))
            self.run_git(main_repo, 'worktree', 'add', '-b', 'feature-b', str(second_worktree))
            self.run_git(main_repo, 'worktree', 'add', '-b', 'feature-c', str(third_worktree))
            (second_worktree / 'second.txt').write_text('second', encoding='utf-8')
            (third_worktree / 'third.txt').write_text('third', encoding='utf-8')
            self.commit_all(second_worktree, 'second')
            self.commit_all(third_worktree, 'third')

            archive_path = base / 'linked-root.zip'
            archive_git_sources(first_worktree, archive_path, include_untracked=True)
            names = self.archive_names(archive_path)
            self.assertIn('tracked.txt', names)
            self.assertIn(
                '__worktrees__/repository/checkout/second.txt',
                names,
            )
            self.assertIn(
                '__worktrees__/repository/checkout-2/third.txt',
                names,
            )


if __name__ == '__main__':
    unittest.main()

import unittest
from pathlib import Path
from subprocess import CompletedProcess

from others.netlify_deploy import (
    DeployDetails,
    build_deploy_args,
    build_post_deploy_notice,
    parse_team_slug,
    prepare_account,
    read_deploy_details,
)


class TestNetlifyDeploy(unittest.TestCase):
    def test_build_deploy_args_targets_production_without_build(self) -> None:
        directory = Path(r'C:\site')

        self.assertEqual(
            build_deploy_args(directory),
            ['deploy', '--prod', '--no-build', '--dir', r'C:\site'],
        )

    def test_prepare_account_uses_netlify_switch_menu(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **_: object) -> CompletedProcess[str]:
            calls.append(command)
            return CompletedProcess(command, 0, stdout='', stderr='')

        self.assertTrue(prepare_account(command_runner=runner))
        self.assertEqual(calls, [['switch']])

    def test_prepare_account_returns_false_when_switch_is_cancelled(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **_: object) -> CompletedProcess[str]:
            calls.append(command)
            return CompletedProcess(command, 1, stdout='', stderr='')

        self.assertFalse(prepare_account(command_runner=runner))
        self.assertEqual(calls, [['switch']])

    def test_parse_team_slug_prefers_default_team(self) -> None:
        teams_json = '[{"slug":"personal-team","default":false},{"slug":"3074006686","default":true}]'

        self.assertEqual(parse_team_slug(teams_json), '3074006686')

    def test_read_deploy_details_reads_status_and_team_data(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **_: object) -> CompletedProcess[str]:
            calls.append(command)
            if command == ['status']:
                output = (
                    'Email: 3074006686@qq.com\n'
                    'Current project: marathon-data-story\n'
                    'Admin URL: https://app.netlify.com/projects/marathon-data-story/overview\n'
                    'Project URL: https://marathon-data-story.netlify.app/\n'
                )
                return CompletedProcess(command, 0, stdout=output, stderr='')
            return CompletedProcess(
                command,
                0,
                stdout='[{"slug":"3074006686","default":true}]',
                stderr='',
            )

        details = read_deploy_details(runner)

        self.assertIsNotNone(details)
        assert details is not None
        self.assertEqual(details.site_url, 'https://marathon-data-story.netlify.app/')
        self.assertEqual(details.account_email, '3074006686@qq.com')
        self.assertEqual(details.team_slug, '3074006686')
        self.assertEqual(calls, [['status'], ['teams:list', '--json']])

    def test_build_post_deploy_notice_matches_expected_information(self) -> None:
        details = DeployDetails(
            site_url='https://marathon-data-story.netlify.app/',
            project_url='https://app.netlify.com/projects/marathon-data-story/overview',
            site_name='marathon-data-story',
            account_email='3074006686@qq.com',
            team_slug='3074006686',
        )

        self.assertEqual(
            build_post_deploy_notice(details),
            '已部署：https://marathon-data-story.netlify.app/\n\n'
            '后续更新访问 https://app.netlify.com/projects/marathon-data-story/overview 将网页文件夹拖拽到图中位置即可，账号 3074006686@qq.com\n\n'
            '每月有 100G 免费额度，重新部署会消耗额度（最好不要太频繁部署），剩余额度可在 https://app.netlify.com/teams/3074006686/billing/general 查看。',
        )


if __name__ == '__main__':
    unittest.main()

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fs.create_date_folder import (
    build_folder_name,
    create_date_folder,
    main,
    show_duplicate_folder_notification,
)


class TestBuildFolderName(unittest.TestCase):
    def test_default_template_uses_current_date(self) -> None:
        folder_name = build_folder_name('YYYYMMDD', current_datetime=datetime(2026, 7, 12, 9, 30, 0))

        self.assertEqual(folder_name, '20260712')

    def test_custom_template_formats_date(self) -> None:
        folder_name = build_folder_name('YYYY-MM-DD', current_datetime=datetime(2026, 7, 12, 9, 30, 0))

        self.assertEqual(folder_name, '2026-07-12')


class TestCreateDateFolder(unittest.TestCase):
    def test_creates_folder_under_target_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder_path, created = create_date_folder(
                temp_dir,
                current_datetime=datetime(2026, 7, 12, 9, 30, 0),
            )

            self.assertTrue(created)
            self.assertEqual(folder_path, Path(temp_dir) / '20260712')
            self.assertTrue(folder_path.is_dir())

    def test_returns_existing_folder_without_recreating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_path = Path(temp_dir) / '2026-07-12'
            existing_path.mkdir()

            folder_path, created = create_date_folder(
                temp_dir,
                template='YYYY-MM-DD',
                current_datetime=datetime(2026, 7, 12, 9, 30, 0),
            )

            self.assertFalse(created)
            self.assertEqual(folder_path, existing_path)

    def test_rejects_missing_target_directory(self) -> None:
        with self.assertRaises(FileNotFoundError):
            create_date_folder(
                'D:/this-path-should-not-exist-for-tests',
                current_datetime=datetime(2026, 7, 12, 9, 30, 0),
            )


class TestWindowsNotification(unittest.TestCase):
    def test_show_duplicate_folder_notification_uses_windows_toasts(self) -> None:
        events: list[tuple[str, str, str]] = []

        class FakeToast:
            def __init__(self) -> None:
                self.text_fields: list[str] = []

        class FakeWindowsToaster:
            def __init__(self, app_name: str) -> None:
                events.append(('init', app_name, ''))

            def show_toast(self, toast: FakeToast) -> None:
                events.append(('show', toast.text_fields[0], toast.text_fields[1]))

        show_duplicate_folder_notification(
            Path('D:/demo/2026-07-12'),
            toaster_class=FakeWindowsToaster,
            toast_class=FakeToast,
        )

        self.assertEqual(events, [('init', 'create_date_folder', ''), ('show', '文件夹已存在', 'D:\\demo\\2026-07-12')])

    def test_main_shows_notification_when_folder_exists(self) -> None:
        fake_parser = SimpleNamespace(
            parse_args=lambda: SimpleNamespace(directory='D:/demo', template='YYYYMMDD'),
        )

        with patch('fs.create_date_folder.create_argument_parser', return_value=fake_parser), \
             patch('fs.create_date_folder.create_date_folder', return_value=(Path('D:/demo/20260712'), False)), \
             patch('fs.create_date_folder.show_duplicate_folder_notification') as mock_notification:
            exit_code = main()

        self.assertEqual(exit_code, 0)
        mock_notification.assert_called_once_with(Path('D:/demo/20260712'))


if __name__ == '__main__':
    unittest.main()

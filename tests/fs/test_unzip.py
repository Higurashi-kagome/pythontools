import subprocess
import tempfile
import unittest
from pathlib import Path

from fs.unzip import extract_archive, find_7zip


class TestExtractArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.seven_zip = find_7zip()
        except FileNotFoundError as error:
            raise unittest.SkipTest(str(error)) from error

    def create_archive(
        self,
        input_directory: Path,
        archive_path: Path,
        sources: list[str],
    ) -> None:
        result = subprocess.run(
            [self.seven_zip, 'a', '-sccUTF-8', str(archive_path), *sources],
            cwd=input_directory,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_single_top_level_folder_extracts_to_archive_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_directory = root / 'input'
            archive_directory = root / 'archives'
            input_directory.mkdir()
            archive_directory.mkdir()
            (input_directory / 'single' / 'file.txt').parent.mkdir()
            (input_directory / 'single' / 'file.txt').write_text('content', encoding='utf-8')
            archive_path = archive_directory / 'single.zip'
            self.create_archive(input_directory, archive_path, ['single'])

            destination = extract_archive(archive_path)

            self.assertEqual(destination, archive_directory.resolve())
            self.assertEqual(
                (archive_directory / 'single' / 'file.txt').read_text(encoding='utf-8'),
                'content',
            )

    def test_multiple_top_level_items_extract_to_archive_named_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_directory = root / 'input'
            archive_directory = root / 'archives'
            input_directory.mkdir()
            archive_directory.mkdir()
            (input_directory / 'one.txt').write_text('one', encoding='utf-8')
            (input_directory / 'two' / 'two.txt').parent.mkdir()
            (input_directory / 'two' / 'two.txt').write_text('two', encoding='utf-8')
            archive_path = archive_directory / 'multiple.zip'
            self.create_archive(input_directory, archive_path, ['one.txt', 'two'])

            destination = extract_archive(archive_path)

            expected_destination = archive_directory / 'multiple'
            self.assertEqual(destination, expected_destination.resolve())
            self.assertEqual((expected_destination / 'one.txt').read_text(encoding='utf-8'), 'one')
            self.assertEqual(
                (expected_destination / 'two' / 'two.txt').read_text(encoding='utf-8'),
                'two',
            )

    def test_existing_archive_named_folder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_directory = root / 'input'
            archive_directory = root / 'archives'
            input_directory.mkdir()
            archive_directory.mkdir()
            (input_directory / 'one.txt').write_text('one', encoding='utf-8')
            (input_directory / 'two.txt').write_text('two', encoding='utf-8')
            archive_path = archive_directory / 'multiple.zip'
            self.create_archive(input_directory, archive_path, ['one.txt', 'two.txt'])
            (archive_directory / 'multiple').mkdir()

            with self.assertRaises(FileExistsError):
                extract_archive(archive_path)


if __name__ == '__main__':
    unittest.main()

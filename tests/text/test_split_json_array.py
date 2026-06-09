import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from text.split_json_array import sanitize_filename, split_json_array_file


class TestSanitizeFilename(unittest.TestCase):
    def test_replaces_windows_invalid_characters(self) -> None:
        self.assertEqual(sanitize_filename('a<b>:c"/\\|?*d'), 'a_b__c______d')

    def test_rejects_blank_filename(self) -> None:
        self.assertEqual(sanitize_filename('   .  '), '')

    def test_prefixes_reserved_windows_name(self) -> None:
        self.assertEqual(sanitize_filename('con'), '_con')


class TestSplitJsonArrayFile(unittest.TestCase):
    def test_defaults_to_index_based_filenames(self) -> None:
        sample_data = [
            {'name': 'alpha', 'value': 1},
            {'name': 'alpha', 'value': 2},
            {'name': 'a/b', 'value': 3},
            {'value': 4},
            {'name': '   ', 'value': 5},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / 'input.json'
            input_path.write_text(json.dumps(sample_data, ensure_ascii=False), encoding='utf-8')

            output_directory = split_json_array_file(
                input_file=str(input_path),
                timestamp='20260609_120000',
            )

            self.assertEqual(output_directory.name, '20260609_120000')

            generated_files = sorted(path.name for path in output_directory.iterdir())
            self.assertEqual(
                generated_files,
                ['item_1.json', 'item_2.json', 'item_3.json', 'item_4.json', 'item_5.json'],
            )

            first_item = json.loads((output_directory / 'item_1.json').read_text(encoding='utf-8'))
            duplicate_item = json.loads((output_directory / 'item_2.json').read_text(encoding='utf-8'))
            fallback_item = json.loads((output_directory / 'item_4.json').read_text(encoding='utf-8'))

            self.assertEqual(first_item['value'], 1)
            self.assertEqual(duplicate_item['value'], 2)
            self.assertEqual(fallback_item['value'], 4)

    def test_uses_custom_key_for_filename(self) -> None:
        sample_data = [
            {'id': '1001', 'name': 'ignored'},
            {'id': '1001', 'name': 'ignored2'},
            {'name': 'missing-id'},
            {'id': 'a/b', 'name': 'invalid-id'},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / 'input.json'
            input_path.write_text(json.dumps(sample_data, ensure_ascii=False), encoding='utf-8')

            output_directory = split_json_array_file(
                input_file=str(input_path),
                key_name='id',
                timestamp='20260609_120001',
            )

            generated_files = sorted(path.name for path in output_directory.iterdir())
            self.assertEqual(generated_files, ['1001.json', '1001_2.json', 'a_b.json', 'item_3.json'])

    def test_rejects_non_array_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / 'input.json'
            input_path.write_text('{"name":"alpha"}', encoding='utf-8')

            with self.assertRaises(ValueError):
                split_json_array_file(
                    input_file=str(input_path),
                    timestamp='20260609_120002',
                )

    def test_rejects_non_object_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / 'input.json'
            input_path.write_text('[{"name":"alpha"}, 123]', encoding='utf-8')

            with self.assertRaises(ValueError):
                split_json_array_file(
                    input_file=str(input_path),
                    timestamp='20260609_120003',
                )


if __name__ == '__main__':
    unittest.main()

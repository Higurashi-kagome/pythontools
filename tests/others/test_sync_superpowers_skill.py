import tempfile
import unittest
from pathlib import Path

from others.sync_superpowers_skill import (
    INDEX_FILENAME,
    cleanup_legacy_skill_mirrors,
    collect_session_hashes_incremental,
)


class TestSyncSuperpowersSkill(unittest.TestCase):
    def test_cleanup_legacy_skill_mirrors_removes_only_legacy_superpowers_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            cache_root = temp_root / 'cache' / 'openai-curated' / 'superpowers' / 'c6ea566d'
            system_skills_root = temp_root / 'skills' / '.system'

            legacy_skill_dir = system_skills_root / 'brainstorming'
            legacy_skill_dir.mkdir(parents=True)
            (legacy_skill_dir / 'SKILL.md').write_text('legacy', encoding='utf-8')
            (legacy_skill_dir / '.superpowers-source').write_text(
                str(cache_root / 'skills' / 'brainstorming'),
                encoding='utf-8',
            )

            native_skill_dir = system_skills_root / 'imagegen'
            native_skill_dir.mkdir(parents=True)
            (native_skill_dir / 'SKILL.md').write_text('native', encoding='utf-8')

            cleanup_legacy_skill_mirrors(system_skills_root, cache_root.parent)

            self.assertFalse(legacy_skill_dir.exists())
            self.assertTrue(native_skill_dir.exists())

    def test_collect_session_hashes_incremental_uses_cache_for_unchanged_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            sessions_root = temp_root / 'sessions'
            index_dir = temp_root / 'state'
            session_file = sessions_root / '2026' / '06' / '12' / 'rollout.jsonl'
            session_file.parent.mkdir(parents=True)
            session_file.write_text(
                'superpowers/0d4f5414/skills\n',
                encoding='utf-8',
            )

            first_hashes = collect_session_hashes_incremental(sessions_root, index_dir)
            self.assertEqual(first_hashes, {'0d4f5414'})
            self.assertTrue((index_dir / INDEX_FILENAME).exists())

            session_file.write_text(
                'superpowers/0d4f5414/skills\n',
                encoding='utf-8',
            )

            second_hashes = collect_session_hashes_incremental(sessions_root, index_dir)
            self.assertEqual(second_hashes, {'0d4f5414'})


if __name__ == '__main__':
    unittest.main()

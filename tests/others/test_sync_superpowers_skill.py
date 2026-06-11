import tempfile
import unittest
from pathlib import Path

from others.sync_superpowers_skill import cleanup_legacy_skill_mirrors


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


if __name__ == '__main__':
    unittest.main()

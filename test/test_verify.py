"""Exercise source/collection verification in isolated, synthetic theme checkouts."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('src/themes', 'scripts', '.github/workflows'):
            (self.root / directory).mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/verify.mjs', self.root / 'scripts/verify.mjs')
        (self.root / '.github/workflows/release.yml').write_text('name: fixture\n')
        (self.root / 'src/themes/first.css').write_text('body {color:black}\n')
        (self.root / 'src/themes/second.css').write_text('body {color:white}\n')
        (self.root / 'package.json').write_text(json.dumps({
            'type': 'module', 'files': ['src/themes/first.css', 'src/themes/second.css']}))

    def verify(self):
        return subprocess.run(['node', 'scripts/verify.mjs'], cwd=self.root,
                              text=True, capture_output=True)

    def test_two_theme_stylesheets_without_manifest(self):
        self.assertFalse((self.root / 'release.json').exists())
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_theme_stylesheet_required(self):
        for name in ('first.css', 'second.css'):
            (self.root / 'src/themes' / name).unlink()
        (self.root / 'src/themes/asset.svg').write_text('<svg/>')
        self.assertNotEqual(self.verify().returncode, 0)
        (self.root / 'src/elsewhere.css').write_text('body {}')
        self.assertNotEqual(self.verify().returncode, 0)

    def test_css_url_resolution_and_escape_validation(self):
        css = self.root / 'src/themes/first.css'
        for url in ('missing.png', '../../../outside.png'):
            css.write_text(f'body {{background:url("{url}")}}\n')
            self.assertNotEqual(self.verify().returncode, 0)
        (self.root / 'src/themes/asset.svg').write_text('<svg/>')
        css.write_text('body {background:url("asset.svg")}\n')
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_javascript_import_boundaries(self):
        script = self.root / 'src/themes/check.js'
        for specifier in ('./missing.js', '../../../outside.js', '/other/api.js', 'undeclared'):
            script.write_text(f'import "{specifier}"\n')
            self.assertNotEqual(self.verify().returncode, 0)
        script.write_text('import "/core/runtime.js"\n')
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_symlink_rejected(self):
        path = self.root / 'src/themes/first.css'
        path.unlink()
        path.symlink_to(self.root / 'src/themes/second.css')
        self.assertNotEqual(self.verify().returncode, 0)

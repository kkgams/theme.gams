import io
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/release.py'
SPEC = importlib.util.spec_from_file_location('release', SCRIPT)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        # identity() must read the synthetic package, not this checkout's version.
        binding = patch.object(release, '__file__', str(self.root / 'scripts/release.py'))
        binding.start()
        self.addCleanup(binding.stop)
        (self.root / 'src/themes').mkdir(parents=True)
        (self.root / 'src/themes/first.css').write_bytes(b'body { color: black }\n')
        (self.root / 'src/themes/second.css').write_bytes(b'body { color: white }\n')
        (self.root / 'package.json').write_text(json.dumps({
            'name': 'theme.gams', 'version': '1.0.0', 'private': True,
            'license': 'Apache-2.0', 'files': ['src/themes/first.css', 'src/themes/second.css']}))
        (self.root / 'release.json').write_text(json.dumps({'kind': 'theme', 'entries': ['themes/first.css', 'themes/second.css']}))
        for name in ('LICENSE', 'NOTICE', 'README.md'):
            (self.root / name).write_text(name + '\n')
        (self.root / 'licenses').mkdir()
        (self.root / 'licenses/98.css.MIT.txt').write_text('MIT terms\n')
        (self.root / 'THEME-COMPARISON.json').write_text('{}\n')
        evidence = {'files_sha256': {p: release.digest((self.root / p).read_bytes())
                    for p in ('src/themes/first.css', 'src/themes/second.css',
                              'THEME-COMPARISON.json', 'licenses/98.css.MIT.txt')}}
        proof = json.dumps(evidence).encode()
        (self.root / 'NOTICE-EVIDENCE.json').write_bytes(proof)
        (self.root / 'NOTICE').write_text('NOTICE\nNOTICE-EVIDENCE.json SHA-256: ' + release.digest(proof) + '\n')
        self.env = {'GITHUB_REPOSITORY': 'kkgams/theme.gams'}
        self.patch = patch.dict(os.environ, self.env)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.out = Path(self.temp.name) / 'candidate'

    def stage(self):
        release.stage(self.root, self.out, 'v1.0.0')

    def check(self):
        release.check(self.root, self.out, 'v1.0.0')

    def test_real_zip_determinism_and_mapping(self):
        self.stage()
        self.check()
        second = Path(self.temp.name) / 'second'
        release.stage(self.root, second, 'v1.0.0')
        name = 'theme.gams-1.0.0.zip'
        self.assertEqual((self.out / name).read_bytes(), (second / name).read_bytes())
        with zipfile.ZipFile(self.out / name) as z:
            self.assertEqual(set(z.namelist()), {
                'themes/first.css', 'themes/second.css', *release.LEGAL_PAYLOAD})
            self.assertNotIn('unit.json', z.namelist())
            for path in release.LEGAL_PAYLOAD:
                self.assertEqual(z.read(path), (self.root / path).read_bytes())

    def write_evidence(self, evidence):
        proof = json.dumps(evidence).encode()
        (self.root / 'NOTICE-EVIDENCE.json').write_bytes(proof)
        (self.root / 'NOTICE').write_text('NOTICE\nNOTICE-EVIDENCE.json SHA-256: ' + release.digest(proof) + '\n')

    def test_missing_and_malformed_collection_entries(self):
        invalid = [None, [], {}, {'kind': 'theme'},
                   {'kind': 'theme', 'entry': 'themes/first.css'},
                   {'kind': 'view', 'entries': ['themes/first.css']},
                   {'kind': 'theme', 'entries': []},
                   {'kind': 'theme', 'entries': 'themes/first.css'},
                   {'kind': 'theme', 'entries': [None]},
                   {'kind': 'theme', 'entries': ['themes/first.css'] * 2},
                   {'kind': 'theme', 'entries': ['themes/missing.css']},
                   {'kind': 'theme', 'entries': ['LICENSE']},
                   {'kind': 'theme', 'entries': ['../themes/first.css']},
                   {'kind': 'theme', 'entries': ['/themes/first.css']},
                   {'kind': 'theme', 'entries': ['themes//first.css']},
                   {'kind': 'theme', 'entries': ['themes/first.css'], 'host': '2.0.3'}]
        for config in invalid:
            with self.subTest(config=config):
                (self.root / 'release.json').write_text(json.dumps(config))
                with self.assertRaises(ValueError):
                    self.stage()
        (self.root / 'release.json').write_text('{')
        with self.assertRaises(ValueError):
            self.stage()
        (self.root / 'release.json').unlink()
        with self.assertRaises(ValueError):
            self.stage()

    def test_collection_identity_and_version(self):
        package = json.loads((self.root / 'package.json').read_text())
        for key, value in (('name', 'theme.the98'), ('version', '01.0.0'),
                           ('version', '1.0.0-beta'), ('private', False),
                           ('license', 'MIT')):
            with self.subTest(key=key, value=value):
                (self.root / 'package.json').write_text(json.dumps(dict(package, **{key: value})))
                with self.assertRaises(ValueError):
                    self.stage()

    def test_all_evidence_inputs_are_bound_and_validated(self):
        evidence = json.loads((self.root / 'NOTICE-EVIDENCE.json').read_text())
        for name in ('THEME-COMPARISON.json', 'licenses/98.css.MIT.txt'):
            original = (self.root / name).read_bytes()
            (self.root / name).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'audited evidence input changed'):
                self.stage()
            (self.root / name).write_bytes(original)
            reduced = {'files_sha256': dict(evidence['files_sha256'])}
            del reduced['files_sha256'][name]
            self.write_evidence(reduced)
            with self.assertRaisesRegex(ValueError, 'missing audited'):
                self.stage()
            self.write_evidence(evidence)
        for invalid in ({}, {'files_sha256': []}, {'files_sha256': {}}):
            self.write_evidence(invalid)
            with self.assertRaisesRegex(ValueError, 'invalid evidence'):
                self.stage()

    def test_source_closure_rejects_unlisted_and_unaudited_files(self):
        path = self.root / 'src/themes/extra.css'
        path.write_text('body {}')
        with self.assertRaisesRegex(ValueError, 'package files'):
            self.stage()
        package = json.loads((self.root / 'package.json').read_text())
        package['files'].append('src/themes/extra.css')
        (self.root / 'package.json').write_text(json.dumps(package))
        with self.assertRaisesRegex(ValueError, 'audited evidence'):
            self.stage()

    def test_unsafe_evidence_paths_and_source_symlinks(self):
        evidence = json.loads((self.root / 'NOTICE-EVIDENCE.json').read_text())
        for name in ('../outside', '/outside', 'src//themes/first.css', 'src/../NOTICE', 'src\\themes/first.css'):
            with self.subTest(name=name):
                modified = {'files_sha256': dict(evidence['files_sha256'], **{name: '0' * 64})}
                self.write_evidence(modified)
                with self.assertRaisesRegex(ValueError, 'invalid relative path'):
                    self.stage()
        self.write_evidence(evidence)
        path = self.root / 'src/themes/first.css'
        content = path.read_bytes()
        path.unlink()
        external = self.root / 'external.css'
        external.write_bytes(content)
        path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.stage()
        path.unlink()
        path.write_bytes(content)
        (self.root / 'src/linked-directory').symlink_to(self.root / 'licenses', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.stage()

    def test_candidate_symlinks_are_rejected(self):
        self.stage()
        name = 'theme.gams-1.0.0.zip'
        target = Path(self.temp.name) / name
        (self.out / name).rename(target)
        (self.out / name).symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.check()

    def test_incomplete_extra_and_nondeterministic_zip(self):
        self.stage()
        name, files = release.payload(self.root, 'v1.0.0')
        for kind in ('missing', 'extra', 'metadata'):
            with self.subTest(kind=kind):
                candidate = dict(files)
                if kind == 'missing':
                    del candidate['NOTICE-EVIDENCE.json']
                elif kind == 'extra':
                    candidate['unit.json'] = b'{}'
                data = release.archive(candidate)
                if kind == 'metadata':
                    stream = io.BytesIO()
                    with zipfile.ZipFile(stream, 'w') as bundle:
                        for path, content in sorted(candidate.items()):
                            bundle.writestr(path, content)
                    data = stream.getvalue()
                (self.out / name).write_bytes(data)
                (self.out / 'SHA256SUMS').write_text(f'{release.digest(data)}  {name}\n')
                with self.assertRaises(ValueError):
                    self.check()

    def test_current_checkout_can_stage_and_check(self):
        # Exercise the real checkout and evidence without external approval.
        root = SCRIPT.parents[1]
        package = json.loads((root / 'package.json').read_text())
        env = {'GITHUB_REPOSITORY': 'kkgams/' + package['name']}
        with patch.dict(os.environ, env):
            tag = 'v' + package['version']
            release.stage(root, self.out, tag)
            release.check(root, self.out, tag)

    def test_changed_checksum(self):
        self.stage()
        (self.out / 'SHA256SUMS').write_text('bad')
        with self.assertRaises(ValueError):
            self.check()

    def test_changed_content_even_with_recomputed_checksum(self):
        self.stage()
        name, files = release.payload(self.root, 'v1.0.0')
        files['themes/second.css'] = b'changed'
        data = release.archive(files)
        (self.out / name).write_bytes(data)
        (self.out / 'SHA256SUMS').write_text(f'{release.digest(data)}  {name}\n')
        with self.assertRaises(ValueError):
            self.check()

    def test_workflow_repository_identity(self):
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'kkgams/theme.wrong'}):
            with self.assertRaisesRegex(ValueError, 'canonical Project Unit identity'):
                self.stage()

    def test_license_notice_required_without_external_approval(self):
        with patch.dict(os.environ, {}, clear=True):
            self.stage()
            self.check()
        for name in release.LEGAL_PAYLOAD:
            path = self.root / name
            original = path.read_bytes()
            for content in (b'', b'  \n'):
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    release.payload(self.root, 'v1.0.0')
            path.unlink()
            with self.assertRaises(ValueError):
                release.payload(self.root, 'v1.0.0')
            path.symlink_to(self.root / 'README.md')
            with self.assertRaises(ValueError):
                release.payload(self.root, 'v1.0.0')
            path.unlink()
            path.write_bytes(original)
        (self.root / 'NOTICE').write_text('PROVENANCE_PENDING')
        with self.assertRaises(ValueError):
            release.legal_files(self.root)

    def test_legal_texts_are_exactly_packaged_and_checked(self):
        self.stage()
        name, _ = release.payload(self.root, 'v1.0.0')
        with zipfile.ZipFile(self.out / name) as bundle:
            for legal in ('LICENSE', 'NOTICE'):
                self.assertEqual(bundle.read(legal), (self.root / legal).read_bytes())
        (self.root / 'LICENSE').write_text('changed legal text')
        with self.assertRaisesRegex(ValueError, 'candidate content mismatch: LICENSE'):
            self.check()

    def test_tag_mismatch(self):
        with self.assertRaises(ValueError):
            release.stage(self.root, self.out, 'v0.2.0')
        with self.assertRaises(ValueError):
            release.identity('v0.2.0')

    def test_missing_inputs_no_source_fallback(self):
        self.out.mkdir()
        with self.assertRaises(ValueError):
            self.check()
        self.out.rmdir()
        self.stage()
        (self.out / 'theme.gams-1.0.0.zip').unlink()
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_output(self):
        self.stage()
        with self.assertRaises(FileExistsError):
            self.stage()
        package = json.loads((self.root / 'package.json').read_text())
        package['files'].append(package['files'][0])
        (self.root / 'package.json').write_text(json.dumps(package))
        with self.assertRaises(ValueError):
            release.payload(self.root, 'v1.0.0')

    def test_duplicate_zip_entries(self):
        self.stage()
        name, files = release.payload(self.root, 'v1.0.0')
        stream = io.BytesIO(release.archive(files))
        with zipfile.ZipFile(stream, 'a') as z:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr('themes/second.css', files['themes/second.css'])
        data = stream.getvalue()
        (self.out / name).write_bytes(data)
        (self.out / 'SHA256SUMS').write_text(f'{release.digest(data)}  {name}\n')
        with self.assertRaises(ValueError):
            self.check()

    def test_audited_source_and_evidence_changes_fail(self):
        (self.root / 'src/themes/second.css').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'audited evidence input changed'):
            self.stage()
        (self.root / 'NOTICE-EVIDENCE.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'NOTICE does not bind'):
            self.stage()

    def test_workflow_all_branches_and_tag_only_publication(self):
        workflow = SCRIPT.parents[1] / '.github/workflows/release.yml'
        text = workflow.read_text()
        self.assertIn("branches: ['**']", text)
        self.assertIn("node-version: 24", text)
        self.assertIn("needs: candidate", text)
        self.assertNotIn('APPROVED_', text)
        self.assertNotIn('vars.', text)
        self.assertNotIn('refs/heads/release', text)
        self.assertIn('release.py identity', text)
        self.assertEqual(text.count('ref: ${{ github.sha }}'), 2)
        self.assertEqual(text.count('name: unit-${{ github.sha }}'), 2)
        self.assertNotIn('unit-${{ github.ref_name }}', text)
        upload = text[text.index('- uses: actions/upload-artifact@'):text.index('  publish:')]
        self.assertNotIn('if:', upload)
        self.assertIn("  publish:\n    if: startsWith(github.ref, 'refs/tags/v')", text)
        self.assertNotIn('--clobber', text)
        self.assertNotIn('npm publish', text)
        import re
        self.assertEqual(len(re.findall(r'uses: actions/[a-z-]+@[0-9a-f]{40}', text)), 5)

    def test_missing_source_closure(self):
        (self.root / 'src/themes/second.css').unlink()
        with self.assertRaises(ValueError):
            self.stage()

    def test_github_api_fail_closed_and_existing_release(self):
        for code in (401, 403, 500):
            with patch.object(release.urllib.request, 'urlopen', side_effect=urllib.error.HTTPError('url', code, 'error', {}, None)):
                with self.assertRaises(urllib.error.HTTPError):
                    release.absent('owner/repo', 'v1.0.0', 'token')
        with patch.object(release.urllib.request, 'urlopen', side_effect=urllib.error.URLError('offline')):
            with self.assertRaises(urllib.error.URLError):
                release.absent('owner/repo', 'v1.0.0', 'token')
        with patch.object(release.urllib.request, 'urlopen'):
            with self.assertRaises(ValueError):
                release.absent('owner/repo', 'v1.0.0', 'token')
        with patch.object(release.urllib.request, 'urlopen', side_effect=urllib.error.HTTPError('url', 404, 'missing', {}, None)):
            release.absent('owner/repo', 'v1.0.0', 'token')

    def test_annotated_or_lightweight_workflow_sha_is_peeled(self):
        for sha in ('commit-sha', 'annotated-tag-object-sha'):
            with self.subTest(sha=sha), patch.dict(os.environ, {'GITHUB_SHA': sha}):
                with patch.object(release.subprocess, 'check_output', side_effect=[b'commit', b'commit', b'commit']) as git:
                    release.identity('v1.0.0')
                    self.assertEqual(git.call_args_list[-1].args[0],
                                     ['git', 'rev-parse', sha + '^{commit}'])

    def test_tag_identity_requires_checkout_and_workflow_sha_only(self):
        for head, tag, sha in ((b'a', b'b', 'a'), (b'a', b'a', 'b')):
            with patch.object(release.subprocess, 'check_output', side_effect=[head, tag, sha.encode()]), patch.dict(os.environ, {'GITHUB_SHA': sha}):
                with self.assertRaises(ValueError):
                    release.identity('v1.0.0')
        with patch.object(release.subprocess, 'check_output', side_effect=[b'a', b'a', b'a']), patch.dict(os.environ, {'GITHUB_SHA': 'a'}):
            release.identity('v1.0.0')
        with patch.object(release.subprocess, 'check_output', side_effect=RuntimeError('git failed')):
            with self.assertRaises(RuntimeError):
                release.identity('v1.0.0')


if __name__ == '__main__':
    unittest.main()

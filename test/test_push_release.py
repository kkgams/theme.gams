"""Shell protocol tests: all git/gh operations are fakes, never remote calls."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/push-release.sh'
FAKE = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
case = os.environ.get('CASE', '')
with open(os.environ['LOG'], 'a') as log:
    log.write(json.dumps([name, *args]) + '\n')
if name == 'git':
    if args == ['status', '--porcelain']:
        if case == 'dirty': print(' M README.md')
    elif args[:1] == ['symbolic-ref']:
        if case == 'detached': sys.exit(1)
        print('refs/heads/feature/release')
    elif args == ['rev-parse', 'HEAD']: print('abc123')
    elif args[:2] == ['remote', 'get-url']:
        print('https://github.com/other/repo.git' if case == 'origin' else 'git@github.com:kkgams/theme.gams.git')
    elif args[:1] == ['config']:
        if case == 'mirror': print('true')
        elif case == 'config-error': sys.exit(2)
        else: sys.exit(1)
    elif args == ['show', 'HEAD:package.json']:
        print(json.dumps({'name':'theme.gams', 'version':'1.0.0' if case != 'version' else '01.0.0'}))
    elif args[:1] == ['show-ref']:
        sys.exit(0 if case in ('local', 'mismatch') else (2 if case == 'local-error' else 1))
    elif args[:1] == ['rev-parse']: print('bad' if case == 'mismatch' else 'abc123')
    elif args[:1] == ['ls-remote']:
        if case == 'remote-error': sys.exit(128)
        if case == 'remote': print('abc123\trefs/tags/v1.0.0')
    elif args[:1] == ['push']:
        if case == 'push-error': sys.exit(1)
    elif args[:1] != ['tag']: sys.exit('unexpected git call: ' + str(args))
elif name == 'gh':
    if args[:1] == ['auth']:
        if case == 'auth': sys.exit(1)
    elif args[:1] == ['api']:
        if case in ('api401','api403','api404','api500','offline'): sys.exit(1)
        if '.permissions.push' in args: print('false' if case == 'read-only' else 'true')
        elif case == 'release': print('[[{"tag_name":"v1.0.0","draft":true}]]')
        elif case == 'later-release': print('[[],[{"tag_name":"v1.0.0"}]]')
        elif case == 'malformed': print('not json')
        elif case == 'shape': print('{}')
        elif case == 'record': print('[[{}]]')
        elif case == 'page': print('[{}]')
        else: print('[[]]')
    else: sys.exit('unexpected gh mutation')
elif name == 'npm':
    if case == 'tests': sys.exit(1)
else: sys.exit('unexpected executable')
'''


class PushReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/push-release.sh').write_bytes(SCRIPT.read_bytes())
        # Staging itself is tested in test_release.py; this stub isolates shell sequencing.
        (self.root / 'scripts/release.py').write_text('import sys\n')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name in ('git', 'gh', 'npm'):
            path = self.bin / name
            path.write_text(FAKE.replace('#!/usr/bin/env python3', '#!' + sys.executable))
            path.chmod(0o755)
        self.log = self.root / 'calls'

    def run_script(self, case='', *args):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                   CASE=case, LOG=str(self.log))
        result = subprocess.run(['bash', str(self.root / 'scripts/push-release.sh'), *args],
                                env=env, text=True, capture_output=True)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def test_default_preflight_never_changes_refs(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No refs changed', result.stdout)
        self.assertFalse(any(c[:2] in (['git', 'tag'], ['git', 'push']) for c in calls))
        self.assertIn(['git', 'show', 'HEAD:package.json'], calls)
        self.assertTrue(any(c[:2] == ['gh', 'api'] and '--paginate' in c for c in calls))

    def test_publish_pushes_branch_and_tag_atomically(self):
        for case in ('', 'local'):
            with self.subTest(case=case):
                self.log.unlink(missing_ok=True)
                result, calls = self.run_script(case, '--publish')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual([c for c in calls if c[:2] == ['git', 'push']], [
                    ['git', 'push', '--atomic', '--no-follow-tags', 'origin', 'abc123:refs/heads/feature/release', 'refs/tags/v1.0.0:refs/tags/v1.0.0']])
                tags = [c for c in calls if c[:2] == ['git', 'tag']]
                self.assertEqual(tags, [] if case == 'local' else [
                    ['git', 'tag', '-a', 'v1.0.0', 'abc123', '-m', 'Release v1.0.0']])
                self.assertFalse(any(c[:3] == ['gh', 'release', 'create'] for c in calls))

    def test_fail_closed_before_ref_mutation(self):
        for case in ('dirty', 'detached', 'origin', 'mirror', 'config-error',
                     'malformed', 'shape', 'record', 'page', 'later-release',
                     'version', 'mismatch', 'local-error',
                     'auth', 'read-only', 'remote', 'remote-error', 'release', 'api401', 'api403',
                     'api404', 'api500', 'offline', 'tests'):
            with self.subTest(case=case):
                self.log.unlink(missing_ok=True)
                result, calls = self.run_script(case, '--publish')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(c[:2] in (['git', 'tag'], ['git', 'push']) for c in calls))

    def test_push_error_propagates_without_force_or_release_creation(self):
        result, calls = self.run_script('push-error', '--publish')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('--force', sum(calls, []))
        self.assertFalse(any(c[:3] == ['gh', 'release', 'create'] for c in calls))

    def test_invalid_arguments(self):
        for args in (['--force'], ['--publish', 'extra']):
            result, calls = self.run_script('', *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(calls, [])

#!/usr/bin/env python3
"""Stdlib-only deterministic Project Unit staging and independent verification."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.error
import urllib.request
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


LEGAL_PAYLOAD = ('LICENSE', 'NOTICE', 'README.md', 'NOTICE-EVIDENCE.json',
                 'THEME-COMPARISON.json', 'licenses/98.css.MIT.txt')


def safe_path(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError('invalid relative path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name or name == '.':
        raise ValueError('invalid relative path: ' + name)
    local = root / name
    if any(p.is_symlink() for p in (local, *local.parents)):
        raise ValueError('symlink forbidden: ' + name)
    if not local.resolve().is_relative_to(root):
        raise ValueError('path escapes repository: ' + name)
    return local


def regular_bytes(root, name):
    path = safe_path(root, name)
    if not path.is_file() or not path.read_bytes().strip():
        raise ValueError('required nonempty regular file: ' + name)
    return path.read_bytes()


def legal_files(root):
    for name in LEGAL_PAYLOAD:
        regular_bytes(root, name)
    if 'PROVENANCE_PENDING' in (root / 'NOTICE').read_text():
        raise ValueError('theme provenance audit pending')


def payload(root, tag):
    root = root.resolve()
    package = json.loads(regular_bytes(root, 'package.json'))
    config = json.loads(regular_bytes(root, 'release.json'))
    if package['name'] != 'theme.gams':
        raise ValueError('invalid theme collection identity')
    if 'GITHUB_REPOSITORY' in os.environ and os.environ['GITHUB_REPOSITORY'] != 'kkgams/' + package['name']:
        raise ValueError('workflow repository must match canonical Project Unit identity')
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', package['version']) or tag != 'v' + package['version']:
        raise ValueError('tag/version mismatch')
    if package['license'] != 'Apache-2.0' or package['private'] is not True:
        raise ValueError('invalid package licensing/publication policy')
    if not isinstance(config, dict) or set(config) != {'kind', 'entries'} or config['kind'] != 'theme':
        raise ValueError('invalid theme collection manifest')
    entries = config['entries']
    if not isinstance(entries, list) or not entries or any(not isinstance(p, str) for p in entries) or len(entries) != len(set(entries)):
        raise ValueError('entries must be a nonempty unique list')
    legal_files(root)
    evidence_bytes = regular_bytes(root, 'NOTICE-EVIDENCE.json')
    if ('NOTICE-EVIDENCE.json SHA-256: ' + digest(evidence_bytes)) not in (root / 'NOTICE').read_text():
        raise ValueError('NOTICE does not bind current evidence')
    evidence = json.loads(evidence_bytes)
    audited = evidence.get('files_sha256') if isinstance(evidence, dict) else None
    if not isinstance(audited, dict) or not audited:
        raise ValueError('invalid evidence inputs')
    if not {'THEME-COMPARISON.json', 'licenses/98.css.MIT.txt'} <= audited.keys():
        raise ValueError('missing audited comparison/MIT inputs')
    for path, expected in audited.items():
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('invalid evidence digest')
        if digest(regular_bytes(root, path)) != expected:
            raise ValueError('audited evidence input changed: ' + path)
    source_files = package['files']
    if not isinstance(source_files, list) or not source_files or any(not isinstance(p, str) for p in source_files) or len(source_files) != len(set(source_files)):
        raise ValueError('empty or duplicate source mapping')
    source_root = safe_path(root, 'src')
    if not source_root.is_dir():
        raise ValueError('required source directory')
    actual = set()
    for local in source_root.rglob('*'):
        name = local.relative_to(root).as_posix()
        safe_path(root, name)
        if local.is_file():
            actual.add(name)
        elif not local.is_dir():
            raise ValueError('nonregular source: ' + name)
    if actual != set(source_files):
        raise ValueError('source closure differs from package files')
    if actual != {p for p in audited if p.startswith('src/')}:
        raise ValueError('source closure differs from audited evidence')
    files = {name: regular_bytes(root, name) for name in LEGAL_PAYLOAD}
    for source in source_files:
        path = PurePosixPath(source)
        if path.parts[0] != 'src' or len(path.parts) < 2:
            raise ValueError('invalid source path')
        deployed = path.relative_to('src').as_posix()
        if deployed in files or deployed == 'unit.json':
            raise ValueError('duplicate deployment output')
        files[deployed] = regular_bytes(root, source)
    for entry in entries:
        safe_path(root, entry)
        path = PurePosixPath(entry)
        if path.parts[0] != 'themes' or path.suffix != '.css' or entry not in files:
            raise ValueError('entry must be deployed theme CSS: ' + entry)
    return package['name'] + '.zip', files


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return output.getvalue()


def stage(root, out, tag):
    name, files = payload(root, tag)
    data = archive(files)
    out.mkdir(parents=True, exist_ok=False)
    (out / name).write_bytes(data)
    (out / 'SHA256SUMS').write_text(f'{digest(data)}  {name}\n')


def check(root, out, tag):
    name, files = payload(root, tag)
    if out.is_symlink() or not out.is_dir():
        raise ValueError('candidate must be a regular directory; no source fallback')
    if {p.name for p in out.iterdir()} != {name, 'SHA256SUMS'}:
        raise ValueError('missing or extra candidate inputs; no source fallback')
    for filename in (name, 'SHA256SUMS'):
        regular_bytes(out.resolve(), filename)
    data = (out / name).read_bytes()
    if (out / 'SHA256SUMS').read_text() != f'{digest(data)}  {name}\n':
        raise ValueError('checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.namelist()) != len(files) or set(z.namelist()) != set(files):
            raise ValueError('duplicate/missing/extra ZIP entries')
        for path, expected in files.items():
            if z.read(path) != expected:
                raise ValueError(f'candidate content mismatch: {path}')
    if data != archive(files):
        raise ValueError('non-deterministic candidate metadata')


def identity(tag):
    package = json.loads((Path(__file__).resolve().parents[1] / 'package.json').read_text())
    if tag != 'v' + package['version']:
        raise ValueError('tag/version mismatch')
    if package['name'] != 'theme.gams' or os.environ['GITHUB_REPOSITORY'] != 'kkgams/theme.gams':
        raise ValueError('workflow repository must match canonical Project Unit identity')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
    tagged = subprocess.check_output(['git', 'rev-parse', tag + '^{commit}']).strip()
    workflow = subprocess.check_output(['git', 'rev-parse', os.environ['GITHUB_SHA'] + '^{commit}']).strip()
    if head != tagged or head != workflow:
        raise ValueError('tag must match checkout HEAD and workflow SHA')


def absent(repository, tag, token):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository) or not re.fullmatch(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', tag):
        raise ValueError('invalid release identity')
    request = urllib.request.Request(
        f'https://api.github.com/repos/{repository}/releases/tags/{tag}',
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(request, timeout=30):
            pass
    except urllib.error.HTTPError as error:
        error.close()
        if error.code == 404:
            return
        raise
    raise ValueError('immutable release already exists; refusing overwrite')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['stage', 'check', 'identity', 'absent'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, default=Path('dist/candidate'))
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    if args.command in ('stage', 'check'):
        globals()[args.command](args.root.resolve(), args.out, args.tag)
    elif args.command == 'identity':
        identity(args.tag)
    else:
        absent(os.environ['GITHUB_REPOSITORY'], args.tag, os.environ['GH_TOKEN'])

#!/usr/bin/env python3
"""Package theme files for matching-tag releases."""
import argparse
import io
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.error
import urllib.request
import zipfile


REPOSITORY = 'kkgams/theme.gams'
REQUIRED_FILES = ('LICENSE', 'NOTICE', 'README.md', 'licenses/98.css.MIT.txt')
VERSION_PATTERN = r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'


def safe_path(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError('invalid relative path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name or name == '.':
        raise ValueError('invalid relative path: ' + name)
    local = root / name
    reject_symlinks(local)
    if not local.resolve().is_relative_to(root):
        raise ValueError('path escapes repository: ' + name)
    return local


def reject_symlinks(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('symlink forbidden: ' + str(path))


def regular_bytes(root, name):
    path = safe_path(root, name)
    if not path.is_file():
        raise ValueError('required regular file: ' + name)
    return path.read_bytes()


def version(root, tag):
    value = subprocess.check_output(
        ['make', '--no-print-directory', '-s', 'version'], cwd=root, text=True).strip()
    if not re.fullmatch(VERSION_PATTERN, value) or tag != 'v' + value:
        raise ValueError('tag/version mismatch')
    if 'GITHUB_REPOSITORY' in os.environ and os.environ['GITHUB_REPOSITORY'] != REPOSITORY:
        raise ValueError('workflow repository must match canonical Project Unit identity')
    return value


def payload(root, tag):
    root = root.resolve()
    version(root, tag)
    files = {}
    for name in REQUIRED_FILES:
        data = regular_bytes(root, name)
        if not name.startswith('licenses/'):
            files[name] = data
    for directory in ('src', 'licenses'):
        source = safe_path(root, directory)
        if not source.is_dir():
            raise ValueError('required directory: ' + directory)
        for local in sorted(source.rglob('*')):
            name = local.relative_to(root).as_posix()
            safe_path(root, name)
            if local.is_dir():
                continue
            data = regular_bytes(root, name)
            deployed = local.relative_to(source).as_posix() if directory == 'src' else name
            if deployed in files:
                raise ValueError('duplicate deployment output: ' + deployed)
            files[deployed] = data
    return files


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
    data = archive(payload(root, tag))
    reject_symlinks(out.absolute())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)


def identity(tag):
    root = Path(__file__).resolve().parents[1]
    version(root, tag)
    if os.environ['GITHUB_REPOSITORY'] != REPOSITORY:
        raise ValueError('workflow repository must match canonical Project Unit identity')
    def commit(ref):
        return subprocess.check_output(['git', 'rev-parse', ref + '^{commit}'], cwd=root).strip()
    if commit('HEAD') != commit(tag) or commit('HEAD') != commit(os.environ['GITHUB_SHA']):
        raise ValueError('tag must match checkout HEAD and workflow SHA')


def absent(repository, tag, token):
    if repository != REPOSITORY or not re.fullmatch('v' + VERSION_PATTERN, tag) or not token:
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
    parser.add_argument('command', choices=['stage', 'identity', 'absent'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, default=Path('build.nosync/theme.gams.zip'))
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    if args.command == 'stage':
        stage(args.root.resolve(), args.out, args.tag)
    elif args.command == 'identity':
        identity(args.tag)
    else:
        absent(os.environ['GITHUB_REPOSITORY'], args.tag, os.environ['GH_TOKEN'])

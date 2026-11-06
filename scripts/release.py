#!/usr/bin/env python3
"""Matching-tag release identity and availability checks."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request


REPOSITORY = 'kkgams/theme.gams'
VERSION_PATTERN = r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'


def version(root, tag):
    value = subprocess.check_output(
        ['make', '--no-print-directory', '-s', 'version'], cwd=root, text=True).strip()
    if not re.fullmatch(VERSION_PATTERN, value) or tag != 'v' + value:
        raise ValueError('tag/version mismatch')
    if 'GITHUB_REPOSITORY' in os.environ and os.environ['GITHUB_REPOSITORY'] != REPOSITORY:
        raise ValueError('workflow repository must match canonical Project Unit identity')
    return value


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
    parser.add_argument('command', choices=['identity', 'absent'])
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    if args.command == 'identity':
        identity(args.tag)
    else:
        absent(os.environ['GITHUB_REPOSITORY'], args.tag, os.environ['GH_TOKEN'])

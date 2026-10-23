"""Read-only version policy for chart changes between Git commits."""

import argparse
from dataclasses import dataclass
import re
import subprocess
import sys

import yaml


SEMVER = re.compile(
    r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
    r'(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
    r'(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
)


@dataclass(frozen=True)
class Version:
    core: tuple
    prerelease: tuple

    @classmethod
    def parse(cls, value):
        match = SEMVER.fullmatch(value) if isinstance(value, str) else None
        if not match:
            raise ValueError('version must be a quoted or string SemVer (for example 1.2.3)')
        prerelease = tuple(match[4].split('.')) if match[4] else ()
        if any(part.isdigit() and len(part) > 1 and part.startswith('0')
               for part in prerelease):
            raise ValueError('numeric prerelease identifiers cannot have leading zeroes')
        return cls(tuple(int(match[i]) for i in (1, 2, 3)), prerelease)

    def greater_than(self, other):
        if self.core != other.core:
            return self.core > other.core
        if not self.prerelease or not other.prerelease:
            return bool(other.prerelease) and not self.prerelease
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            if left.isdigit() and right.isdigit():
                return int(left) > int(right)
            if left.isdigit() != right.isdigit():
                return not left.isdigit()
            return left > right
        return len(self.prerelease) > len(other.prerelease)


def git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'git {args[0]} failed: {result.stderr.strip()}')
    return result.stdout


def chart_files(commit):
    return set(git('ls-tree', '-r', '--name-only', '-z', commit, '--', 'charts/').split('\0'))


def read_version(commit, path):
    try:
        metadata = yaml.safe_load(git('show', f'{commit}:{path}'))
        if not isinstance(metadata, dict):
            raise ValueError('Chart.yaml must contain a mapping')
        value = metadata.get('version')
        return value, Version.parse(value)
    except (ValueError, yaml.YAMLError) as error:
        raise ValueError(f'{path} at {commit}: {error}') from error


def check(base_ref, head_ref):
    base = git('rev-parse', '--verify', '--end-of-options', f'{base_ref}^{{commit}}').strip()
    head = git('rev-parse', '--verify', '--end-of-options', f'{head_ref}^{{commit}}').strip()
    print(f'Target: {base}\nHead: {head}')
    ancestor = git('merge-base', base, head).strip()
    changed = git('diff', '--no-renames', '--name-only', '-z', ancestor, head, '--', 'charts/')
    names = {path.split('/')[1] for path in changed.split('\0')
             if path.startswith('charts/') and len(path.split('/')) >= 3}
    head_files = chart_files(head)
    names = sorted(name for name in names if any(
        path.startswith(f'charts/{name}/') for path in head_files))
    if not names:
        print('No changed surviving charts; no version bump required.')
        return 0
    if ancestor != base:
        raise ValueError('Chart changes require a branch up to date with the current target. '
                         'Merge or rebase the target branch and rerun validation.')
    base_files = chart_files(base)
    errors = []
    for name in names:
        path = f'charts/{name}/Chart.yaml'
        try:
            current_text, current = read_version(head, path)
            if path in base_files:
                previous_text, previous = read_version(base, path)
                if not current.greater_than(previous):
                    raise ValueError(f'{path}: version {current_text} must be strictly greater '
                                     f'than target version {previous_text}. Manually bump version '
                                     'in Chart.yaml and push the updated PR head '
                                     '(including fork PRs); appVersion alone is insufficient.')
            print(f'{path}: {current_text} OK')
        except ValueError as error:
            errors.append(str(error))
    if errors:
        raise ValueError('\n'.join(errors))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref', required=True, help='current target branch ref')
    parser.add_argument('--head-ref', default='HEAD', help='exact PR head commit or ref')
    args = parser.parse_args()
    try:
        return check(args.base_ref, args.head_ref)
    except ValueError as error:
        print(f'Chart version check failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""Check live PR snapshots and publish a single staged chart-version candidate."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def run(*args):
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(f'{args[0]} {args[1]} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def context():
    keys = ('REPOSITORY', 'PR_NUMBER', 'BASE_REF', 'HEAD_REF', 'EXPECTED_HEAD_SHA')
    values = {key: os.environ.get(key, '') for key in keys}
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', values['REPOSITORY']):
        raise ValueError('Invalid repository name')
    if not re.fullmatch(r'[1-9][0-9]*', values['PR_NUMBER']):
        raise ValueError('Invalid PR number')
    if not re.fullmatch(r'[0-9a-f]{40}', values['EXPECTED_HEAD_SHA']):
        raise ValueError('Expected a full PR head SHA')
    for key in ('BASE_REF', 'HEAD_REF'):
        run('git', 'check-ref-format', 'refs/heads/' + values[key])
    if run('git', 'rev-parse', 'HEAD') != values['EXPECTED_HEAD_SHA']:
        raise ValueError('Checkout is not the expected event head; run validation on the current PR head')
    return values


def check_metadata(values, writer=False):
    metadata = json.loads(run('gh', 'api',
                              f"repos/{values['REPOSITORY']}/pulls/{values['PR_NUMBER']}"))
    if not isinstance(metadata, dict):
        raise ValueError('Expected pull request metadata from GitHub')
    head = metadata.get('head') or {}
    base = metadata.get('base') or {}
    if (metadata.get('state') != 'open' or head.get('sha') != values['EXPECTED_HEAD_SHA']
            or head.get('ref') != values['HEAD_REF'] or base.get('ref') != values['BASE_REF']
            or (base.get('repo') or {}).get('full_name') != values['REPOSITORY']):
        raise ValueError('PR head or target changed, or PR closed; use the current open PR head')
    if writer and ((head.get('repo') or {}).get('full_name') != values['REPOSITORY']
                   or (metadata.get('user') or {}).get('login') == 'dependabot[bot]'
                   or os.environ.get('GITHUB_ACTOR') == 'dependabot[bot]'):
        raise ValueError('Fork and Dependabot PRs are read-only; manually bump chart version')


def target_sha(values):
    ref = values['BASE_REF']
    run('git', 'fetch', '--no-tags', 'origin', f'+refs/heads/{ref}:refs/remotes/origin/{ref}')
    return run('git', 'rev-parse', f'refs/remotes/origin/{ref}')


def remote_refs(values):
    output = run('git', 'ls-remote', '--heads', 'origin',
                 'refs/heads/' + values['BASE_REF'], 'refs/heads/' + values['HEAD_REF'])
    return dict((ref, sha) for sha, ref in (line.split() for line in output.splitlines()))


def check_remote(values, base, head):
    refs = remote_refs(values)
    if (refs.get('refs/heads/' + values['BASE_REF']) != base
            or refs.get('refs/heads/' + values['HEAD_REF']) != head):
        raise ValueError('Remote target or head advanced; update the branch and validate its current head')


def validate_snapshot(values):
    check_metadata(values)
    base = target_sha(values)
    expected = os.environ.get('EXPECTED_BASE_SHA')
    if expected and base != expected:
        raise ValueError('Target advanced during validation; rerun on the updated current head')
    print(f"PR snapshot: target {base}, head {values['EXPECTED_HEAD_SHA']}")
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'base_sha={base}\n')


def publish_bump(values):
    check_metadata(values, writer=True)
    base = target_sha(values)
    head = values['EXPECTED_HEAD_SHA']
    check_remote(values, base, head)
    staged = run('git', 'diff', '--cached', '--name-only', '-z')
    paths = staged.rstrip('\0').split('\0') if staged else []
    if any(not re.fullmatch(r'charts/[^/]+/Chart\.yaml', path) for path in paths):
        raise ValueError('Only chart metadata may be staged for the version commit')
    if paths:
        run('git', 'merge-base', '--is-ancestor', base, head)
        run('git', 'commit', '-m', 'chore: Bump chart versions for Docker image updates')
    final = run('git', 'rev-parse', 'HEAD')
    checker = Path(__file__).with_name('check_chart_versions.py')
    print(run(sys.executable, str(checker), '--base-ref', base, '--head-ref', final))
    check_metadata(values, writer=True)
    check_remote(values, base, head)
    if paths:
        run('git', 'push', 'origin', f"HEAD:refs/heads/{values['HEAD_REF']}")
        check_remote(values, base, final)
    print(f'Final PR head: {final}. Version policy passed; full final-head validation is still required. '
          'On the PR page approve workflows for this exact SHA, then require Validate Charts to pass. '
          'If no run appears, follow the documented human empty-commit recovery. '
          'Rerunning an older event does not validate this head.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('validate-snapshot', 'publish-bump'))
    args = parser.parse_args()
    try:
        values = context()
        if args.mode == 'validate-snapshot':
            validate_snapshot(values)
        else:
            publish_bump(values)
        return 0
    except (ValueError, OSError) as error:
        print(f'PR automation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

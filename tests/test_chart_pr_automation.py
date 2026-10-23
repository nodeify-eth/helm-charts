import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUTOMATION = ROOT / '.github/scripts/chart_pr_automation.py'


class ChartPRAutomationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        self.repo = self.work / 'repo'
        self.repo.mkdir()
        self.remote = self.work / 'origin.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.com')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.write('charts/one/Chart.yaml', 'version: 1.2.3\nappVersion: v1\n')
        self.commit()
        self.git('branch', '-M', 'main')
        self.git('push', '-q', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-qb', 'feature')
        self.write('charts/one/Chart.yaml', 'version: 1.2.3\nappVersion: v2\n')
        self.commit()
        self.git('push', '-q', 'origin', 'feature')
        self.head = self.git('rev-parse', 'HEAD')
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        self.calls = self.work / 'calls'
        self.pushes = self.work / 'pushes'
        self.overrides = self.work / 'metadata.json'
        self.overrides.write_text('{}')
        stub = self.bin / 'gh'
        stub.write_text('#!' + sys.executable + '\n' + '''import json, os, subprocess, sys
from pathlib import Path
assert sys.argv[1:] == ['api', 'repos/example/charts/pulls/7'], sys.argv
p = Path(os.environ['GH_STUB_CALLS'])
calls = p.read_text().splitlines() if p.exists() else []
p.write_text('\\n'.join(calls + ['read pull request']) + '\\n')
sha = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/feature'], text=True).split()[0]
data = {'state': 'open', 'head': {'sha': sha, 'ref': 'feature', 'repo': {'full_name': 'example/charts'}},
        'base': {'ref': 'main', 'repo': {'full_name': 'example/charts'}}, 'user': {'login': 'author'}}
override = json.loads(Path(os.environ['GH_STUB_METADATA']).read_text())
if 'on_second_read' in override and calls:
    override = override['on_second_read']
else:
    override.pop('on_second_read', None)
for key, value in override.items():
    data[key] = value
print(json.dumps(data))
''')
        stub.chmod(0o755)
        git_stub = self.bin / 'git'
        git_stub.write_text('#!' + sys.executable + '\n' + f'''import os, sys
from pathlib import Path
if sys.argv[1:2] == ['push']:
    with Path(os.environ['GH_STUB_PUSHES']).open('a') as output:
        output.write('push attempt\\n')
os.execv({shutil.which('git')!r}, ['git', *sys.argv[1:]])
''')
        git_stub.chmod(0o755)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True,
                                       stderr=subprocess.PIPE).strip()

    def write(self, path, content):
        destination = self.repo / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def remote_head(self):
        return self.git('ls-remote', 'origin', 'refs/heads/feature').split()[0]

    def run_automation(self, success, mode='publish-bump', **extra):
        env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
               'REPOSITORY': 'example/charts', 'PR_NUMBER': '7', 'BASE_REF': 'main',
               'HEAD_REF': 'feature', 'EXPECTED_HEAD_SHA': self.head,
               'GH_STUB_CALLS': str(self.calls), 'GH_STUB_METADATA': str(self.overrides),
               'GH_STUB_PUSHES': str(self.pushes),
               **extra}
        result = subprocess.run([sys.executable, str(AUTOMATION), mode], cwd=self.repo,
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def stage_bump(self):
        self.write('charts/one/Chart.yaml', 'version: 1.2.4\nappVersion: v2\n')
        self.git('add', 'charts/one/Chart.yaml')

    def run_bump_shell(self, success=True):
        workflow = yaml.safe_load((ROOT / '.github/workflows/update-index.yaml').read_text())
        steps = workflow['jobs']['bump-version']['steps']
        output = self.work / 'output'
        result = subprocess.run(['bash', '-e', '-c', steps[1]['run']], cwd=self.repo,
                                env={**os.environ, 'BASE_REF': 'main', 'GITHUB_OUTPUT': str(output)},
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if not output.exists():
            return
        lines = output.read_text().splitlines()
        changed = '\n'.join(lines[1:-1])
        result = subprocess.run(['bash', '-e', '-c', steps[2]['run']], cwd=self.repo,
                                env={**os.environ, 'BASE_REF': 'main', 'CHANGED_CHARTS': changed},
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)

    def test_one_commit_then_noop_and_stale_original(self):
        self.run_bump_shell()
        self.run_automation(True)
        final = self.remote_head()
        self.assertNotEqual(final, self.head)
        self.assertEqual(self.git('rev-list', '--count', self.head + '..' + final), '1')
        self.assertIn('1.2.4', self.git('show', final + ':charts/one/Chart.yaml'))
        original = self.head
        self.head = final
        self.run_bump_shell()
        self.assertIn(final, self.run_automation(True))
        self.assertEqual(self.remote_head(), final)
        self.assertEqual(self.pushes.read_text().splitlines(), ['push attempt'])
        self.head = original
        self.run_automation(False)
        self.assertEqual(self.remote_head(), final)

    def test_manual_versions_and_missing_bump(self):
        for version, success in (('1.2.4', True), ('1.2.3+manual', False),
                                 ('"1.2.3"', False), ('1.2.2', False),
                                 ('1.2.4-rc.1', True), ('invalid', False)):
            with self.subTest(version=version):
                self.git('reset', '--hard', self.head)
                self.write('charts/one/Chart.yaml', f'version: {version}\nappVersion: v2\n')
                self.commit()
                self.git('push', '-q', 'origin', 'feature')
                self.head = self.git('rev-parse', 'HEAD')
                self.run_bump_shell()
                self.run_automation(success)
                self.assertEqual(self.remote_head(), self.head)
        self.run_automation(False)

    def test_fork_closed_changed_base_and_dependabot(self):
        overrides = ({'head': {'sha': self.head, 'ref': 'feature', 'repo': {'full_name': 'fork/charts'}}},
                     {'state': 'closed'}, {'base': {'ref': 'other'}},
                     {'user': {'login': 'dependabot[bot]'}})
        for metadata in overrides:
            with self.subTest(metadata=metadata):
                self.overrides.write_text(json.dumps(metadata))
                self.stage_bump()
                self.run_automation(False)
                self.assertEqual(self.remote_head(), self.head)
                self.assertFalse(self.pushes.exists())
        self.overrides.write_text('{}')
        self.run_automation(False, GITHUB_ACTOR='dependabot[bot]')
        self.assertEqual(self.remote_head(), self.head)
        self.assertFalse(self.pushes.exists())

    def test_non_fast_forward_is_not_retried(self):
        other = subprocess.check_output(['git', 'commit-tree', 'HEAD^{tree}', '-p', self.head,
                                         '-m', 'concurrent human commit'], cwd=self.repo,
                                        text=True).strip()
        self.git('push', '-q', 'origin', other + ':refs/heads/other')
        hook = self.repo / '.git/hooks/pre-push'
        hook.write_text('#!/bin/sh\ngit --git-dir="' + str(self.remote)
                        + '" update-ref refs/heads/feature ' + other + '\n')
        hook.chmod(0o755)
        self.stage_bump()
        self.run_automation(False)
        self.assertEqual(self.remote_head(), other)
        self.assertEqual(self.pushes.read_text().splitlines(), ['push attempt'])

    def test_template_only_requires_manual_bump(self):
        self.write('charts/one/Chart.yaml', 'version: 1.2.3\nappVersion: v1\n')
        self.write('charts/one/templates/example.yaml', 'kind: ConfigMap\n')
        self.commit()
        self.git('push', '-q', 'origin', 'feature')
        self.head = self.git('rev-parse', 'HEAD')
        self.run_bump_shell()
        self.run_automation(False)
        self.assertEqual(self.remote_head(), self.head)
        self.assertFalse(self.pushes.exists())

    def test_head_race_before_push(self):
        self.overrides.write_text(json.dumps({'on_second_read': {'state': 'closed'}}))
        self.stage_bump()
        self.run_automation(False)
        self.assertEqual(self.remote_head(), self.head)

    def test_advanced_target_requires_update(self):
        self.git('checkout', '-q', 'main')
        self.write('README.md', 'target advanced\n')
        self.commit()
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', '-q', 'feature')
        self.stage_bump()
        self.run_automation(False)
        self.assertEqual(self.remote_head(), self.head)

    def test_snapshot_checks_exact_head_and_target(self):
        self.run_automation(True, 'validate-snapshot')
        self.run_automation(False, 'validate-snapshot', EXPECTED_BASE_SHA='0' * 40)
        self.run_automation(False, 'validate-snapshot', EXPECTED_HEAD_SHA='0' * 40)
        self.assertEqual(self.remote_head(), self.head)

    def test_fork_snapshot_is_read_only(self):
        self.overrides.write_text(json.dumps({'head': {
            'sha': self.head, 'ref': 'feature', 'repo': {'full_name': 'fork/charts'}}}))
        self.run_automation(True, 'validate-snapshot')
        self.assertFalse(self.pushes.exists())

    def test_prerelease_baseline_requires_manual_bump(self):
        self.git('checkout', '-q', 'main')
        self.git('merge', '--ff-only', 'feature')
        self.write('charts/one/Chart.yaml', 'version: 1.2.3-rc.1\nappVersion: v2\n')
        self.commit()
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', '-q', 'feature')
        self.git('merge', '--ff-only', 'main')
        self.write('charts/one/Chart.yaml', 'version: 1.2.3-rc.1\nappVersion: v3\n')
        self.commit()
        self.git('push', '-q', 'origin', 'feature')
        self.head = self.git('rev-parse', 'HEAD')
        self.run_bump_shell(False)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.remote_head(), self.head)

    def test_human_empty_commit_recovery_has_no_second_bump(self):
        self.run_bump_shell()
        self.run_automation(True)
        final = self.remote_head()
        self.git('commit', '--allow-empty', '-qm', 'request current head validation')
        self.git('push', '-q', 'origin', 'feature')
        self.head = self.git('rev-parse', 'HEAD')
        self.assertNotEqual(self.head, final)
        self.assertEqual(self.git('rev-parse', self.head + '^{tree}'),
                         self.git('rev-parse', final + '^{tree}'))
        self.run_bump_shell()
        self.run_automation(True)
        self.run_automation(True, 'validate-snapshot')
        self.assertEqual(self.remote_head(), self.head)
        self.assertEqual(self.git('rev-list', '--count', final + '..HEAD'), '1')

    def test_workflow_writer_contract(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/update-index.yaml').read_text())
        job = workflow['jobs']['bump-version']
        self.assertIn('head.repo.full_name == github.repository', job['if'])
        self.assertIn("github.actor != 'dependabot[bot]'", job['if'])
        self.assertIn("github.event.pull_request.user.login != 'dependabot[bot]'", job['if'])
        self.assertEqual(job['permissions'], {'contents': 'write', 'pull-requests': 'read'})
        self.assertEqual(job['steps'][0]['with']['ref'], '${{ github.event.pull_request.head.sha }}')
        self.assertFalse(job['concurrency']['cancel-in-progress'])
        self.assertNotIn('pull_request_target', (ROOT / '.github/workflows/update-index.yaml').read_text())


if __name__ == '__main__':
    unittest.main()

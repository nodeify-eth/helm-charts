from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / '.github/scripts/check_chart_versions.py'


class ChartVersionsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.com')
        for name in ('one', 'two'):
            self.write(f'charts/{name}/Chart.yaml', 'version: 1.2.3\nappVersion: v1\n')
            self.write(f'charts/{name}/values.yaml', 'enabled: true\n')
        self.commit()
        self.git('branch', 'target')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True).strip()

    def write(self, path, text):
        destination = self.repo / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def check(self, success, message=None):
        before = self.git('status', '--porcelain')
        result = subprocess.run([sys.executable, str(CHECK), '--base-ref', 'target',
                                 '--head-ref', 'HEAD'], cwd=self.repo, text=True,
                                capture_output=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        if message:
            self.assertIn(message, result.stdout + result.stderr)
        self.assertEqual(self.git('status', '--porcelain'), before)
        return result.stdout + result.stderr

    def test_packaged_changes_require_bump(self):
        for path in ('templates/deployment.yaml', 'values.yaml', 'README.md', 'Chart.yaml'):
            with self.subTest(path=path):
                self.git('reset', '--hard', 'target')
                self.git('clean', '-fd')
                if path == 'Chart.yaml':
                    self.write('charts/one/Chart.yaml', 'version: 1.2.3\nappVersion: v2\n')
                else:
                    self.write(f'charts/one/{path}', 'changed\n')
                self.commit()
                self.check(False, 'strictly greater')

    def test_manual_versions_and_repeat_runs(self):
        for version, success in (('1.2.4', True), ('2.0.0', True), ('1.2.3', False),
                                 ('1.2.2', False), ('1.2.3+build.2', False),
                                 ('1.2.4-alpha.1', True)):
            with self.subTest(version=version):
                self.git('reset', '--hard', 'target')
                self.write('charts/one/Chart.yaml', f'version: "{version}"\nappVersion: v2\n')
                self.commit()
                self.assertEqual(self.check(success), self.check(success))

    def test_new_deleted_and_multiple_charts(self):
        self.write('charts/new/Chart.yaml', 'version: 0.1.0-alpha+build\n')
        shutil.rmtree(self.repo / 'charts/two')
        self.commit()
        self.check(True)
        self.write('charts/one/values.yaml', 'changed\n')
        self.commit()
        self.check(False, 'charts/one')
        self.write('charts/one/Chart.yaml', 'version: 1.2.4\n')
        self.commit()
        self.check(True)

    def test_missing_or_invalid_versions(self):
        for content in ('appVersion: v2\n', 'version: 1.2\n', 'version: 01.2.3\n',
                        'version: 1.2.3-01\n', 'version: 1.2.3-\n',
                        'version: 1.2.3+\n', 'version: [\n', '[]\n', 'version: 123\n'):
            with self.subTest(content=content):
                self.git('reset', '--hard', 'target')
                self.write('charts/new/Chart.yaml', content)
                self.commit()
                self.check(False, 'charts/new/Chart.yaml')

    def test_file_deletion_and_cross_chart_move(self):
        (self.repo / 'charts/one/values.yaml').unlink()
        self.commit()
        self.check(False, 'charts/one')
        self.git('reset', '--hard', 'target')
        self.git('mv', 'charts/one/values.yaml', 'charts/two/moved.yaml')
        self.write('charts/two/Chart.yaml', 'version: 1.2.4\n')
        self.commit()
        self.check(False, 'charts/one')
        self.write('charts/one/Chart.yaml', 'version: 1.2.4\n')
        self.commit()
        self.check(True)

    def test_target_advancement_and_unrelated_changes(self):
        self.write('charts/one/Chart.yaml', 'version: 1.2.4\n')
        self.commit()
        head = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-q', 'target')
        self.write('README.md', 'target advanced\n')
        self.commit()
        self.git('checkout', '-q', '--detach', head)
        self.check(False, 'up to date')
        self.git('merge', '-qm', 'merge target', 'target')
        self.check(True)
        self.git('checkout', '-q', 'target')
        self.write('charts/one/Chart.yaml', 'version: 1.2.4\n')
        self.commit()
        self.git('checkout', '-q', '--detach', head)
        self.git('merge', '-qm', 'merge target', 'target')
        self.write('charts/one/values.yaml', 'changed\n')
        self.commit()
        self.check(False, 'strictly greater')
        self.write('charts/one/Chart.yaml', 'version: 1.2.5\n')
        self.commit()
        self.check(True)
        self.git('checkout', '-q', '--detach', head + '~1')
        self.write('CONTRIBUTING.md', 'docs only\n')
        self.commit()
        self.check(True)

    def test_prerelease_precedence(self):
        versions = ('1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-alpha.beta',
                    '1.0.0-beta', '1.0.0-beta.2', '1.0.0-beta.11',
                    '1.0.0-rc.1', '1.0.0')
        for lower, higher in zip(versions, versions[1:]):
            with self.subTest(lower=lower, higher=higher):
                self.write('charts/one/Chart.yaml', f'version: {lower}\n')
                self.git('add', '.')
                self.git('commit', '--allow-empty', '-qm', 'prerelease base')
                self.git('branch', '-f', 'target', 'HEAD')
                self.write('charts/one/Chart.yaml', f'version: {higher}\n')
                self.commit()
                self.check(True)


if __name__ == '__main__':
    unittest.main()

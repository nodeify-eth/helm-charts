import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / '.github/scripts/generate_chart_docs.py'
GENERATED = b'# Tier 2 fixture\n\nGenerated values stay in this chart.\n'
FAKE_TOOL = r'''
import argparse
import json
import os
from pathlib import Path
import sys

with Path(os.environ['FAKE_HELM_DOCS_LOG']).open('a') as log:
    log.write(json.dumps({'args': sys.argv[1:], 'cwd': os.getcwd()}) + '\n')
if sys.argv[1:] == ['--version']:
    print(os.environ.get('FAKE_HELM_DOCS_VERSION', 'helm-docs version 1.14.2'))
    sys.exit(int(os.environ.get('FAKE_VERSION_EXIT', '0')))
parser = argparse.ArgumentParser()
parser.add_argument('--chart-search-root', required=True)
parser.add_argument('--template-files', required=True)
parser.add_argument('--sort-values-order', required=True)
parser.add_argument('--log-level', required=True)
parser.add_argument('--dry-run', action='store_true', required=True)
args = parser.parse_args()
if os.environ.get('FAKE_RENDER_FAIL'):
    print('fixture rendering failed', file=sys.stderr)
    sys.exit(9)
if os.environ.get('FAKE_EMPTY_OUTPUT'):
    sys.exit(0)
print('fixture diagnostic on stderr', file=sys.stderr)
sys.stdout.buffer.write((Path(args.chart_search_root) / 'generated.fixture.md').read_bytes())
'''


class ChartDocsTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(GENERATOR.is_file(), 'Documentation wrapper is not implemented')
        self.directory = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.chart = self.repo / 'charts/substreams-tier-2'
        self.chart.mkdir(parents=True)
        scripts = self.repo / '.github/scripts'
        scripts.mkdir(parents=True)
        self.generator = scripts / GENERATOR.name
        shutil.copy2(GENERATOR, self.generator)
        (self.chart / 'Chart.yaml').write_text('name: substreams-tier-2\nversion: 1.1.7\n')
        (self.chart / 'values.yaml').write_text('enabled: true\n')
        (self.chart / 'README.md.gotmpl').write_text('fixture template\n')
        (self.chart / 'README.md').write_text('stale documentation\n')
        (self.chart / 'generated.fixture.md').write_bytes(GENERATED)
        other = self.repo / 'charts/firehose-core'
        other.mkdir()
        (other / 'README.md').write_text('unapproved chart must remain untouched\n')
        (self.repo / 'nested').mkdir()
        self.bin = self.repo / 'bin'
        self.bin.mkdir()
        self.tool = self.bin / 'helm-docs'
        self.tool.write_text(f'#!{sys.executable}\n' + FAKE_TOOL)
        self.tool.chmod(0o755)
        self.log = self.repo / 'calls.jsonl'
        self.env = {**os.environ, 'PATH': str(self.bin),
                    'FAKE_HELM_DOCS_LOG': str(self.log)}

    def run_generator(self, *args, **env):
        return subprocess.run([sys.executable, str(self.generator), *args],
                              cwd=self.repo / 'nested', env={**self.env, **env},
                              capture_output=True, text=True)

    def snapshot(self):
        return {str(path.relative_to(self.repo)): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.repo.rglob('*')
                if path.is_file() and path != self.log}

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()
                ] if self.log.exists() else []

    def test_generation_is_repeatable_and_writes_only_selected_readme(self):
        before = self.snapshot()
        result = self.run_generator('substreams-tier-2')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.chart / 'README.md').read_bytes(), GENERATED)
        after = self.snapshot()
        expected_path = 'charts/substreams-tier-2/README.md'
        self.assertEqual({path for path in before if before[path] != after[path]},
                         {expected_path})
        self.assertEqual(before.keys(), after.keys())
        result = self.run_generator('substreams-tier-2')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.chart / 'README.md').read_bytes(), GENERATED)
        render = self.calls()[1]
        self.assertEqual(render['cwd'], str(self.repo))
        args = render['args']
        self.assertEqual(args[args.index('--chart-search-root') + 1], str(self.chart))
        self.assertEqual(args[args.index('--template-files') + 1], 'README.md.gotmpl')
        self.assertEqual(args[args.index('--sort-values-order') + 1], 'alphanum')
        self.assertIn('--dry-run', args)

    def test_check_reports_drift_and_never_rewrites_files(self):
        before = self.snapshot()
        result = self.run_generator('--check', 'substreams-tier-2')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('out of date', result.stderr)
        self.assertEqual(self.snapshot(), before)
        (self.chart / 'README.md').write_bytes(GENERATED)
        before = self.snapshot()
        for _ in range(2):
            result = self.run_generator('--check', 'substreams-tier-2')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.snapshot(), before)

    def test_wrong_or_unrecognized_tool_version_stops_before_rendering(self):
        before = self.snapshot()
        for version in ('helm-docs version 1.14.1', 'helm-docs version 1.14.20',
                        'helm-docs version 1.14.2-custom', 'unknown'):
            with self.subTest(version=version):
                result = self.run_generator('substreams-tier-2',
                                            FAKE_HELM_DOCS_VERSION=version)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('1.14.2', result.stderr)
                self.assertEqual(self.snapshot(), before)
        self.assertTrue(all(call['args'] == ['--version'] for call in self.calls()))

    def test_failed_version_command_does_not_render_or_write(self):
        before = self.snapshot()
        result = self.run_generator('substreams-tier-2', FAKE_VERSION_EXIT='3')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('version', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual([call['args'] for call in self.calls()], [['--version']])

    def test_missing_tool_fails_without_installing_or_writing(self):
        self.tool.unlink()
        before = self.snapshot()
        result = self.run_generator('substreams-tier-2')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('helm-docs 1.14.2', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.calls(), [])

    def test_unapproved_paths_and_implicit_all_chart_requests_do_not_invoke_tool(self):
        before = self.snapshot()
        for args in ((), ('firehose-core',), ('../substreams-tier-2',),
                     ('charts/substreams-tier-2',), (str(self.chart),),
                     ('substreams-tier-2/../firehose-core',), ('--all',),
                     ('substreams-tier-2', 'firehose-core')):
            with self.subTest(args=args):
                result = self.run_generator(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(self.calls(), [])

    def test_missing_template_fails_before_tool_invocation(self):
        (self.chart / 'README.md.gotmpl').unlink()
        before = self.snapshot()
        result = self.run_generator('substreams-tier-2')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('README.md.gotmpl', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.calls(), [])

    def test_symlinked_chart_or_readme_cannot_escape_selected_chart(self):
        outside = self.repo / 'outside'
        shutil.copytree(self.chart, outside)
        shutil.rmtree(self.chart)
        self.chart.symlink_to(outside, target_is_directory=True)
        before = self.snapshot()
        result = self.run_generator('substreams-tier-2')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.calls(), [])
        self.chart.unlink()
        shutil.copytree(outside, self.chart)
        readme = self.chart / 'README.md'
        readme.unlink()
        readme.symlink_to(outside / 'README.md')
        before = self.snapshot()
        result = self.run_generator('substreams-tier-2')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.calls(), [])

    def test_rendering_failure_or_empty_output_preserves_readme(self):
        before = self.snapshot()
        for env in ({'FAKE_RENDER_FAIL': '1'}, {'FAKE_EMPTY_OUTPUT': '1'}):
            with self.subTest(env=env):
                result = self.run_generator('substreams-tier-2', **env)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(self.snapshot(), before)
        self.assertIn('fixture rendering failed',
                      self.run_generator('substreams-tier-2',
                                         FAKE_RENDER_FAIL='1').stderr)


if __name__ == '__main__':
    unittest.main()

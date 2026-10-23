import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
STEPS = yaml.safe_load((ROOT / '.github/workflows/update-index.yaml').read_text())['jobs']['bump-version']['steps']


class ChartVersionWorkflowTest(unittest.TestCase):
    def test_multiple_charts_and_repeat_run(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)

            def git(*args):
                return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()

            git('init', '-q')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.com')
            for name in ('one', 'two'):
                chart = repo / 'charts' / name / 'Chart.yaml'
                chart.parent.mkdir(parents=True)
                chart.write_text('version: 1.2.3\nappVersion: v1\n')
            git('add', '.')
            git('commit', '-qm', 'base')
            git('branch', 'origin/main')
            for chart in repo.glob('charts/*/Chart.yaml'):
                chart.write_text('version: 1.2.3\nappVersion: v2\n')
            git('commit', '-qam', 'update apps')

            def run(script, **env):
                script = script.replace('${{ github.base_ref }}', 'main')
                subprocess.run(['bash', '-e', '-c', script], cwd=repo,
                               env={**os.environ, **env}, check=True)

            output = repo / 'output'
            run(STEPS[1]['run'], GITHUB_OUTPUT=str(output), BASE_REF='main')
            lines = output.read_text().splitlines()
            if lines[0].startswith('changed_charts<<'):
                delimiter = lines[0].split('<<', 1)[1]
                self.assertEqual(lines[-1], delimiter)
                changed = '\n'.join(lines[1:-1])
            else:
                self.assertEqual(len(lines), 1, 'GitHub output has invalid bare lines')
                changed = lines[0].split('=', 1)[1]
            self.assertEqual(set(changed.splitlines()), {'charts/one/Chart.yaml', 'charts/two/Chart.yaml'})
            bump = STEPS[2]['run'].split('if git diff --staged --quiet;')[0]
            bump = bump.replace('${{ steps.check-changes.outputs.changed_charts }}', changed)
            for _ in range(2):
                run(bump, CHANGED_CHARTS=changed, BASE_REF='main')
                for chart in repo.glob('charts/*/Chart.yaml'):
                    self.assertIn('version: 1.2.4\n', chart.read_text())


if __name__ == '__main__':
    unittest.main()

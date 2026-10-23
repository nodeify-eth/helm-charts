"""Generate or check documentation for one explicitly approved Helm chart."""

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
HELM_DOCS_VERSION = '1.14.2'
APPROVED_CHARTS = ('substreams-tier-2',)


def helm_docs(*args):
    try:
        result = subprocess.run(['helm-docs', *args], cwd=ROOT, capture_output=True)
    except FileNotFoundError as error:
        raise ValueError(f'helm-docs {HELM_DOCS_VERSION} is required on PATH; '
                         'no tools are installed by this command.') from error
    if result.returncode:
        detail = result.stderr.decode(errors='replace').strip()
        raise ValueError(f'helm-docs {args[0]} failed (exit {result.returncode}): {detail}')
    return result.stdout


def generate(chart_name, check):
    chart = ROOT / 'charts' / chart_name
    if chart.is_symlink() or chart.resolve() != chart or not chart.is_dir():
        raise ValueError(f'{chart}: expected a chart directory without symlinks')
    for name in ('Chart.yaml', 'values.yaml', 'README.md.gotmpl', 'README.md'):
        path = chart / name
        if path.is_symlink() or path.resolve() != path:
            raise ValueError(f'{path}: symlinks are not supported')
        if name != 'README.md' and not path.is_file():
            raise ValueError(f'{path}: required chart file is missing')

    version = helm_docs('--version').decode(errors='replace').strip()
    if version != f'helm-docs version {HELM_DOCS_VERSION}':
        raise ValueError(f'Expected helm-docs {HELM_DOCS_VERSION}; found {version!r}')
    rendered = helm_docs('--chart-search-root', str(chart),
                         '--template-files', 'README.md.gotmpl',
                         '--sort-values-order', 'alphanum',
                         '--log-level', 'error', '--dry-run')
    if not rendered.strip():
        raise ValueError('helm-docs returned empty documentation; README was not changed')
    readme = chart / 'README.md'
    current = readme.read_bytes() if readme.exists() else None
    relative = readme.relative_to(ROOT)
    if current == rendered:
        print(f'Documentation is up to date: {relative}')
        return 0
    if check:
        raise ValueError(f'{relative} is out of date; run '
                         f'python3 .github/scripts/generate_chart_docs.py {chart_name}')
    readme.write_bytes(rendered)
    print(f'Generated {relative}')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='report stale documentation without writing files')
    parser.add_argument('chart', choices=APPROVED_CHARTS,
                        help='explicit chart name; only opted-in charts are supported')
    args = parser.parse_args()
    try:
        return generate(args.chart, args.check)
    except (OSError, ValueError) as error:
        print(f'Chart documentation generation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

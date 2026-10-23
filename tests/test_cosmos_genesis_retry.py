import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENESIS = b'{"chain_id":"retry-test","validators":[]}\n'
PREVIOUS = b'{"chain_id":"previous"}\n'


class CosmosGenesisRetryTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        self.config = self.work / 'home/config'
        self.config.mkdir(parents=True)
        self.downloaded = self.config / 'genesis.json.downloaded'
        self.final = self.config / 'genesis.json'
        self.final.write_bytes(PREVIOUS)
        self.fixture = self.work / 'fixture.json'
        self.fixture.write_bytes(GENESIS)
        self.calls = self.work / 'wget-calls'
        bin_dir = self.work / 'bin'
        bin_dir.mkdir()
        wget = bin_dir / 'wget'
        wget.write_text('#!/bin/sh\nset -eu\n'
                        'while [ "$1" != "-O" ]; do shift; done\n'
                        '[ "$3" = "https://offline.invalid/genesis.json" ]\n'
                        'printf "download\\n" >> "$WGET_CALLS"\n'
                        'cp "$GENESIS_FIXTURE" "$2"\n')
        wget.chmod(0o755)
        self.env = {**os.environ,
                    'PATH': str(bin_dir) + os.pathsep + os.environ['PATH'],
                    'CHAIN_HOME': str(self.work / 'home'),
                    'GENESIS_FIXTURE': str(self.fixture),
                    'WGET_CALLS': str(self.calls),
                    'GENESIS_URL': 'https://offline.invalid/genesis.json'}

    def run_download(self, checksum):
        command = ['helm', 'template', 'retry-test', str(ROOT / 'charts/cosmos-node'),
                   '--show-only', 'templates/configmap.yaml']
        if checksum:
            command.extend(['--set-string', 'bootstrap.genesis.checksum=' + checksum])
        script = yaml.safe_load(subprocess.check_output(command, text=True))['data']['init.sh']
        # Assert the final invocation boundary before running any rendered code.
        marker = 'main "$@"'
        self.assertTrue(script.rstrip().endswith(marker))
        self.assertEqual(script.count(marker), 1)
        definitions, tail = script.rsplit(marker, 1)
        self.assertFalse(tail.strip())
        script = definitions + 'download_genesis\n'
        self.assertNotIn(marker, script)
        return subprocess.run(['sh', '-c', script], env=self.env, text=True,
                              capture_output=True, timeout=10)

    def test_checksum_failure_remains_rejected_on_second_invocation(self):
        first = self.run_download('0' * 64)
        second = self.run_download('0' * 64)
        self.assertNotEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertNotEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertFalse(self.downloaded.exists())
        self.assertEqual(self.final.read_bytes(), PREVIOUS)

    def test_rejected_download_is_not_published_or_left_temporary(self):
        result = self.run_download('0' * 64)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.downloaded.exists())
        self.assertFalse((self.config / 'genesis.json.downloaded.tmp').exists())
        self.assertEqual(self.final.read_bytes(), PREVIOUS)

    def test_legacy_mismatched_cache_fails_with_recovery_guidance(self):
        self.downloaded.write_bytes(PREVIOUS)
        result = self.run_download(hashlib.sha256(GENESIS).hexdigest())
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('checksum verification failed', result.stdout)
        self.assertIn(str(self.downloaded), result.stdout)
        self.assertIn('retry', result.stdout)
        self.assertEqual(self.downloaded.read_bytes(), PREVIOUS)
        self.assertEqual(self.final.read_bytes(), PREVIOUS)
        self.assertFalse(self.calls.exists())

    def test_cached_genesis_is_checked_against_current_digest(self):
        self.downloaded.write_bytes(GENESIS)
        first = self.run_download(hashlib.sha256(GENESIS).hexdigest())
        second = self.run_download('0' * 64)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertNotEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self.downloaded.read_bytes(), GENESIS)
        self.assertEqual(self.final.read_bytes(), PREVIOUS)
        self.assertFalse(self.calls.exists())

    def test_matching_cache_succeeds_without_downloading(self):
        self.downloaded.write_bytes(GENESIS)
        result = self.run_download(hashlib.sha256(GENESIS).hexdigest())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('checksum verified', result.stdout)
        self.assertEqual(self.downloaded.read_bytes(), GENESIS)
        self.assertEqual(self.final.read_bytes(), PREVIOUS)
        self.assertFalse(self.calls.exists())

    def test_no_checksum_preserves_download_and_cached_retry(self):
        first = self.run_download('')
        second = self.run_download('')
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self.downloaded.read_bytes(), GENESIS)
        self.assertEqual(self.final.read_bytes(), PREVIOUS)
        self.assertEqual(self.calls.read_text().splitlines(), ['download'])


if __name__ == '__main__':
    unittest.main()

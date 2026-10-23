import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENESIS = b'{"chain_id":"checksum-test","validators":[]}\n'


class CosmosGenesisTest(unittest.TestCase):
    def run_download(self, checksum, existing_genesis=None):
        command = ['helm', 'template', 'checksum-test', str(ROOT / 'charts/cosmos-node'),
                   '--show-only', 'templates/configmap.yaml']
        if checksum:
            command.extend(['--set-string', 'bootstrap.genesis.checksum=' + checksum])
        rendered = subprocess.check_output(command, text=True)
        script = yaml.safe_load(rendered)['data']['init.sh']
        # Keep the rendered definitions intact; invoke only the download helper,
        # avoiding package installation and other bootstrap network operations.
        self.assertIn('main "$@"', script, "Rendered init script must end with the main invocation")
        script = script.rsplit('main "$@"', 1)[0] + 'download_genesis\n'
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            config = work / 'home/config'
            config.mkdir(parents=True)
            if existing_genesis is not None:
                (config / 'genesis.json').write_bytes(existing_genesis)
            fixture = work / 'genesis-fixture.json'
            fixture.write_bytes(GENESIS)
            bin_dir = work / 'bin'
            bin_dir.mkdir()
            wget = bin_dir / 'wget'
            wget.write_text('#!/bin/sh\nwhile [ "$1" != "-O" ]; do shift; done\n'
                            'cp "$GENESIS_FIXTURE" "$2"\n')
            wget.chmod(0o755)
            result = subprocess.run(['sh', '-c', script], text=True, capture_output=True,
                                    env={**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH'],
                                         'CHAIN_HOME': str(work / 'home'),
                                         'GENESIS_FIXTURE': str(fixture),
                                         'GENESIS_URL': 'https://offline.invalid/genesis.json'})
            downloaded = config / 'genesis.json.downloaded'
            final = config / 'genesis.json'
            return result, downloaded.read_bytes() if downloaded.exists() else None, final.read_bytes() if final.exists() else None

    def test_correct_checksum_accepts_download_before_final_file_exists(self):
        result, downloaded, final = self.run_download(hashlib.sha256(GENESIS).hexdigest())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(downloaded, GENESIS)
        self.assertIsNone(final)
        self.assertIn('Genesis checksum verified', result.stdout)

    def test_wrong_checksum_rejects_download(self):
        result, _, final = self.run_download('0' * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Genesis checksum verification failed', result.stdout)
        self.assertIsNone(final)

    def test_existing_final_file_cannot_validate_different_download(self):
        previous = b'{"chain_id":"previous"}\n'
        result, _, final = self.run_download(hashlib.sha256(previous).hexdigest(), previous)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Genesis checksum verification failed', result.stdout)
        self.assertEqual(final, previous)

    def test_no_checksum_preserves_download_behavior(self):
        result, downloaded, final = self.run_download('')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(downloaded, GENESIS)
        self.assertIsNone(final)
        self.assertNotIn('Genesis checksum verified', result.stdout)


if __name__ == '__main__':
    unittest.main()

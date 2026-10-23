import base64
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ('firehose-core', 'firehose-ethereum')
REVISION = 'firehose.streamingfast.io/jwt-revision'


class FirehoseJWTTest(unittest.TestCase):
    def render(self, chart, *args, path=None):
        return subprocess.run(['helm', 'template', 'jwt-check', str(path or ROOT / 'charts' / chart),
                               '--namespace', 'jwt-check', *args], capture_output=True, text=True)

    def documents(self, result):
        self.assertEqual(result.returncode, 0, 'render failed; credential output suppressed')
        return [d for d in yaml.safe_load_all(result.stdout) if d]

    def consumers(self, docs):
        return [d['spec']['template'] for d in docs if d['kind'] in ('StatefulSet', 'Deployment')
                and any(v['name'] == 'jwt-secret' for v in d['spec']['template']['spec'].get('volumes', []))]

    def secret(self, docs):
        return next(d for d in docs if d['kind'] == 'Secret' and d['metadata']['name'] == 'jwt-check-firehose-jwt')

    def test_managed_crypto_and_shared_checksum(self):
        for chart in CHARTS:
            with self.subTest(chart=chart):
                args = ('--set', 'fullMode.components.opNode.enabled=true') if chart.endswith('ethereum') else ()
                docs = self.documents(self.render(chart, *args))
                encoded = self.secret(docs)['data']['jwt.hex']
                key = base64.b64decode(encoded, validate=True)
                self.assertTrue(bool(re.fullmatch(rb'[0-9a-fA-F]{64}', key)))
                self.assertTrue(key != hashlib.sha256(b'firehose-jwt-jwt-check-jwt-check').hexdigest().encode())
                other = self.secret(self.documents(self.render(chart)))['data']['jwt.hex']
                self.assertTrue(encoded != other, 'independent installs must generate fresh bytes')
                for pod in self.consumers(docs):
                    self.assertTrue(pod['metadata'].get('annotations', {}).get('checksum/jwt-secret') == hashlib.sha256(key).hexdigest())

    def test_external_deterministic_names_revision_and_no_managed_secret(self):
        for chart in CHARTS:
            with self.subTest(chart=chart):
                args = ['--set-string', 'fullMode.jwt.existingSecret=external-jwt', '--set-string', 'fullMode.jwt.revision=rotation-2', '--is-upgrade']
                if chart.endswith('ethereum'):
                    args += ['--set', 'fullMode.components.opNode.enabled=true']
                a, b = self.render(chart, *args), self.render(chart, *args)
                docs = self.documents(a)
                self.assertTrue(a.stdout == b.stdout, 'external renders differ')
                self.assertFalse(any(d['kind'] == 'Secret' and d['metadata']['name'] == 'jwt-check-firehose-jwt' for d in docs))
                pods = self.consumers(docs)
                self.assertEqual(len(pods), 3 if chart.endswith('ethereum') else 2)
                for pod in pods:
                    self.assertEqual(pod['metadata']['annotations'][REVISION], 'rotation-2')
                    self.assertNotIn('checksum/jwt-secret', pod['metadata']['annotations'])
                    self.assertEqual(next(v['secret']['secretName'] for v in pod['spec']['volumes'] if v['name'] == 'jwt-secret'), 'external-jwt')

    def test_reader_disabled_guard_and_external_escape(self):
        for chart in CHARTS:
            for client in (['lighthouse', 'opNode'] if chart.endswith('ethereum') else ['lighthouse']):
                with self.subTest(chart=chart, client=client):
                    args = ['--set', 'fullMode.components.reader.enabled=false', '--set', 'fullMode.components.lighthouse.enabled=false', '--set', f'fullMode.components.{client}.enabled=true', '--set', f'fullMode.components.{client}.replicas=0']
                    result = self.render(chart, *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('fullMode.jwt.existingSecret', result.stderr)
                    self.documents(self.render(chart, *args, '--set-string', 'fullMode.jwt.existingSecret=external-jwt'))

    def test_chunk_and_all_disabled_bypass(self):
        for chart in CHARTS:
            for args in [('--set', 'mode=chunk'), ('--set', 'fullMode.components.reader.enabled=false', '--set', 'fullMode.components.lighthouse.enabled=false', '--set', 'fullMode.components.opNode.enabled=false')]:
                with self.subTest(chart=chart, args=args):
                    docs = self.documents(self.render(chart, *args, '--is-upgrade'))
                    self.assertFalse(self.consumers(docs))
                    self.assertFalse(any(d['kind'] == 'Secret' and d['metadata']['name'] == 'jwt-check-firehose-jwt' for d in docs))

    def test_missing_upgrade_same_name_and_types_fail(self):
        for chart in CHARTS:
            for args, message in [(('--is-upgrade',), 'restore'), (('--set-string', 'fullMode.jwt.existingSecret=jwt-check-firehose-jwt'), 'new'), (('--set', 'fullMode.jwt.existingSecret=true'), 'string'), (('--set', 'fullMode.jwt.revision=123'), 'string')]:
                with self.subTest(chart=chart, args=args):
                    result = self.render(chart, *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)

    def test_reserved_annotations_fail(self):
        for chart in CHARTS:
            for component in (['reader', 'lighthouse', 'opNode'] if chart.endswith('ethereum') else ['reader', 'lighthouse']):
                for annotation in ('checksum/jwt-secret', REVISION):
                    with self.subTest(chart=chart, component=component, annotation=annotation):
                        with tempfile.TemporaryDirectory() as tmp:
                            values = Path(tmp) / 'values.yaml'
                            values.write_text(yaml.safe_dump({'fullMode': {'components': {component: {'enabled': True, 'podAnnotations': {annotation: 'collision'}}}}}))
                            result = self.render(chart, '-f', str(values))
                            self.assertNotEqual(result.returncode, 0)
                            self.assertIn('reserved', result.stderr)

    def test_mocked_lookup_preserves_valid_bytes_and_rejects_invalid_data(self):
        # Copied-chart lookup substitution is helper evidence, not a live API test.
        valid = [b'ab' * 32, b'AB' * 32,
                 hashlib.sha256(b'firehose-jwt-jwt-check-jwt-check').hexdigest().encode()]
        cases = [({'data': {'jwt.hex': base64.b64encode(key).decode()}}, key) for key in valid]
        cases += [(item, None) for item in [{'metadata': {'name': 'fake'}}, {'data': {}},
                  {'data': {'jwt.hex': ''}}, {'data': {'jwt.hex': 'not-base64!'}},
                  {'data': {'jwt.hex': base64.b64encode(b'g' * 64).decode()}},
                  {'data': {'jwt.hex': base64.b64encode(b'a' * 63).decode()}},
                  {'data': {'jwt.hex': 123}}]]
        import json
        for chart in CHARTS:
            for index, (response, key) in enumerate(cases):
                with self.subTest(chart=chart, case=index), tempfile.TemporaryDirectory() as tmp:
                    copied = Path(tmp) / chart
                    shutil.copytree(ROOT / 'charts' / chart, copied)
                    helper = copied / 'templates/_jwt.tpl'
                    source = helper.read_text()
                    lookup = 'lookup "v1" "Secret" .Release.Namespace $state.name'
                    self.assertEqual(source.count(lookup), 1)
                    helper.write_text(source.replace(lookup, '(' + json.dumps(json.dumps(response)) + ' | fromJson)'))
                    result = self.render(chart, '--is-upgrade', path=copied)
                    if key is None:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('managed JWT Secret', result.stderr)
                    else:
                        docs = self.documents(result)
                        self.assertTrue(self.secret(docs)['data']['jwt.hex'] == response['data']['jwt.hex'])
                        for pod in self.consumers(docs):
                            self.assertTrue(pod['metadata']['annotations']['checksum/jwt-secret'] == hashlib.sha256(key).hexdigest())

    def test_mocked_lookup_is_bypassed_or_errors_propagate(self):
        for chart in CHARTS:
            with self.subTest(chart=chart), tempfile.TemporaryDirectory() as tmp:
                copied = Path(tmp) / chart
                shutil.copytree(ROOT / 'charts' / chart, copied)
                helper = copied / 'templates/_jwt.tpl'
                helper.write_text(helper.read_text().replace('lookup "v1" "Secret" .Release.Namespace $state.name', '(fail "simulated lookup error")'))
                for args in [('--set-string', 'fullMode.jwt.existingSecret=external-jwt'),
                             ('--set', 'mode=chunk'),
                             ('--set', 'fullMode.components.reader.enabled=false', '--set', 'fullMode.components.lighthouse.enabled=false', '--set', 'fullMode.components.opNode.enabled=false')]:
                    self.documents(self.render(chart, *args, '--is-upgrade', path=copied))
                result = self.render(chart, path=copied)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('simulated lookup error', result.stderr)


if __name__ == '__main__':
    unittest.main()

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ('firehose-core', 'firehose-ethereum')
COMPONENTS = ('grpc', 'substreams')


class FirehoseIngressModesTest(unittest.TestCase):
    def render(self, chart, component=None, *, mode='chunk', method='firehose',
               enabled=True, host='ingress.example.com', replicas=1, ingress=True):
        values = {'mode': mode, 'chunkMode': {'method': method},
                  'fullMode': {'jwt': {'existingSecret': 'external-jwt'}}}
        if component:
            options = {'enabled': ingress}
            if host is not None:
                options['host'] = host
            values['fullMode']['components'] = {
                component: {'enabled': enabled, 'replicas': replicas, 'ingress': options}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'values.yaml'
            path.write_text(yaml.safe_dump(values))
            return subprocess.run(['helm', 'template', 'ingress-check',
                                   str(ROOT / 'charts' / chart), '-f', str(path)],
                                  capture_output=True, text=True)

    def documents(self, result):
        self.assertEqual(result.returncode, 0, 'render failed; output suppressed')
        return [doc for doc in yaml.safe_load_all(result.stdout) if doc]

    def test_chunk_active_ingress_is_rejected(self):
        for chart in CHARTS:
            for method in ('firehose', 'poller'):
                for component in COMPONENTS:
                    for host in ('ingress.example.com', '', None):
                        for replicas in (0, 1):
                            with self.subTest(chart=chart, method=method, component=component,
                                              host=host, replicas=replicas):
                                result = self.render(chart, component, method=method,
                                                     host=host, replicas=replicas)
                                if result.returncode == 0:
                                    docs = self.documents(result)
                                    services = {doc['metadata']['name'] for doc in docs
                                                if doc['kind'] == 'Service'}
                                    dangling = [doc['metadata']['name'] for doc in docs
                                                if doc['kind'] == 'Ingress'
                                                for rule in doc['spec']['rules']
                                                for path in rule['http']['paths']
                                                if path['backend']['service']['name'] not in services]
                                    self.fail('chunk active Ingress must fail; dangling Ingresses: '
                                              + repr(dangling))
                                self.assertIn(f'fullMode.components.{component}.ingress.enabled', result.stderr)
                                self.assertIn('mode=full', result.stderr)
                                self.assertIn('disable', result.stderr)

    def test_chunk_defaults_disabled_components_and_disabled_ingresses_are_valid(self):
        for chart in CHARTS:
            for method in ('firehose', 'poller'):
                self.documents(self.render(chart, method=method))
                for component in COMPONENTS:
                    for enabled, ingress in ((False, True), (True, False)):
                        for mode in ('full', 'chunk'):
                            with self.subTest(chart=chart, method=method, component=component,
                                              enabled=enabled, ingress=ingress, mode=mode):
                                docs = self.documents(self.render(chart, component, method=method,
                                                                  enabled=enabled, ingress=ingress, mode=mode))
                                self.assertFalse(any(doc['kind'] == 'Ingress' for doc in docs))

    def test_full_ingresses_resolve_to_service_ports_and_keep_existing_gates(self):
        for chart in CHARTS:
            for component in COMPONENTS:
                for replicas in (0, 1):
                    for host in ('ingress.example.com', ''):
                        with self.subTest(chart=chart, component=component, replicas=replicas, host=host):
                            docs = self.documents(self.render(chart, component, mode='full',
                                                              replicas=replicas, host=host))
                            ingresses = [doc for doc in docs if doc['kind'] == 'Ingress']
                            self.assertEqual(len(ingresses), 0 if component == 'grpc' and not host else 1)
                            for ingress in ingresses:
                                suffix = 'firehose-grpc-ingress' if component == 'grpc' else 'substreams-tier-1-ingress'
                                self.assertEqual(ingress['metadata']['name'], f'ingress-check-{suffix}')
                                for rule in ingress['spec']['rules']:
                                    for path in rule['http']['paths']:
                                        backend = path['backend']['service']
                                        service = next(doc for doc in docs if doc['kind'] == 'Service'
                                                       and doc['metadata']['name'] == backend['name'])
                                        self.assertIn(backend['port']['name'],
                                                      [port['name'] for port in service['spec']['ports']])


if __name__ == '__main__':
    unittest.main()

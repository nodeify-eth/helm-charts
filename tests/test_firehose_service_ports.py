from pathlib import Path
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PORTS = {'reader': 10010, 'merger': 10012, 'relayer': 10014, 'grpc': 10015}


class FirehoseServicePortsTest(unittest.TestCase):
    def test_full_mode_metrics_resolve_in_selected_workloads(self):
        for chart in ('firehose-core', 'firehose-ethereum'):
            result = subprocess.run(
                ['helm', 'template', 'ports-check', str(ROOT / 'charts' / chart),
                 '--set-string', 'fullMode.jwt.existingSecret=external-jwt',
                 *[arg for component in COMPONENT_PORTS
                   for arg in ('--set', f'fullMode.components.{component}.enabled=true')]],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, 'render failed; output suppressed')
            docs = [doc for doc in yaml.safe_load_all(result.stdout) if doc]
            workloads = [doc for doc in docs if doc['kind'] in ('Deployment', 'StatefulSet')]
            for component, grpc_port in COMPONENT_PORTS.items():
                with self.subTest(chart=chart, component=component):
                    service = next(doc for doc in docs if doc['kind'] == 'Service'
                                   and doc['metadata']['name'] == f'ports-check-firehose-{component}-svc')
                    selector = service['spec']['selector']
                    self.assertTrue(selector)
                    selected = [doc for doc in workloads if all(
                        doc['spec']['template']['metadata']['labels'].get(key) == value
                        for key, value in selector.items())]
                    self.assertEqual([doc['metadata']['name'] for doc in selected],
                                     [f'ports-check-firehose-{component}'])
                    metrics = next(port for port in service['spec']['ports'] if port['name'] == 'metrics')
                    self.assertEqual(metrics['port'], 9102)
                    grpc = next(port for port in service['spec']['ports'] if port['name'] == 'grpc')
                    self.assertEqual((grpc['port'], grpc['targetPort']), (grpc_port, 'grpc'))
                    target = metrics['targetPort']
                    self.assertIsInstance(target, str)
                    ports = [port for container in selected[0]['spec']['template']['spec']['containers']
                             for port in container.get('ports', []) if port.get('name') == target]
                    self.assertEqual([(port['containerPort'], port.get('protocol', 'TCP')) for port in ports],
                                     [(9102, metrics.get('protocol', 'TCP'))],
                                     f'{chart}/{component}: metrics target {target!r} must resolve')
                    if chart == 'firehose-ethereum' and component == 'grpc':
                        self.assertEqual(target, 'metrics')


if __name__ == '__main__':
    unittest.main()

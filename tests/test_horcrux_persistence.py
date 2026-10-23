from pathlib import Path
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class HorcruxPersistenceTest(unittest.TestCase):
    def render(self, *settings):
        return subprocess.run(
            ['helm', 'template', 'persistence-check', str(ROOT / 'charts/horcrux'), *settings],
            capture_output=True, text=True,
        )

    def test_disabled_persistence_requires_durable_signing_state(self):
        for mode in ('threshold', 'single'):
            with self.subTest(mode=mode):
                result = self.render('--set', 'persistence.enabled=false', '--set', f'horcrux.signMode={mode}')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('persistence.enabled=true', result.stderr)
                self.assertIn('signing state', result.stderr)

    def test_signing_modes_keep_state_claim_and_valid_mounts(self):
        for mode in ('threshold', 'single'):
            with self.subTest(mode=mode):
                result = self.render('--set', f'horcrux.signMode={mode}')
                self.assertEqual(result.returncode, 0, result.stderr)
                documents = list(yaml.safe_load_all(result.stdout))
                statefulset = next(doc for doc in documents if doc and doc['kind'] == 'StatefulSet')
                self.assertEqual(statefulset['metadata']['name'], 'persistence-check-horcrux')
                spec = statefulset['spec']
                self.assertEqual(spec['serviceName'], 'persistence-check-horcrux-headless')
                self.assertEqual(spec['replicas'], 3)
                self.assertEqual(spec['selector']['matchLabels'], {
                    'app.kubernetes.io/name': 'horcrux',
                    'app.kubernetes.io/instance': 'persistence-check',
                })
                claims = spec['volumeClaimTemplates']
                self.assertEqual([claim['metadata']['name'] for claim in claims], ['state'])
                self.assertEqual(claims[0]['spec']['resources']['requests']['storage'], '1Gi')
                self.assertEqual(claims[0]['spec']['accessModes'], ['ReadWriteOnce'])
                pod = spec['template']['spec']
                volumes = {volume['name'] for volume in pod['volumes']} | {'state'}
                for container in pod['initContainers'] + pod['containers']:
                    for mount in container.get('volumeMounts', []):
                        self.assertIn(mount['name'], volumes)
                    self.assertIn({'name': 'state', 'mountPath': '/horcrux/state'}, container['volumeMounts'])


if __name__ == '__main__':
    unittest.main()

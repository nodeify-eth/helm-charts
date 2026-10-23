from pathlib import Path
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures'
RELEASE = 'fixture'
NAMESPACE = 'fixture-render'
CHARTS = ('cosmos-node', 'firehose-core', 'firehose-ethereum', 'horcrux',
          'substreams-sink-noop', 'substreams-tier-2')
WORKLOAD_KINDS = ('Deployment', 'StatefulSet', 'DaemonSet', 'Job')
CLUSTER_KINDS = ('ClusterSecretStore', 'ClusterRole', 'ClusterRoleBinding')


class ChartRenderingTest(unittest.TestCase):
    def documents(self, result):
        self.assertEqual(result.returncode, 0, 'render failed; credential output suppressed')
        try:
            documents = [document for document in yaml.safe_load_all(result.stdout) if document]
        except yaml.YAMLError:
            self.fail('rendered YAML could not be parsed; credential output suppressed')
        self.assertTrue(all(isinstance(document, dict) for document in documents),
                        'rendered documents must be mappings')
        return documents

    def namespace(self, document):
        if document['kind'] in CLUSTER_KINDS:
            return None
        return document.get('metadata', {}).get('namespace', NAMESPACE)

    def identity(self, document):
        return document['kind'], self.namespace(document), document['metadata']['name']

    def selected(self, resources, selector, namespace, template=False):
        self.assertTrue(selector, 'a chart-owned selector must not be empty')
        return [resource for resource in resources
                if self.namespace(resource) == namespace
                and all((resource['spec']['template'] if template else resource)
                        .get('metadata', {}).get('labels', {}).get(key) == value
                        for key, value in selector.items())]

    def references(self, documents, case):
        resources = {self.identity(document): document for document in documents}
        external = {}
        for reference in case.get('external_resources', []):
            namespace = reference.get('namespace', case.get('namespace', NAMESPACE))
            if reference['kind'] in CLUSTER_KINDS:
                namespace = None
            identity = reference['kind'], namespace, reference['name']
            self.assertNotIn(identity, external, 'duplicate external declaration')
            self.assertNotIn(identity, resources, 'external declaration shadows a rendered resource')
            external[identity] = set(reference.get('keys', []))
        generated = {}
        for document in documents:
            if document['kind'] == 'ExternalSecret':
                identity = 'Secret', self.namespace(document), document['spec']['target']['name']
                self.assertNotIn(identity, external, 'generated Secret must not be exempted as external')
                generated[identity] = {entry['secretKey'] for entry in document['spec']['data']}
        used_external = set()

        def resolve(kind, name, namespace, keys=()):
            identity = kind, None if kind in CLUSTER_KINDS else namespace, name
            if identity in resources:
                resource = resources[identity]
                available = set(resource.get('data', {})) | set(resource.get('binaryData', {}))
                available |= set(resource.get('stringData', {}))
            elif identity in generated:
                available = generated[identity]
            else:
                self.assertIn(identity, external, f'undeclared external reference: {identity}')
                used_external.add(identity)
                available = external[identity]
            self.assertTrue(set(keys) <= available,
                            f'referenced keys missing from {kind}/{name}; values suppressed')

        def configuration(reference, namespace, kind, name_key='name'):
            resolve(kind, reference[name_key], namespace,
                    [item['key'] for item in reference.get('items', [])])

        workloads = [document for document in documents if document['kind'] in WORKLOAD_KINDS]
        for workload in workloads:
            namespace = self.namespace(workload)
            pod = workload['spec']['template']['spec']
            resolve('ServiceAccount', pod.get('serviceAccountName', 'default'), namespace)
            for reference in pod.get('imagePullSecrets', []):
                resolve('Secret', reference['name'], namespace)
            volumes = pod.get('volumes', [])
            defined = {volume['name'] for volume in volumes}
            defined |= {claim['metadata']['name']
                        for claim in workload['spec'].get('volumeClaimTemplates', [])}
            for volume in volumes:
                if 'configMap' in volume:
                    configuration(volume['configMap'], namespace, 'ConfigMap')
                if 'secret' in volume:
                    configuration(volume['secret'], namespace, 'Secret', 'secretName')
                for source in volume.get('projected', {}).get('sources', []):
                    for field, kind in (('secret', 'Secret'), ('configMap', 'ConfigMap')):
                        if field in source:
                            configuration(source[field], namespace, kind)
            for container in pod.get('initContainers', []) + pod['containers']:
                for mount in container.get('volumeMounts', []):
                    self.assertIn(mount['name'], defined,
                                  f'undefined mount in {workload["metadata"]["name"]}')
                for entry in container.get('env', []):
                    for field, kind in (('secretKeyRef', 'Secret'), ('configMapKeyRef', 'ConfigMap')):
                        reference = entry.get('valueFrom', {}).get(field)
                        if reference:
                            resolve(kind, reference['name'], namespace, [reference['key']])
                for entry in container.get('envFrom', []):
                    for field, kind in (('secretRef', 'Secret'), ('configMapRef', 'ConfigMap')):
                        if field in entry:
                            resolve(kind, entry[field]['name'], namespace)
        for document in documents:
            namespace = self.namespace(document)
            if document['kind'] == 'Ingress':
                for tls in document['spec'].get('tls', []):
                    if tls.get('secretName'):
                        resolve('Secret', tls['secretName'], namespace, ['tls.crt', 'tls.key'])
            elif document['kind'] == 'ExternalSecret':
                reference = document['spec']['secretStoreRef']
                resolve(reference['kind'], reference['name'], namespace)
            elif document['kind'] == 'RoleBinding':
                reference = document['roleRef']
                resolve(reference['kind'], reference['name'], namespace)
                for subject in document['subjects']:
                    if subject['kind'] == 'ServiceAccount':
                        resolve('ServiceAccount', subject['name'],
                                subject.get('namespace', namespace))
        self.assertEqual(used_external, set(external), 'external catalog contains unused exemptions')

    def relationships(self, documents):
        resources = {self.identity(document): document for document in documents}
        workloads = [document for document in documents if document['kind'] in WORKLOAD_KINDS]
        services = [document for document in documents if document['kind'] == 'Service']
        for workload in workloads:
            selector = workload['spec'].get('selector', {}).get('matchLabels', {})
            labels = workload['spec']['template']['metadata']['labels']
            self.assertTrue(selector and all(labels.get(key) == value for key, value in selector.items()),
                            f'workload selector does not match its pods: {workload["metadata"]["name"]}')
        for service in services:
            namespace = self.namespace(service)
            selected = self.selected(workloads, service['spec']['selector'], namespace, template=True)
            self.assertTrue(selected, f'Service selects no rendered workload: {service["metadata"]["name"]}')
            for port in service['spec']['ports']:
                target = port.get('targetPort', port['port'])
                if isinstance(target, str):
                    for workload in selected:
                        names = {entry['name']
                                 for container in workload['spec']['template']['spec']['containers']
                                 for entry in container.get('ports', []) if 'name' in entry}
                        self.assertIn(target, names,
                                      f'named target unresolved: {service["metadata"]["name"]}/{target}')
        for document in documents:
            namespace = self.namespace(document)
            kind = document['kind']
            if kind == 'HorizontalPodAutoscaler':
                reference = document['spec']['scaleTargetRef']
                self.assertIn(reference['kind'], WORKLOAD_KINDS, 'HPA target must be a workload')
                self.assertIn((reference['kind'], namespace, reference['name']), resources,
                              'HPA target is not a rendered workload')
            elif kind == 'Ingress':
                for rule in document['spec'].get('rules', []):
                    for path in rule.get('http', {}).get('paths', []):
                        reference = path['backend']['service']
                        identity = 'Service', namespace, reference['name']
                        self.assertIn(identity, resources, 'Ingress backend Service is absent')
                        ports = resources[identity]['spec']['ports']
                        key = 'name' if 'name' in reference['port'] else 'port'
                        value = reference['port'].get('name', reference['port'].get('number'))
                        self.assertTrue(any(port.get(key) == value for port in ports),
                                        'Ingress backend port is absent')
            elif kind in ('ServiceMonitor', 'VMServiceScrape'):
                selected = self.selected(services, document['spec']['selector']['matchLabels'], namespace)
                for endpoint in document['spec']['endpoints']:
                    self.assertTrue(any(endpoint['port'] in {port.get('name') for port in service['spec']['ports']}
                                        for service in selected), 'monitor endpoint has no matching Service port')
            elif kind in ('PodDisruptionBudget', 'NetworkPolicy'):
                field = 'podSelector' if kind == 'NetworkPolicy' else 'selector'
                self.assertTrue(self.selected(workloads, document['spec'][field]['matchLabels'],
                                              namespace, template=True),
                                f'{kind} selector has no matching workload')

    def embedded_configuration(self, documents, case):
        chunks = []
        for document in documents:
            if document['kind'] != 'ConfigMap':
                continue
            for name, value in document.get('data', {}).items():
                if not name.endswith('.yaml'):
                    continue
                try:
                    configuration = yaml.safe_load(value)
                except yaml.YAMLError:
                    self.fail('embedded YAML could not be parsed; credential output suppressed')
                self.assertIsInstance(configuration, dict, 'embedded YAML must be a mapping')
                if name.startswith('chunk-'):
                    flags = configuration['start']['flags']
                    chunks.append((int(name.removeprefix('chunk-').removesuffix('.yaml')),
                                   [flags['reader-node-start-block-num'], flags['reader-node-stop-block-num']]))
        if 'chunk_ranges' in case:
            self.assertEqual([bounds for _, bounds in sorted(chunks)], case['chunk_ranges'])

    def test_matrix_covers_all_charts(self):
        matrices = sorted(FIXTURES.glob('*/matrix.yaml'))
        self.assertEqual({yaml.safe_load(path.read_text())['chart'] for path in matrices}, set(CHARTS))
        self.assertEqual(len(matrices), len(CHARTS), 'the matrix must cover each chart once')

    def check_chart(self, chart):
        matrix_path = FIXTURES / chart / 'matrix.yaml'
        matrix = yaml.safe_load(matrix_path.read_text())
        self.assertEqual(matrix['chart'], chart)
        self.assertTrue(matrix['cases'], 'each chart needs render cases')
        names = [case['name'] for case in matrix['cases']]
        self.assertEqual(len(names), len(set(names)), 'duplicate case names')
        for case in matrix['cases']:
            with self.subTest(chart=chart, case=case['name']):
                values = matrix_path.parent / case['values']
                result = subprocess.run(
                    ['helm', 'template', RELEASE, str(ROOT / 'charts' / chart),
                     '--namespace', NAMESPACE, '-f', str(values)], capture_output=True, text=True,
                )
                if 'error_contains' in case:
                    self.assertNotEqual(result.returncode, 0, 'invalid input unexpectedly rendered')
                    self.assertTrue(case['error_contains'] in result.stderr,
                                    'expected guard missing; credential output suppressed')
                    continue
                documents = self.documents(result)
                if case.get('allow_empty', False):
                    self.assertEqual(case['name'], 'full-disabled-components')
                    self.assertEqual(len(documents), 0, 'explicit all-disabled fixture must be empty')
                    self.assertEqual(case['resources'], [])
                    continue
                self.assertTrue(documents, 'positive fixture unexpectedly rendered no resources')
                identities = [self.identity(document) for document in documents]
                self.assertEqual(len(identities), len(set(identities)), 'duplicate resource identities')
                actual = {f'{kind}/{name}' for kind, _, name in identities}
                self.assertEqual(actual, set(case['resources']), 'intended resource set changed')
                self.assertTrue(all(namespace == case.get('namespace', NAMESPACE)
                                    for _, namespace, _ in identities), 'resource namespace changed')
                self.references(documents, case)
                self.relationships(documents)
                self.embedded_configuration(documents, case)

    def test_cosmos_node(self):
        self.check_chart('cosmos-node')

    def test_firehose_core(self):
        self.check_chart('firehose-core')

    def test_firehose_ethereum(self):
        self.check_chart('firehose-ethereum')

    def test_horcrux(self):
        self.check_chart('horcrux')

    def test_substreams_sink_noop(self):
        self.check_chart('substreams-sink-noop')

    def test_substreams_tier_2(self):
        self.check_chart('substreams-tier-2')


if __name__ == '__main__':
    unittest.main()

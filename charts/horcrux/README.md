# horcrux

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v3.3.2](https://img.shields.io/badge/AppVersion-v3.3.2-informational?style=flat-square)

A production-grade Helm chart for deploying Horcrux remote signer for Cosmos chains

**Homepage:** <https://github.com/strangelove-ventures/horcrux>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| Horcrux Team |  | <https://github.com/strangelove-ventures/horcrux> |

## Source Code

* <https://github.com/strangelove-ventures/horcrux>

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | Affinity rules for pod assignment |
| args | list | `[]` | Args override |
| chain | object | `{"environment":"mainnet","id":"cosmoshub"}` | Chain configuration |
| chain.environment | string | `"mainnet"` | Chain environment (e.g., mainnet, testnet) |
| chain.id | string | `"cosmoshub"` | Chain identifier (e.g., cosmoshub, osmosis, juno) |
| command | list | `[]` | Command override |
| extraContainers | list | `[]` | Extra containers (sidecars) |
| extraEnv | list | `[]` | Extra environment variables |
| extraEnvFrom | list | `[]` | Extra environment variables from ConfigMaps or Secrets |
| extraInitContainers | list | `[]` | Extra init containers |
| extraVolumeMounts | list | `[]` | Extra volume mounts |
| extraVolumes | list | `[]` | Extra volumes |
| fullnameOverride | string | `""` | Override the full name of the release |
| global | object | `{"namespace":""}` | Global settings |
| global.namespace | string | `""` | Namespace to deploy into (if not specified, uses release namespace) |
| horcrux | object | `{"chainNodes":[{"privValAddr":"tcp://node-0.node-service.default.svc.cluster.local:1234"}],"debugAddr":"0.0.0.0:2345","extraConfig":{},"grpcAddr":"","signMode":"threshold","thresholdMode":{"grpcTimeout":"1000ms","raftTimeout":"1000ms","threshold":2}}` | Horcrux signing configuration |
| horcrux.chainNodes | list | `[{"privValAddr":"tcp://node-0.node-service.default.svc.cluster.local:1234"}]` | Chain nodes configuration |
| horcrux.debugAddr | string | `"0.0.0.0:2345"` | Debug server address (used for health checks and metrics) |
| horcrux.extraConfig | object | `{}` | Additional configuration options (merged into config.yaml) |
| horcrux.grpcAddr | string | `""` | GRPC server address (empty string disables) |
| horcrux.signMode | string | `"threshold"` | Sign mode: "threshold" or "single" |
| horcrux.thresholdMode | object | `{"grpcTimeout":"1000ms","raftTimeout":"1000ms","threshold":2}` | Threshold mode configuration (only used when signMode is "threshold") |
| horcrux.thresholdMode.grpcTimeout | string | `"1000ms"` | GRPC timeout for cosigner communication |
| horcrux.thresholdMode.raftTimeout | string | `"1000ms"` | Raft consensus timeout |
| horcrux.thresholdMode.threshold | int | `2` | Minimum number of signers required for threshold signing (must be <= replicaCount) |
| image | object | `{"pullPolicy":"IfNotPresent","repository":"ghcr.io/strangelove-ventures/horcrux","tag":""}` | Horcrux image configuration |
| image.tag | string | `""` | Overrides the image tag whose default is the chart appVersion |
| imagePullSecrets | list | `[]` | Image pull secrets for private registries |
| initContainer | object | `{"image":{"pullPolicy":"IfNotPresent","repository":"busybox","tag":"1.36"}}` | Init container configuration |
| lifecycle | object | `{}` | Lifecycle hooks |
| livenessProbe | object | `{"enabled":true,"failureThreshold":3,"httpGet":{"path":"/health","port":"debug"},"initialDelaySeconds":30,"periodSeconds":10,"successThreshold":1,"timeoutSeconds":5}` | Liveness probe configuration |
| monitoring | object | `{"serviceMonitor":{"enabled":false,"interval":"30s","labels":{},"metricRelabelings":[],"relabelings":[],"scrapeTimeout":"10s"},"vmServiceScrape":{"enabled":false,"interval":"30s","labels":{},"scrapeTimeout":"10s"}}` | Monitoring configuration |
| monitoring.serviceMonitor | object | `{"enabled":false,"interval":"30s","labels":{},"metricRelabelings":[],"relabelings":[],"scrapeTimeout":"10s"}` | Enable ServiceMonitor for Prometheus Operator |
| monitoring.serviceMonitor.interval | string | `"30s"` | Scrape interval |
| monitoring.serviceMonitor.labels | object | `{}` | Additional labels for ServiceMonitor |
| monitoring.serviceMonitor.metricRelabelings | list | `[]` | Metric relabel configs |
| monitoring.serviceMonitor.relabelings | list | `[]` | Relabel configs |
| monitoring.serviceMonitor.scrapeTimeout | string | `"10s"` | Scrape timeout |
| monitoring.vmServiceScrape | object | `{"enabled":false,"interval":"30s","labels":{},"scrapeTimeout":"10s"}` | Enable VMServiceScrape for VictoriaMetrics Operator |
| monitoring.vmServiceScrape.interval | string | `"30s"` | Scrape interval |
| monitoring.vmServiceScrape.labels | object | `{}` | Additional labels for VMServiceScrape |
| monitoring.vmServiceScrape.scrapeTimeout | string | `"10s"` | Scrape timeout |
| nameOverride | string | `""` | Override the name of the chart |
| networkPolicy | object | `{"egress":[],"enabled":false,"ingress":[]}` | Network Policy configuration |
| networkPolicy.egress | list | `[]` | Egress rules |
| networkPolicy.enabled | bool | `false` | Enable network policies |
| networkPolicy.ingress | list | `[]` | Ingress rules |
| nodeSelector | object | `{}` | Node selector for pod assignment |
| persistence | object | `{"accessMode":"ReadWriteOnce","annotations":{},"enabled":true,"size":"1Gi","storageClassName":""}` | Persistent volume configuration for state storage |
| persistence.accessMode | string | `"ReadWriteOnce"` | Access mode |
| persistence.annotations | object | `{}` | Annotations for PVCs |
| persistence.enabled | bool | `true` | Enable persistent storage for validator state |
| persistence.size | string | `"1Gi"` | Storage size |
| persistence.storageClassName | string | `""` | Storage class name (use "-" for default, "" for no storage class) |
| podAnnotations | object | `{}` | Pod annotations |
| podDisruptionBudget | object | `{"enabled":true,"minAvailable":2}` | Pod Disruption Budget |
| podDisruptionBudget.enabled | bool | `true` | Enable PodDisruptionBudget |
| podDisruptionBudget.minAvailable | int | `2` | Minimum available pods (use either minAvailable or maxUnavailable) |
| podLabels | object | `{}` | Pod labels |
| podManagementPolicy | string | `"Parallel"` | Pod management policy: "OrderedReady" or "Parallel" |
| podSecurityContext | object | `{"fsGroup":1000,"runAsNonRoot":true,"runAsUser":1000}` | Security context for pods |
| priorityClassName | string | `""` | Priority class name for pod scheduling |
| rbac | object | `{"create":true}` | RBAC configuration |
| rbac.create | bool | `true` | Create RBAC resources |
| readinessProbe | object | `{"enabled":true,"failureThreshold":3,"httpGet":{"path":"/health","port":"debug"},"initialDelaySeconds":10,"periodSeconds":5,"successThreshold":1,"timeoutSeconds":3}` | Readiness probe configuration |
| replicaCount | int | `3` | Number of Horcrux co-signer replicas (minimum 2, recommended 3 or more) |
| resources | object | `{"limits":{"cpu":"2","memory":"2Gi"},"requests":{"cpu":"500m","memory":"512Mi"}}` | Resource limits and requests |
| securityContext | object | `{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]},"readOnlyRootFilesystem":false,"runAsNonRoot":true,"runAsUser":1000}` | Security context for containers |
| service | object | `{"headless":{"annotations":{},"enabled":true,"p2pPort":2222,"type":"ClusterIP"},"metrics":{"annotations":{},"enabled":true,"port":2345,"type":"ClusterIP"}}` | Service configuration |
| service.headless | object | `{"annotations":{},"enabled":true,"p2pPort":2222,"type":"ClusterIP"}` | Headless service for StatefulSet pod discovery |
| service.headless.p2pPort | int | `2222` | P2P port for cosigner communication |
| service.metrics | object | `{"annotations":{},"enabled":true,"port":2345,"type":"ClusterIP"}` | Metrics service configuration |
| serviceAccount | object | `{"annotations":{},"create":true,"name":""}` | ServiceAccount configuration |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| shards | object | `{"externalSecrets":{"enabled":false,"refreshInterval":"1h","secretStoreRef":{"kind":"ClusterSecretStore","name":""},"shardConfigs":[]},"method":"secret","secrets":{"create":false,"existingSecrets":["horcrux-shard-1","horcrux-shard-2","horcrux-shard-3"]}}` | Shard secrets configuration |
| shards.externalSecrets | object | `{"enabled":false,"refreshInterval":"1h","secretStoreRef":{"kind":"ClusterSecretStore","name":""},"shardConfigs":[]}` | External Secrets Operator configuration (used when method is "externalSecret") |
| shards.externalSecrets.enabled | bool | `false` | Enable External Secrets |
| shards.externalSecrets.refreshInterval | string | `"1h"` | Refresh interval for secrets |
| shards.externalSecrets.secretStoreRef | object | `{"kind":"ClusterSecretStore","name":""}` | Secret store reference |
| shards.externalSecrets.shardConfigs | list | `[]` | Remote references for each shard |
| shards.method | string | `"secret"` | Method to provide shard secrets: "secret" or "externalSecret" |
| shards.secrets | object | `{"create":false,"existingSecrets":["horcrux-shard-1","horcrux-shard-2","horcrux-shard-3"]}` | Direct Kubernetes secrets (used when method is "secret") Each shard must contain: provider_shard.json, ecies_keys.json, provider_priv_validator_state.json |
| shards.secrets.create | bool | `false` | Create secrets from values (NOT RECOMMENDED for production - use external secrets) |
| shards.secrets.existingSecrets | list | `["horcrux-shard-1","horcrux-shard-2","horcrux-shard-3"]` | Existing secret names (one per replica) IMPORTANT: You must create these secrets before installing the chart |
| startupProbe | object | `{"enabled":false,"failureThreshold":30,"httpGet":{"path":"/health","port":"debug"},"initialDelaySeconds":0,"periodSeconds":10,"successThreshold":1,"timeoutSeconds":3}` | Startup probe configuration (useful for slow-starting pods) |
| terminationGracePeriodSeconds | int | `30` | Termination grace period in seconds |
| tolerations | list | `[]` | Tolerations for pod assignment |
| updateStrategy | object | `{"rollingUpdate":{},"type":"RollingUpdate"}` | Update strategy for StatefulSet |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)

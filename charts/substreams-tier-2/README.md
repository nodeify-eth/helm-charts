# substreams-tier-2

![Version: 1.1.7](https://img.shields.io/badge/Version-1.1.7-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v2.24.1](https://img.shields.io/badge/AppVersion-v2.24.1-informational?style=flat-square)

A Helm chart for deploying substreams-tier-2

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| fullnameOverride | string | `""` |  |
| image.pullPolicy | string | `"IfNotPresent"` | Image pull policy (e.g., Always, IfNotPresent, Never) |
| image.repository | string | `"ghcr.io/streamingfast/firehose-ethereum"` | Repository for the substreams image |
| image.tag | string | `""` | Overrides the image tag (default: Chart.appVersion) |
| nameOverride | string | `""` |  |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.create | bool | `false` | Specifies whether a service account should be created |
| serviceAccount.name | string | `""` | The name of the service account to use.    If not set and `create` is true, a name is generated using the fullname template. |
| substreams_tier_2.autoscaling | object | `{"behavior":{"scaleDown":{"policies":[{"periodSeconds":60,"type":"Pods","value":1}],"stabilizationWindowSeconds":300},"scaleUp":{"policies":[{"periodSeconds":15,"type":"Pods","value":1}],"stabilizationWindowSeconds":5}},"enabled":false,"maxReplicas":10,"minReplicas":1,"targetCPUUtilizationPercentage":80,"targetMemoryUtilizationPercentage":80}` | Horizontal Pod Autoscaler configuration |
| substreams_tier_2.autoscaling.behavior | object | `{"scaleDown":{"policies":[{"periodSeconds":60,"type":"Pods","value":1}],"stabilizationWindowSeconds":300},"scaleUp":{"policies":[{"periodSeconds":15,"type":"Pods","value":1}],"stabilizationWindowSeconds":5}}` | Optional behavior configuration for fine-tuning scaling operations |
| substreams_tier_2.autoscaling.behavior.scaleDown | object | `{"policies":[{"periodSeconds":60,"type":"Pods","value":1}],"stabilizationWindowSeconds":300}` | Configuration for scaling down pods |
| substreams_tier_2.autoscaling.behavior.scaleDown.policies | list | `[{"periodSeconds":60,"type":"Pods","value":1}]` | Policies that control how many pods to remove during scaling operations |
| substreams_tier_2.autoscaling.behavior.scaleDown.policies[0] | object | `{"periodSeconds":60,"type":"Pods","value":1}` | Policy to remove exactly one pod at a time |
| substreams_tier_2.autoscaling.behavior.scaleDown.policies[0].periodSeconds | int | `60` | How frequently (in seconds) this policy can be applied |
| substreams_tier_2.autoscaling.behavior.scaleDown.policies[0].value | int | `1` | Number of pods to remove in a single scaling operation |
| substreams_tier_2.autoscaling.behavior.scaleDown.stabilizationWindowSeconds | int | `300` | Number of seconds to wait with under-utilization before scaling down |
| substreams_tier_2.autoscaling.behavior.scaleUp | object | `{"policies":[{"periodSeconds":15,"type":"Pods","value":1}],"stabilizationWindowSeconds":5}` | Configuration for scaling up pods |
| substreams_tier_2.autoscaling.behavior.scaleUp.policies | list | `[{"periodSeconds":15,"type":"Pods","value":1}]` | Policies that control how many pods to add during scaling operations |
| substreams_tier_2.autoscaling.behavior.scaleUp.policies[0] | object | `{"periodSeconds":15,"type":"Pods","value":1}` | Policy to add exactly one pod at a time |
| substreams_tier_2.autoscaling.behavior.scaleUp.policies[0].periodSeconds | int | `15` | How frequently (in seconds) this policy can be applied |
| substreams_tier_2.autoscaling.behavior.scaleUp.policies[0].value | int | `1` | Number of pods to add in a single scaling operation |
| substreams_tier_2.autoscaling.behavior.scaleUp.stabilizationWindowSeconds | int | `5` | Number of seconds to wait before scaling up after a previous scale up |
| substreams_tier_2.autoscaling.enabled | bool | `false` | Enable autoscaling for the deployment |
| substreams_tier_2.autoscaling.maxReplicas | int | `10` | Maximum number of replicas |
| substreams_tier_2.autoscaling.minReplicas | int | `1` | Minimum number of replicas |
| substreams_tier_2.autoscaling.targetCPUUtilizationPercentage | int | `80` | Target CPU utilization percentage |
| substreams_tier_2.autoscaling.targetMemoryUtilizationPercentage | int | `80` | Target memory utilization percentage |
| substreams_tier_2.config | string | `"# -- Sets the verbosity level of the logging. 0 means least verbose.\nlog-verbosity: 0\n\n# -- Determines if logs should be written to a file. If false, logs will be written to stdout.\nlog-to-file: false\n\n# -- Percentage of memory limit that should trigger auto memory management.\ncommon-auto-mem-limit-percent: 90\n\n# -- Address for the Substreams Tier 2 gRPC listener.\nsubstreams-tier2-grpc-listen-addr: :9000\n\n# -- Endpoint for Substreams Tier 2 subrequests.\nsubstreams-tier2-max-concurrent-requests: 50\n"` |  |
| substreams_tier_2.env | object | `{"enabled":false,"variables":{}}` | Define custom aliases for preconfigured commands in your environment. This allows you to create shorthand commands for frequently used operations, |
| substreams_tier_2.env.enabled | bool | `false` | Enable environment variable injection into the container |
| substreams_tier_2.extraArgs | object | `{}` | Specify additional command-line arguments to pass to the `tier-2` component. These arguments can be used to override default settings or provide additional configurations that are not covered by the standard configuration options.   |
| substreams_tier_2.ingress.annotations | object | `{}` |  |
| substreams_tier_2.ingress.enabled | bool | `false` | Enable or disable ingress |
| substreams_tier_2.ingress.host | string | `"example.domain.com"` | Hostname for the ingress |
| substreams_tier_2.ingress.ingressClassName | string | `"nginx"` | Ingress class configuration (K8s 1.19+) |
| substreams_tier_2.ingress.paths.default | string | `"/"` | Default path mapping for ingress |
| substreams_tier_2.ingress.tls.enabled | bool | `false` | Enable TLS (HTTPS) for ingress |
| substreams_tier_2.ingress.tls.secretName | string | `""` | Name of the TLS secret (leave empty for auto-generation) |
| substreams_tier_2.podSecurityContext | object | `{"runAsNonRoot":false}` | Pod-wide security context settings |
| substreams_tier_2.podSecurityContext.runAsNonRoot | bool | `false` | Run the pod as a non-root user (recommended for security) |
| substreams_tier_2.replicaCount | int | `1` | Number of pod replicas for substreams tier 2 |
| substreams_tier_2.resources | object | `{}` | Resource limits and requests for the container (required for HPA to function) |
| substreams_tier_2.service.ipFamilies | list | `["IPv4"]` | Set the IP families to use (e.g., ["IPv4", "IPv6"]) |
| substreams_tier_2.service.ipFamilyPolicy | object | `{}` | Specifies the IP family policy for the service. Valid options are "SingleStack", "PreferDualStack", and "RequireDualStack". |
| substreams_tier_2.service.ports.grpc | int | `9000` | Specifies the port for the Substreams GRPC interface. This port will be exposed by the service. |
| substreams_tier_2.service.ports.metrics | int | `9102` | Specifies the port for the metrics interface. This port will be exposed by the service. |
| substreams_tier_2.service.type | string | `"ClusterIP"` | Specifies the type of the Kubernetes service. Valid options are "ClusterIP", "NodePort", "LoadBalancer", and "ExternalName". |
| substreams_tier_2.serviceMonitor.annotations | object | `{}` | Additional annotations for the ServiceMonitor resource |
| substreams_tier_2.serviceMonitor.enabled | bool | `false` | Enable or disable the service monitor |
| substreams_tier_2.serviceMonitor.honorLabels | bool | `false` | Honor labels from scraped metrics |
| substreams_tier_2.serviceMonitor.interval | string | `"30s"` | Interval at which Prometheus scrapes metrics |
| substreams_tier_2.serviceMonitor.labels | object | `{}` | Additional labels for the ServiceMonitor resource |
| substreams_tier_2.serviceMonitor.path | string | `"/metrics"` | Configure metrics path |
| substreams_tier_2.serviceMonitor.relabelings | list | `[]` | Relabeling configurations for the ServiceMonitor |
| substreams_tier_2.serviceMonitor.scrapeTimeout | string | `"10s"` | Timeout for the scrape request |
| substreams_tier_2.terminationGracePeriodSeconds | int | `60` | Grace period for pod termination (in seconds) |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)

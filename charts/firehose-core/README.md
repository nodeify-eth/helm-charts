# firehose-core

![Version: 1.2.11](https://img.shields.io/badge/Version-1.2.11-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v1.10.2](https://img.shields.io/badge/AppVersion-v1.10.2-informational?style=flat-square)

Metrics Services retain their public `metrics` port (9102) and now target the existing named container port for each selected workload.

A Helm chart for Kubernetes

## JWT lifecycle and migration

Full mode uses one Engine API credential shared by reader and Lighthouse. The fixed Secret key is `jwt.hex`, mounted read-only at `/jwt/jwt.hex`; its decoded value must be exactly 64 ASCII hexadecimal characters. Chunk mode and full mode with all JWT consumers disabled do not resolve or create JWT credentials.

| Value | Default | Purpose |
| --- | --- | --- |
| `fullMode.jwt.existingSecret` | `""` | Namespace-local external Secret, provisioned before consumers start; use a name different from `<release>-firehose-jwt`. |
| `fullMode.jwt.revision` | `""` | Public, nonsecret token to trigger coordinated consumer restarts. Never put credential material here. |

With an empty `existingSecret`, a connected first install creates `<release>-firehose-jwt` from 32 cryptographically random bytes. Connected upgrades preserve valid existing bytes exactly. This includes legacy Ethereum credentials derived from public release metadata: upgrading this chart **does not remediate those weak credentials**. Review Engine API exposure and plan a separate coordinated rotation. Invalid data or a missing managed Secret during upgrade fails closed; securely restore the original Secret or provision a new external Secret and select it. This also applies when enabling a previously disabled reader on upgrade. Normal uninstall removes the managed Secret; reinstall creates a new identity.

When reader is disabled and any JWT client is enabled, `existingSecret` is required, even if the client's replicas are zero. Coordinate the credential with the external execution engine. External mode emits no managed JWT Secret and performs no lookup or live validation of its presence/content. The provisioning system must validate the fixed key/format and ensure the Secret exists before Pods start.

### Offline rendering and permissions

Use an external Secret for offline rendering and GitOps. Identical external name/revision values render deterministically. Managed install previews generate fresh random credentials and cannot establish the eventual installed identity. Client `helm template` and client dry-runs cannot read live Secrets; managed `--is-upgrade` rendering therefore fails when lookup finds no Secret. A renderer that always presents an install cannot detect an upgrade: GitOps must use `existingSecret` rather than relying on this guard.

Connected Helm lookup needs the rendering identity to GET the named Secret in the release namespace; the workload service account is not that identity. API/RBAC errors propagate as rendering failures. Server-side dry-run can exercise lookup only with appropriate cluster connectivity and permissions. Avoid logging rendered Secret manifests or credential bytes during validation.

The chart reserves pod annotation keys `checksum/jwt-secret` and `firehose.streamingfast.io/jwt-revision`; setting either through consumer `podAnnotations` fails. Managed checksums cover credential bytes only and are consistent across consumers. External mode uses the revision token instead of reading or hashing the external Secret. These annotations trigger restarts but do not guarantee their order or that an engine reloads a projected file.

### Migration and coordinated rotation

1. Before moving from managed to external ownership, securely provision a **new Secret name** with the current credential through your secret-management system. Do not print keys or Secret manifests. Setting `existingSecret` to the managed name is rejected: removing the managed resource from Helm's desired manifests can delete it. No automatic adoption or keep policy is provided.
2. Plan a maintenance window and rehearse how to stop engine clients and suspend any reconciliation that would restart them. Core's Lighthouse StatefulSet has no configurable replicas value; do not assume a values-only procedure can stop it. Coordinate external engine owners as applicable.
3. Select the new external Secret consistently for the reader and all clients. For rotation, provision fresh cryptographically random material in another new external Secret; stop clients, restart the reader with that credential, and wait for readiness before restarting clients with the same credential. A single Helm upgrade or revision change does not guarantee this sequence.
4. Verify real Engine API authentication and synchronization before resuming normal operation. In-place Secret changes also require a rehearsed restart sequence; projected-volume updates alone do not prove binary reload. Keep the prior credential securely for the agreed rollback window, and roll back credentials and consumers together. Helm rollback can restore historical manifests and credentials.

Connected install/upgrade preservation, denied lookup, actual external ownership transition, revision rollouts, rollback, real-engine authentication and restart ordering have **not been rehearsed by this change**. Offline rendering and synthetic lookup regression tests do not substitute for an approved disposable-environment rehearsal. This runbook describes required coordination, not a proven production deployment procedure.

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| chunkMode.chunkConfig.startBlock | int | `0` | Starting block number (inclusive) |
| chunkMode.chunkConfig.stopBlock | int | `100000` | Ending block number (exclusive) |
| chunkMode.chunkConfig.workers | int | `4` | Number of workers to split block range across |
| chunkMode.components.merger.config | object | `{"merger-delete-threads":100,"merger-time-between-store-lookups":"10s"}` | Merger node configuration |
| chunkMode.components.merger.enabled | bool | `true` | Enable the Firehose merger node |
| chunkMode.components.reader.config | object | `{"reader-node-blocks-chan-capacity":5000,"reader-node-firehose-plaintext":true,"reader-node-readiness-max-latency":"1200s"}` | Reader node configuration |
| chunkMode.components.reader.enabled | bool | `true` | Enable the Firehose reader node |
| chunkMode.components.remoteFirehose.endpoint | string | `"https://firehose.example.com/ethereum"` | Firehose endpoint to fetch processed block data |
| chunkMode.components.rpcPoller.endpoint | string | `"https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"` | RPC endpoint to poll for blocks |
| chunkMode.method | string | `"firehose"` | Mode to use in chunk processing Options:   - "firehose": Remote firehose for block data   - "poller": Remote rpc for block data |
| chunkMode.storage | object | `{"readerNode":{"size":"50Mi"},"storageClass":""}` | Storage configuration for chunk mode |
| commonConfig.common-auth-plugin | string | `""` |  |
| commonConfig.common-auto-mem-limit-percent | int | `90` |  |
| commonConfig.common-forked-blocks-store-url | string | `""` |  |
| commonConfig.common-index-block-sizes | int | `10000` |  |
| commonConfig.common-live-blocks-addr | string | `""` |  |
| commonConfig.common-merged-blocks-store-url | string | `""` |  |
| commonConfig.common-metering-plugin | string | `""` |  |
| commonConfig.common-one-block-store-url | string | `""` |  |
| commonConfig.common-system-shutdown-signal-delay | string | `"10s"` |  |
| fullMode.components.grpc.config.advertise-chain-name | string | `"mainnet"` | gRPC server arguments |
| fullMode.components.grpc.config.firehose-rate-limit-bucket-fill-rate | string | `"2s"` |  |
| fullMode.components.grpc.config.firehose-rate-limit-bucket-size | int | `10` |  |
| fullMode.components.grpc.enabled | bool | `true` | Enable the Firehose gRPC server |
| fullMode.components.grpc.ingress | object | `{"annotations":[],"enabled":false,"host":"firehose.example.com","ingressClassName":""}` | gRPC server configuration |
| fullMode.components.grpc.replicas | int | `1` | Number of replicas for the gRPC server |
| fullMode.components.indexer.config.log-to-file | bool | `false` | Indexer arguments |
| fullMode.components.indexer.enabled | bool | `true` | Enable the Firehose indexer node |
| fullMode.components.indexer.replicas | int | `1` | Number of replicas for the relayer node |
| fullMode.components.lighthouse.checkpointSyncUrl | string | `"https://sync-mainnet.beaconcha.in"` | Checkpoint sync URL for faster initial sync |
| fullMode.components.lighthouse.enabled | bool | `true` | Enable Lighthouse for beacon chain synchronization |
| fullMode.components.lighthouse.network | string | `"mainnet"` | Ethereum network (mainnet, goerli, sepolia, holesky) |
| fullMode.components.lighthouse.pruneBlobs | bool | `true` | Remove old blob data to save space (recommended for non-archive nodes) |
| fullMode.components.merger.config.merger-delete-threads | int | `100` |  |
| fullMode.components.merger.config.merger-time-between-store-lookups | string | `"10s"` | Merger node arguments |
| fullMode.components.merger.enabled | bool | `true` | Enable the Firehose merger node |
| fullMode.components.merger.replicas | int | `1` | Number of replicas for the merger node |
| fullMode.components.reader.config.reader-node-arguments | string | `"--networkid=1 --ipcpath={data-dir}/reader/ipc --port=30302 --http --http.api=eth,net,web3 --http.port=8545 --http.addr=0.0.0.0 --http.vhosts=* --authrpc.port=8551 --authrpc.addr=0.0.0.0 --authrpc.vhosts=* --authrpc.jwtsecret=/jwt/jwt.hex --cache=8192 --syncmode=full --vmtrace=firehose"` |  |
| fullMode.components.reader.config.reader-node-blocks-chan-capacity | int | `5000` |  |
| fullMode.components.reader.config.reader-node-firehose-plaintext | bool | `true` |  |
| fullMode.components.reader.config.reader-node-path | string | `"/app/geth"` | Execution binary path |
| fullMode.components.reader.config.reader-node-readiness-max-latency | string | `"1200s"` |  |
| fullMode.components.reader.enabled | bool | `true` | Enable the Firehose reader node |
| fullMode.components.reader.replicas | int | `1` | Number of replicas for the reader node |
| fullMode.components.relayer.config.relayer-max-source-latency | string | `"1h"` | Relayer node arguments |
| fullMode.components.relayer.enabled | bool | `true` | Enable the Firehose relayer node |
| fullMode.components.relayer.replicas | int | `1` | Number of replicas for the relayer node |
| fullMode.components.substreams.config.advertise-chain-name | string | `"mainnet"` | Substreams arguments |
| fullMode.components.substreams.config.substreams-block-execution-timeout | string | `"10m"` |  |
| fullMode.components.substreams.config.substreams-state-store-default-tag | string | `"s3"` |  |
| fullMode.components.substreams.config.substreams-state-store-url | string | `""` |  |
| fullMode.components.substreams.config.substreams-tier1-active-requests-hard-limit | int | `50` |  |
| fullMode.components.substreams.config.substreams-tier1-active-requests-soft-limit | int | `45` |  |
| fullMode.components.substreams.config.substreams-tier1-quicksave-store | string | `""` |  |
| fullMode.components.substreams.config.substreams-tier1-subrequests-endpoint | string | `""` |  |
| fullMode.components.substreams.enabled | bool | `false` | Enable Substreams Tier 1 |
| fullMode.components.substreams.ingress | object | `{"annotations":[],"enabled":false,"host":"substreams.example.com","ingressClassName":"nginx"}` | gRPC server configuration |
| fullMode.components.substreams.replicas | int | `1` | Number of replicas for the Substreams component |
| fullMode.storage | object | `{"lighthouse":{"size":"400Gi"},"readerNode":{"size":"4Ti"},"storageClass":""}` | Storage configuration for full mode |
| fullnameOverride | string | `""` |  |
| image.pullPolicy | string | `"IfNotPresent"` |  |
| image.repository | string | `"ghcr.io/streamingfast/firehose-core"` | Image for Firehose |
| image.tag | string | Chart.appVersion | Overrides the image tag |
| imagePullSecrets | list | `[]` | Pull secrets required to fetch the Image |
| mode | string | `"full"` | Firehose operating mode Options:   - "full": Complete Firehose stack with all components (reader, merger, relayer, etc.)   - "chunk": Lightweight mode for specific block ranges |
| nameOverride | string | `""` |  |
| s3CredentialsSecret | list | `[]` | Secret name containing S3/object storage credentials. Must contain keys: access-key, secret-key |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)

# Nodeify Helm Charts

This repository contains Helm charts for Nodeify's tools and services.

## Available Charts

| Chart | Purpose |
| --- | --- |
| [cosmos-node](charts/cosmos-node/README.md) | Run Cosmos SDK blockchain nodes with persistent storage, bootstrap, networking, and monitoring configuration. |
| [firehose-core](charts/firehose-core/README.md) | Deploy Firehose components for blockchain data ingestion, block storage, and streaming, including chunk processing. |
| [firehose-ethereum](charts/firehose-ethereum/README.md) | Deploy Ethereum Firehose infrastructure with an instrumented execution client and block streaming components. |
| [horcrux](charts/horcrux/README.md) | Deploy Horcrux remote signing infrastructure for Cosmos validators. |
| [substreams-sink-noop](charts/substreams-sink-noop/README.md) | Consume Substreams modules with the noop sink for processing and inspecting their output. |
| [substreams-tier-2](charts/substreams-tier-2/README.md) | Run Substreams tier 2 workers for parallel module execution. |

The catalog lists the charts currently present in this repository. Historical packages in the Helm repository may include charts no longer maintained here.

## Usage

```bash
helm repo add nodeify https://nodeify-eth.github.io/helm-charts
helm repo update
helm install cosmos-node nodeify/cosmos-node
```

The Cosmos example uses the chart's Cosmos Hub defaults; no credentials are required to render it. Before installing, review the [Cosmos prerequisites and configuration](charts/cosmos-node/README.md), including persistent storage, image and chain compatibility, bootstrap sources, and resource capacity. Rendering manifests does not verify that a node can sync on your cluster.

To preview the checked-out chart without adding the published repository:

```bash
helm template cosmos-node ./charts/cosmos-node
```

For other charts, follow their linked README and inspect their values before installation; required endpoints, storage, and credentials depend on the workload.

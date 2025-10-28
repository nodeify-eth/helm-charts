# Cosmos Node Helm Chart

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/cosmos-node)](https://artifacthub.io/packages/search?repo=cosmos-node)
[![Helm Chart Version](https://img.shields.io/badge/chart-2.0.0-blue)](https://github.com/cosmos/helm-charts)

A professional, production-ready Helm chart for deploying Cosmos SDK blockchain nodes with enterprise-grade features and security.

## ✨ Features

- **🌍 Universal Multi-Chain Support**: Deploy any Cosmos SDK blockchain (Cosmos Hub, Osmosis, Juno, etc.)
- **📊 StatefulSet Architecture**: Reliable data persistence with volume claim templates
- **🔒 Security Hardened**: Pod Security Standards, RBAC, Network Policies, and security contexts
- **📈 Production Ready**: Comprehensive health checks, monitoring, and observability
- **🚀 Bootstrap Automation**: Automatic genesis, snapshot, seeds, and addrbook configuration
- **🏗️ Enterprise Features**: HPA, PDB, topology spread constraints, and priority classes
- **🔧 Highly Configurable**: 200+ configuration options with validation and best practices

## 🏗️ Architecture

This chart deploys a StatefulSet with:
- **Init Container**: Handles bootstrap (genesis, seeds, snapshots)
- **Main Container**: Runs the Cosmos SDK daemon
- **Persistent Storage**: Volume claim templates for reliable data persistence
- **Services**: Regular and headless services for P2P and RPC access
- **Security**: Comprehensive RBAC, security contexts, and network policies

## 📋 Prerequisites

- Kubernetes 1.19+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- Minimum 4 CPU cores and 16GB RAM per node

## 🚀 Quick Start

### Basic Installation

```bash
# Add the repository
helm repo add cosmos-node https://charts.cosmos.network
helm repo update

# Install Cosmos Hub
helm install my-cosmos-node cosmos-node/cosmos-node

# Install with custom values
helm install my-cosmos-node cosmos-node/cosmos-node -f my-values.yaml
```

### Example Configurations

#### Cosmos Hub (Mainnet)
```yaml
chain:
  name: "cosmos"
  chainId: "cosmoshub-4"
  daemon: "gaiad"
  home: ".gaia"
  minGasPrices: "0.001uatom"
  denom: "uatom"

bootstrap:
  snapshot:
    enabled: true
    command: "curl -s https://polkachu.com/api/v2/chain_snapshots/cosmos/mainnet | jq -r .snapshot.url"

image:
  repository: "ghcr.io/cosmos/gaia"
  tag: "v25.1.0"

resources:
  requests:
    cpu: 2
    memory: 4Gi
  limits:
    memory: 48Gi

persistence:
  size: 500Gi

daemon:
  flags:
    - "--halt-height=0"
    - "--halt-time=0"
    - "--min-retain-blocks=0"
```

## ⚙️ Configuration

### Core Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `chain.name` | Chain identifier | `"cosmos"` |
| `chain.chainId` | Network chain ID | `"cosmoshub-4"` |
| `chain.daemon` | Daemon binary name | `"gaiad"` |
| `chain.home` | Home directory | `".gaia"` |
| `chain.minGasPrices` | Minimum gas prices | `"0.001uatom"` |

### Image Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `"ghcr.io/cosmos/gaia"` |
| `image.tag` | Container image tag | `""` (uses appVersion) |
| `image.pullPolicy` | Image pull policy | `"IfNotPresent"` |
| `global.imageRegistry` | Global image registry override | `""` |

### Bootstrap Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `bootstrap.genesis.url` | Genesis file URL | `"https://snapshots.polkachu.com/genesis/cosmos/genesis.json"` |
| `bootstrap.addrbook.url` | Address book URL | `"https://snapshots.polkachu.com/addrbook/cosmos/addrbook.json"` |
| `bootstrap.seeds.list` | Comma-separated seeds list | `"ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@seeds.polkachu.com:14956"` |
| `bootstrap.snapshot.enabled` | Enable snapshot download | `true` |
| `bootstrap.snapshot.url` | Direct snapshot URL | `""` |
| `bootstrap.snapshot.command` | Command to get snapshot URL | `"curl -s https://polkachu.com/api/v2/chain_snapshots/cosmos/mainnet | jq -r .snapshot.url"` |

### Storage Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | Storage size | `"250Gi"` |
| `persistence.storageClass` | Storage class | `""` |
| `persistence.accessMode` | Access mode | `"ReadWriteOnce"` |

### Security Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.runAsNonRoot` | Run as non-root user | `true` |
| `podSecurityContext.runAsUser` | User ID | `1000` |
| `securityContext.readOnlyRootFilesystem` | Read-only root filesystem | `false` |
| `rbac.create` | Create RBAC resources | `true` |
| `networkPolicy.enabled` | Enable network policy | `false` |

### Monitoring & Health Checks

| Parameter | Description | Default |
|-----------|-------------|---------|
| `daemon.monitoring.prometheus` | Enable Prometheus metrics | `true` |
| `healthChecks.startup.enabled` | Enable startup probe | `true` |
| `healthChecks.liveness.enabled` | Enable liveness probe | `true` |
| `healthChecks.readiness.enabled` | Enable readiness probe | `true` |

## 🔧 Advanced Configuration

### Seeds Configuration

```yaml
# Single seed
bootstrap:
  seeds:
    list: "ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@seeds.polkachu.com:14956"

# Multiple seeds (comma-separated)
bootstrap:
  seeds:
    list: "ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@seeds.polkachu.com:14956,20e1000e88125698264454a884812746c2eb4807@seeds.example.com:26656"
```

### Custom Chain Example

```yaml
chain:
  name: "mychain"
  chainId: "mychain-1"
  daemon: "mychaind"
  home: ".mychain"
  minGasPrices: "0.001umytoken"
  denom: "umytoken"
  ports:
    p2p: 26656
    rpc: 26657
    grpc: 9090
    api: 1317

image:
  repository: "myregistry/mychain"
  tag: "v1.0.0"

# Custom bootstrap URLs
bootstrap:
  genesis:
    url: "https://example.com/genesis.json"
    checksum: "sha256:abcd1234..."
  seeds:
    list: "seed1@1.2.3.4:26656,seed2@5.6.7.8:26656"
  snapshot:
    enabled: true
    url: "https://example.com/snapshot.tar.lz4"
    timeout: 120

# Production settings
resources:
  requests:
    cpu: 8
    memory: 32Gi
  limits:
    cpu: 16
    memory: 64Gi

persistence:
  size: 1Ti
  storageClass: "fast-ssd"

# High availability
podDisruptionBudget:
  enabled: true
  minAvailable: 1

# Security
networkPolicy:
  enabled: true

# Monitoring
daemon:
  monitoring:
    prometheus: true
    address: "0.0.0.0:26660"

service:
  type: LoadBalancer
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
```

### State Sync Configuration

```yaml
network:
  config:
    stateSync:
      enabled: true
      rpcServers:
        - "https://rpc1.cosmos.network:443"
        - "https://rpc2.cosmos.network:443"
      trustHeight: 12345678
      trustHash: "ABCD1234..."

bootstrap:
  snapshot:
    enabled: false  # Disable snapshot when using state sync
```

### Horizontal Pod Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

## 🛡️ Security Best Practices

This chart implements comprehensive security measures:

### Pod Security Standards
- Non-root user execution (UID 1000)
- Read-only root filesystem where possible
- Dropped capabilities (ALL)
- Seccomp profiles
- No privilege escalation

### RBAC Configuration
- Minimal required permissions
- Namespace-scoped roles
- Service account isolation

### Network Security
- Network policies for ingress/egress control
- Separate headless service for StatefulSet
- Port isolation and protocol restrictions

## 📦 Manual Snapshot Configuration

### Overview

The chart provides full manual control over snapshot downloads with two methods: direct URLs or custom commands. No auto-detection is performed.

#### Configuration Options

**1. Direct Snapshot URL**:
```yaml
bootstrap:
  snapshot:
    enabled: true
    url: "https://example.com/snapshot.tar.lz4"
    command: ""  # Leave empty when using direct URL
```

**2. Custom Command (e.g., your curl command)**:
```yaml
bootstrap:
  snapshot:
    enabled: true
    url: ""  # Leave empty when using command
    command: "curl -s https://polkachu.com/api/v2/chain_snapshots/cosmos/mainnet | jq -r .snapshot.url"
```

**3. Disable Snapshots**:
```yaml
bootstrap:
  snapshot:
    enabled: false
```

#### Usage Examples

**Using Direct LZ4 URL**:
```yaml
bootstrap:
  snapshot:
    enabled: true
    url: "https://snapshots.mycdn.com/cosmos-20240115.tar.lz4"
    timeout: 120  # 2 hours for large snapshots
```

**Using Your Curl Command**:
```yaml
bootstrap:
  snapshot:
    enabled: true
    command: "curl -s https://polkachu.com/api/v2/chain_snapshots/cosmos/mainnet | jq -r .snapshot.url"
    timeout: 60
```

**Chain-Specific Examples**:

```yaml
# Cosmos Hub with direct URL
chain:
  name: "cosmos"
bootstrap:
  snapshot:
    url: "https://cosmos-snapshots.polkachu.com/snapshots/cosmos/cosmos_12345678.tar.lz4"

# Osmosis with API command
chain:
  name: "osmosis"
bootstrap:
  snapshot:
    command: "curl -s https://polkachu.com/api/v2/chain_snapshots/osmosis/mainnet | jq -r .snapshot.url"

# Custom chain with your own snapshot
chain:
  name: "mychain"
bootstrap:
  snapshot:
    url: "https://my-snapshots.com/mychain-latest.tar.lz4"
```

#### How It Works

1. **Direct URL**: Downloads directly from the specified URL
2. **Custom Command**: Executes your command, expects it to return a single URL
3. **Validation**: Validates the URL format before downloading
4. **Download**: Uses aria2c for fast, resumable downloads
5. **Extract**: Extracts LZ4-compressed tar archives with progress monitoring

## 📊 Monitoring & Observability

### Prometheus Metrics
The chart exposes Prometheus metrics on port 26660 by default:

```yaml
daemon:
  monitoring:
    prometheus: true
    address: "0.0.0.0:26660"
```

### Health Checks
- **Startup Probe**: Ensures node starts properly (600 failures, 30s intervals)
- **Liveness Probe**: Monitors block height progression
- **Readiness Probe**: Checks RPC endpoint availability

### Logging
Structured JSON logging is enabled by default:

```yaml
daemon:
  logLevel: "info"
  logFormat: "json"
```

## 🔄 Upgrades & Maintenance

### Chart Upgrades

```bash
# Upgrade to new chart version
helm upgrade my-cosmos-node cosmos-node/cosmos-node --version 2.1.0

# Upgrade with new image
helm upgrade my-cosmos-node cosmos-node/cosmos-node \
  --set image.tag=v19.0.0 \
  --set chain.chainId=cosmoshub-5
```

### Data Migration

The StatefulSet ensures data persistence across upgrades. For major chain upgrades:

1. Stop the current deployment
2. Backup the data volume
3. Update configuration
4. Deploy with new parameters

### Rollback

```bash
# Rollback to previous revision
helm rollback my-cosmos-node 1
```

## 🐛 Troubleshooting

### Common Issues

#### Pod Stuck in Init
```bash
# Check init container logs
kubectl logs <pod-name> -c init-chain

# Common causes:
# - Genesis download failure
# - Insufficient storage
# - Network connectivity issues
```

#### Node Not Syncing
```bash
# Check main container logs
kubectl logs <pod-name> -c cosmos-node

# Check probe script
kubectl exec <pod-name> -- /scripts/probe.sh
```

#### Storage Issues
```bash
# Check PVC status
kubectl get pvc

# Check storage class
kubectl get storageclass
```

### Debug Mode

Enable debug logging:

```yaml
daemon:
  logLevel: "debug"
  flags:
    - "--log_level=debug"
    - "--rpc.unsafe=true"  # Only for debugging
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Testing

```bash
# Lint the chart
helm lint .

# Test template rendering
helm template test . --debug

# Test installation
helm install test . --dry-run --debug
```

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Cosmos SDK](https://github.com/cosmos/cosmos-sdk) team
- [Polkachu](https://polkachu.com) for snapshot and bootstrap services
- Cosmos community for feedback and contributions

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/cosmos/helm-charts/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cosmos/helm-charts/discussions)
- **Discord**: [Cosmos Developer Discord](https://discord.gg/cosmosnetwork)

---

*Made with ❤️ by the Cosmos community*
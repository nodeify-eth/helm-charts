# Nodeify Helm Charts

This repository contains Helm charts for Nodeify's tools and services.

## Available Charts

- indexer-tools - Tools for blockchain indexing
- cosmoshub-rpc - Blockchain node

## Usage

```bash
helm repo add nodeify https://nodeify-eth.github.io/helm-charts
helm repo update
helm install indexer-tools nodeify/indexer-tools
helm install cosmoshub-rpc nodeify/cosmoshub-rpc

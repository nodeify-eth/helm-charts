{{/*
Expand the name of the chart.
*/}}
{{- define "cosmos-node.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "cosmos-node.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "cosmos-node.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "cosmos-node.labels" -}}
helm.sh/chart: {{ include "cosmos-node.chart" . }}
{{ include "cosmos-node.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: node
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "cosmos-node.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cosmos-node.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
chain.cosmos.network/name: {{ .Values.chain.name }}
chain.cosmos.chainid/name: {{ .Values.chain.chainId }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "cosmos-node.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cosmos-node.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate image name with registry support
*/}}
{{- define "cosmos-node.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
Generate init container image name
*/}}
{{- define "cosmos-node.initImage" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.initContainer.image.registry -}}
{{- $repository := .Values.initContainer.image.repository -}}
{{- $tag := .Values.initContainer.image.tag -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
Validate chain configuration
*/}}
{{- define "cosmos-node.validateChain" -}}
{{- if not .Values.chain.name -}}
{{- fail "chain.name is required" -}}
{{- end -}}
{{- if not .Values.chain.daemon -}}
{{- fail "chain.daemon is required" -}}
{{- end -}}
{{- if not .Values.chain.home -}}
{{- fail "chain.home is required" -}}
{{- end -}}
{{- if not .Values.chain.chainId -}}
{{- fail "chain.chainId is required" -}}
{{- end -}}
{{- end }}

{{/*
Get genesis URL - no auto-detection
*/}}
{{- define "cosmos-node.genesisUrl" -}}
{{- .Values.bootstrap.genesis.url -}}
{{- end }}

{{/*
Get addrbook URL - no auto-detection
*/}}
{{- define "cosmos-node.addrbookUrl" -}}
{{- .Values.bootstrap.addrbook.url -}}
{{- end }}

{{/*
Get seeds list
*/}}
{{- define "cosmos-node.seedsList" -}}
{{- .Values.bootstrap.seeds.list -}}
{{- end }}

{{/*
Get snapshot URL or command - no auto-detection
*/}}
{{- define "cosmos-node.snapshotSource" -}}
{{- if .Values.bootstrap.snapshot.url -}}
{{- printf "direct:%s" .Values.bootstrap.snapshot.url -}}
{{- else if .Values.bootstrap.snapshot.command -}}
{{- printf "command:%s" .Values.bootstrap.snapshot.command -}}
{{- else -}}
{{- printf "none:" -}}
{{- end -}}
{{- end }}

{{/*
Generate home directory path
*/}}
{{- define "cosmos-node.homePath" -}}
{{- printf "/home/cosmos/%s" .Values.chain.home -}}
{{- end }}

{{/*
Generate data directory path
*/}}
{{- define "cosmos-node.dataPath" -}}
{{- printf "%s/data" (include "cosmos-node.homePath" .) -}}
{{- end }}

{{/*
Generate config directory path
*/}}
{{- define "cosmos-node.configPath" -}}
{{- printf "%s/config" (include "cosmos-node.homePath" .) -}}
{{- end }}

{{/*
Generate daemon command with flags
*/}}
{{- define "cosmos-node.daemonCommand" -}}
{{- $command := list .Values.chain.daemon "start" -}}
{{- $command = append $command (printf "--home=%s" (include "cosmos-node.homePath" .)) -}}
{{- $command = append $command (printf "--minimum-gas-prices=%s" .Values.chain.minGasPrices) -}}
{{- $command = append $command (printf "--grpc.address=0.0.0.0:%d" (.Values.chain.ports.grpc | int)) -}}
{{- $command = append $command (printf "--rpc.laddr=tcp://0.0.0.0:%d" (.Values.chain.ports.rpc | int)) -}}
{{- range .Values.daemon.flags -}}
{{- $command = append $command . -}}
{{- end -}}
{{- toYaml $command -}}
{{- end }}

{{/*
Common annotations
*/}}
{{- define "cosmos-node.commonAnnotations" -}}
{{- with .Values.commonAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Pod annotations
*/}}
{{- define "cosmos-node.podAnnotations" -}}
checksum/configmap: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
{{- with .Values.podAnnotations }}
{{ toYaml . }}
{{- end }}
{{- with .Values.commonAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Image pull secrets
*/}}
{{- define "cosmos-node.imagePullSecrets" -}}
{{- $secrets := list -}}
{{- range .Values.global.imagePullSecrets -}}
{{- $secrets = append $secrets . -}}
{{- end -}}
{{- range .Values.image.pullSecrets -}}
{{- $secrets = append $secrets . -}}
{{- end -}}
{{- if $secrets -}}
imagePullSecrets:
{{- range $secrets }}
  - name: {{ . }}
{{- end -}}
{{- end -}}
{{- end }}

{{/*
Volume claim template name
*/}}
{{- define "cosmos-node.volumeClaimTemplateName" -}}
{{- printf "%s-data" (include "cosmos-node.fullname" .) -}}
{{- end }}

{{/*
Generate network policy selector labels
*/}}
{{- define "cosmos-node.networkPolicySelector" -}}
{{- include "cosmos-node.selectorLabels" . }}
{{- end }}

{{/*
Validate persistence configuration
*/}}
{{- define "cosmos-node.validatePersistence" -}}
{{- if not .Values.persistence.enabled -}}
{{- fail "Persistence must be enabled for StatefulSet deployment" -}}
{{- end -}}
{{- if not .Values.persistence.size -}}
{{- fail "persistence.size is required when persistence is enabled" -}}
{{- end -}}
{{- end }}

{{/*
Generate priority class name
*/}}
{{- define "cosmos-node.priorityClassName" -}}
{{- if .Values.priorityClassName -}}
{{- .Values.priorityClassName -}}
{{- end -}}
{{- end }}

{{/*
Generate security context for pod
*/}}
{{- define "cosmos-node.podSecurityContext" -}}
{{- toYaml .Values.podSecurityContext }}
{{- end }}

{{/*
Generate security context for container
*/}}
{{- define "cosmos-node.securityContext" -}}
{{- toYaml .Values.securityContext }}
{{- end }}

{{/*
Generate probe configuration
*/}}
{{- define "cosmos-node.startupProbe" -}}
{{- if .Values.healthChecks.startup.enabled }}
httpGet:
  path: /status
  port: rpc
  scheme: HTTP
initialDelaySeconds: {{ .Values.healthChecks.startup.initialDelaySeconds }}
periodSeconds: {{ .Values.healthChecks.startup.periodSeconds }}
timeoutSeconds: {{ .Values.healthChecks.startup.timeoutSeconds }}
successThreshold: {{ .Values.healthChecks.startup.successThreshold }}
failureThreshold: {{ .Values.healthChecks.startup.failureThreshold }}
{{- end }}
{{- end }}

{{/*
Generate liveness probe configuration
*/}}
{{- define "cosmos-node.livenessProbe" -}}
{{- if .Values.healthChecks.liveness.enabled }}
httpGet:
  path: /status
  port: rpc
  scheme: HTTP
initialDelaySeconds: {{ .Values.healthChecks.liveness.initialDelaySeconds }}
periodSeconds: {{ .Values.healthChecks.liveness.periodSeconds }}
timeoutSeconds: {{ .Values.healthChecks.liveness.timeoutSeconds }}
successThreshold: {{ .Values.healthChecks.liveness.successThreshold }}
failureThreshold: {{ .Values.healthChecks.liveness.failureThreshold }}
{{- end }}
{{- end }}

{{/*
Generate readiness probe configuration
*/}}
{{- define "cosmos-node.readinessProbe" -}}
{{- if .Values.healthChecks.readiness.enabled }}
httpGet:
  path: /status
  port: rpc
  scheme: HTTP
initialDelaySeconds: {{ .Values.healthChecks.readiness.initialDelaySeconds }}
periodSeconds: {{ .Values.healthChecks.readiness.periodSeconds }}
timeoutSeconds: {{ .Values.healthChecks.readiness.timeoutSeconds }}
successThreshold: {{ .Values.healthChecks.readiness.successThreshold }}
failureThreshold: {{ .Values.healthChecks.readiness.failureThreshold }}
{{- end }}
{{- end }}
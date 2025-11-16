{{/*
Expand the name of the chart.
*/}}
{{- define "horcrux.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "horcrux.fullname" -}}
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
{{- define "horcrux.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "horcrux.labels" -}}
helm.sh/chart: {{ include "horcrux.chart" . }}
{{ include "horcrux.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: horcrux
{{- if .Values.chain.id }}
app.kubernetes.io/chain: {{ .Values.chain.id }}
{{- end }}
{{- if .Values.chain.environment }}
app.kubernetes.io/environment: {{ .Values.chain.environment }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "horcrux.selectorLabels" -}}
app.kubernetes.io/name: {{ include "horcrux.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "horcrux.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "horcrux.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper Horcrux image name
*/}}
{{- define "horcrux.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- printf "%s:%s" .Values.image.repository $tag }}
{{- end }}

{{/*
Return the proper init container image name
*/}}
{{- define "horcrux.initImage" -}}
{{- printf "%s:%s" .Values.initContainer.image.repository .Values.initContainer.image.tag }}
{{- end }}

{{/*
Return the namespace
*/}}
{{- define "horcrux.namespace" -}}
{{- default .Release.Namespace .Values.global.namespace }}
{{- end }}

{{/*
Return the headless service name
*/}}
{{- define "horcrux.serviceName" -}}
{{- printf "%s-headless" (include "horcrux.fullname" .) }}
{{- end }}

{{/*
Return the metrics service name
*/}}
{{- define "horcrux.metricsServiceName" -}}
{{- printf "%s-metrics" (include "horcrux.fullname" .) }}
{{- end }}

{{/*
Return the config map name
*/}}
{{- define "horcrux.configMapName" -}}
{{- printf "%s-config" (include "horcrux.fullname" .) }}
{{- end }}

{{/*
Generate cosigner configuration
*/}}
{{- define "horcrux.cosigners" -}}
{{- $fullname := include "horcrux.fullname" . -}}
{{- $serviceName := include "horcrux.serviceName" . -}}
{{- $namespace := include "horcrux.namespace" . -}}
{{- if and (eq .Values.shards.method "externalSecret") .Values.shards.externalSecrets.enabled }}
{{- range $i, $shardConfig := .Values.shards.externalSecrets.shardConfigs }}
- shardID: {{ int $shardConfig.shardId }}
  p2pAddr: tcp://{{ $fullname }}-{{ $i }}.{{ $serviceName }}.{{ $namespace }}.svc.cluster.local:{{ $.Values.service.headless.p2pPort }}
{{- end }}
{{- else }}
{{- range $i := until (int .Values.replicaCount) }}
- shardID: {{ add $i 1 }}
  p2pAddr: tcp://{{ $fullname }}-{{ $i }}.{{ $serviceName }}.{{ $namespace }}.svc.cluster.local:{{ $.Values.service.headless.p2pPort }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate shard secret name
*/}}
{{- define "horcrux.shardSecretName" -}}
{{- $fullname := include "horcrux.fullname" .root -}}
{{- $shardId := .shardId -}}
{{- if eq .root.Values.shards.method "externalSecret" -}}
{{- printf "%s-shard-%d" $fullname $shardId }}
{{- else if .root.Values.shards.secrets.existingSecrets -}}
{{- index .root.Values.shards.secrets.existingSecrets (sub $shardId 1) }}
{{- else -}}
{{- printf "%s-shard-%d" $fullname $shardId }}
{{- end }}
{{- end }}

{{/*
Validate configuration
*/}}
{{- define "horcrux.validateConfig" -}}
{{- if lt (int .Values.replicaCount) 2 }}
{{- fail "replicaCount must be at least 2 for Horcrux to function properly" }}
{{- end }}
{{- if and (eq .Values.horcrux.signMode "threshold") (gt (int .Values.horcrux.thresholdMode.threshold) (int .Values.replicaCount)) }}
{{- fail "threshold cannot be greater than replicaCount" }}
{{- end }}
{{- if and (eq .Values.horcrux.signMode "threshold") (lt (int .Values.horcrux.thresholdMode.threshold) 2) }}
{{- fail "threshold must be at least 2 for threshold signing mode" }}
{{- end }}
{{- if eq (len .Values.horcrux.chainNodes) 0 }}
{{- fail "At least one chain node must be configured in horcrux.chainNodes" }}
{{- end }}
{{- if and (eq .Values.shards.method "secret") (not .Values.shards.secrets.create) (eq (len .Values.shards.secrets.existingSecrets) 0) }}
{{- fail "When shards.method is 'secret' and shards.secrets.create is false, you must provide existingSecrets" }}
{{- end }}
{{- if and (eq .Values.shards.method "secret") (not .Values.shards.secrets.create) (ne (len .Values.shards.secrets.existingSecrets) (int .Values.replicaCount)) }}
{{- fail (printf "Number of existingSecrets (%d) must match replicaCount (%d)" (len .Values.shards.secrets.existingSecrets) (int .Values.replicaCount)) }}
{{- end }}
{{- if and (eq .Values.shards.method "externalSecret") (not .Values.shards.externalSecrets.enabled) }}
{{- fail "When shards.method is 'externalSecret', shards.externalSecrets.enabled must be true" }}
{{- end }}
{{- if and .Values.shards.externalSecrets.enabled (eq .Values.shards.externalSecrets.secretStoreRef.name "") }}
{{- fail "When using external secrets, secretStoreRef.name must be specified" }}
{{- end }}
{{- if and .Values.shards.externalSecrets.enabled (ne (len .Values.shards.externalSecrets.shardConfigs) (int .Values.replicaCount)) }}
{{- fail (printf "Number of shardConfigs (%d) must match replicaCount (%d)" (len .Values.shards.externalSecrets.shardConfigs) (int .Values.replicaCount)) }}
{{- end }}
{{- end }}

{{/*
Return pod labels including custom labels
*/}}
{{- define "horcrux.podLabels" -}}
{{ include "horcrux.selectorLabels" . }}
app.kubernetes.io/component: horcrux
{{- if .Values.chain.id }}
chain: {{ .Values.chain.id }}
{{- end }}
{{- if .Values.chain.environment }}
environment: {{ .Values.chain.environment }}
{{- end }}
{{- with .Values.podLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Return pod annotations
*/}}
{{- define "horcrux.podAnnotations" -}}
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
{{- with .Values.podAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}
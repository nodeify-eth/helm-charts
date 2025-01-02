# templates/_helpers.tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "cosmoshub.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "cosmoshub.fullname" -}}
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
{{- define "cosmoshub.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "cosmoshub.labels" -}}
helm.sh/chart: {{ include "cosmoshub.chart" . }}
{{ include "cosmoshub.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "cosmoshub.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cosmoshub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Define RPC port
*/}}
{{- define "cosmoshub.rpc" -}}
{{- .Values.service.port.rpc }}
{{- end }}

{{/*
Define P2P port
*/}}
{{- define "cosmoshub.p2p" -}}
{{- .Values.service.port.p2p }}
{{- end }}

{{/*
Define GRPC port
*/}}
{{- define "cosmoshub.grpc" -}}
{{- .Values.service.port.grpc }}
{{- end }}
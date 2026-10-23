{{/* Resolve once in chart-qualified root context; never store credentials in Values. */}}
{{- define "firehose-ethereum.jwt.resolve" -}}
{{- if not (hasKey . "_firehose-ethereum_jwt") -}}
  {{- $state := dict "active" false "external" false "name" (printf "%s-firehose-jwt" .Release.Name) -}}
  {{- if eq .Values.mode "full" -}}
    {{- $components := .Values.fullMode.components -}}
    {{- if or $components.reader.enabled $components.lighthouse.enabled $components.opNode.enabled -}}
      {{- $_ := set $state "active" true -}}
      {{- $jwt := .Values.fullMode.jwt -}}
      {{- if not (kindIs "map" $jwt) -}}
        {{- fail "fullMode.jwt must be a map with string existingSecret and revision" -}}
      {{- end -}}
      {{- if or (not (kindIs "string" $jwt.existingSecret)) (not (kindIs "string" $jwt.revision)) -}}
        {{- fail "fullMode.jwt.existingSecret and fullMode.jwt.revision must be strings" -}}
      {{- end -}}
      {{- $_ := set $state "revision" $jwt.revision -}}
      {{- if $jwt.existingSecret -}}
        {{- if eq $jwt.existingSecret $state.name -}}
          {{- fail "fullMode.jwt.existingSecret must use a new external name, different from the managed Secret name, to avoid Helm deletion/ownership conflicts" -}}
        {{- end -}}
        {{- $_ := set $state "external" true -}}
        {{- $_ := set $state "name" $jwt.existingSecret -}}
      {{- else -}}
        {{- if not $components.reader.enabled -}}
          {{- fail "enabled JWT clients with reader disabled require a namespace-local Secret containing jwt.hex; set fullMode.jwt.existingSecret" -}}
        {{- end -}}
        {{- $existing := lookup "v1" "Secret" .Release.Namespace $state.name -}}
        {{- $encoded := "" -}}
        {{- if $existing -}}
          {{- $data := $existing.data -}}
          {{- if not (kindIs "map" $data) -}}
            {{- fail "managed JWT Secret has invalid data; restore valid jwt.hex or use fullMode.jwt.existingSecret" -}}
          {{- end -}}
          {{- $encoded = index $data "jwt.hex" -}}
          {{- if not (kindIs "string" $encoded) -}}
            {{- fail "managed JWT Secret requires jwt.hex; restore it or use fullMode.jwt.existingSecret" -}}
          {{- end -}}
          {{- $decoded := b64dec $encoded -}}
          {{- if or (ne (b64enc $decoded) $encoded) (not (regexMatch "^[0-9a-fA-F]{64}$" $decoded)) -}}
            {{- fail "managed JWT Secret jwt.hex must encode exactly 64 ASCII hex characters; restore it or use fullMode.jwt.existingSecret" -}}
          {{- end -}}
        {{- else -}}
          {{- if .Release.IsUpgrade -}}
            {{- fail "managed JWT Secret is missing during upgrade; restore it or provision a new Secret and set fullMode.jwt.existingSecret" -}}
          {{- end -}}
          {{- $encoded = printf "%x" (randBytes 32 | b64dec) | b64enc -}}
        {{- end -}}
        {{- $_ := set $state "encoded" $encoded -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
  {{- $_ := set . "_firehose-ethereum_jwt" $state -}}
{{- end -}}
{{- end -}}

{{- define "firehose-ethereum.jwt.name" -}}
{{- include "firehose-ethereum.jwt.resolve" . -}}
{{- index . "_firehose-ethereum_jwt" "name" -}}
{{- end -}}

{{- define "firehose-ethereum.jwt.annotations" -}}
{{- $root := .root -}}
{{- $annotations := .annotations | default dict -}}
{{- if or (hasKey $annotations "checksum/jwt-secret") (hasKey $annotations "firehose.streamingfast.io/jwt-revision") -}}
  {{- fail "podAnnotations keys checksum/jwt-secret and firehose.streamingfast.io/jwt-revision are reserved; use fullMode.jwt.revision for coordinated rollouts" -}}
{{- end -}}
{{- include "firehose-ethereum.jwt.resolve" $root -}}
{{- $state := index $root "_firehose-ethereum_jwt" -}}
{{- if not $state.external }}
checksum/jwt-secret: {{ $state.encoded | b64dec | sha256sum | quote }}
{{- end }}
firehose.streamingfast.io/jwt-revision: {{ $state.revision | quote }}
{{- with $annotations }}
{{ toYaml . }}
{{- end -}}
{{- end -}}

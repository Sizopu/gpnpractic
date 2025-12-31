{{/*
Common labels.
*/}}
{{- define "qb.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/part-of: quotation-book
{{- end -}}

{{/*
Image helper.
Usage: {{ include "qb.image" (dict "image" .Values.backend.image "global" .Values.global) }}
*/}}
{{- define "qb.image" -}}
{{- $img := .image -}}
{{- $global := .global -}}
{{- $registry := default $global.defaultRegistry $img.registry -}}
{{- $repo := $img.repository -}}
{{- $tag := default $global.defaultTag $img.tag -}}
{{- printf "%s/%s:%s" $registry $repo $tag -}}
{{- end -}}

{{/*
Pull policy helper.
Usage: {{ include "qb.pullPolicy" (dict "image" .Values.backend.image "global" .Values.global) }}
*/}}
{{- define "qb.pullPolicy" -}}
{{- $img := .image -}}
{{- $global := .global -}}
{{- default $global.defaultPullPolicy $img.pullPolicy -}}
{{- end -}}

{{/*
Optional imagePullSecrets.
*/}}
{{- define "qb.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
{{ toYaml .Values.global.imagePullSecrets | indent 2 }}
{{- end }}
{{- end -}}

{{/*
Wait-for init container snippet.
Usage:
  {{ include "qb.waitFor" (dict "name" "wait-postgres" "host" "quotation-book-postgres" "port" 5432 "timeout" 180) }}
*/}}
{{- define "qb.waitFor" -}}
- name: {{ .name }}
  image: busybox:1.36
  command:
    - sh
    - -c
    - >
      set -e;
      echo "Waiting for {{ .host }}:{{ .port }} ...";
      end=$(( $(date +%s) + {{ default 180 .timeout }} ));
      while [ $(date +%s) -lt $end ]; do
        nc -z {{ .host }} {{ .port }} && exit 0;
        sleep 2;
      done;
      echo "Timeout waiting for {{ .host }}:{{ .port }}" >&2;
      exit 1
{{- end -}}

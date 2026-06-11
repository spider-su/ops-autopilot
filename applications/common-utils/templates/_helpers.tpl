{{/*
  app.name — the release name, used as the resource name throughout.
*/}}
{{- define "app.name" -}}
{{- .Release.Name -}}
{{- end }}

{{/*
  app.image — full image string "repository:tag".
*/}}
{{- define "app.image" -}}
{{- printf "%s:%s" .Values.image.repository .Values.image.tag -}}
{{- end }}

{{/*
  app.labels — standard labels applied to every resource.
*/}}
{{- define "app.labels" -}}
app: {{ include "app.name" . }}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ include "app.name" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
  app.selectorLabels — minimal labels used in selector/matchLabels.
  Must be a strict subset of app.labels and must never change after first deploy.
*/}}
{{- define "app.selectorLabels" -}}
app: {{ include "app.name" . }}
{{- end }}


{{- define "home-infra-agent.name" -}}
{{- .Release.Name -}}
{{- end }}
{{- define "home-infra-agent.labels" -}}
app.kubernetes.io/name: {{ include "home-infra-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}
{{- define "home-infra-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "home-infra-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

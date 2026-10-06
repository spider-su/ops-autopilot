{{- define "orchestrator.labels" -}}
app.kubernetes.io/name: investory-orchestrator
app.kubernetes.io/instance: investory-orchestrator
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{- define "orchestrator.image" -}}
{{- printf "%s:%s" .Values.image.repository .Values.image.tag -}}
{{- end }}

{{- define "orchestrator.podSecurityContext" -}}
automountServiceAccountToken: false
securityContext:
  seccompProfile:
    type: RuntimeDefault
{{- end }}

{{- define "orchestrator.containerSecurityContext" -}}
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
{{- end }}

{{- define "orchestrator.imagePullSecrets" -}}
{{- with .Values.image.pullSecrets }}
imagePullSecrets:
  {{- range . }}
  - name: {{ . | quote }}
  {{- end }}
{{- end }}
{{- end }}

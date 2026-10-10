{{- define "vaxgenesis.name" -}}{{ .Chart.Name }}{{- end -}}
{{- define "vaxgenesis.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "vaxgenesis.name" . }}
{{- end -}}

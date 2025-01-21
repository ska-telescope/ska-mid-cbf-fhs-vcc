{{- define "findByName" -}}
{{- $name := index . 0 -}}
{{- $list := index . 1 -}}
{{- range $list }}
  {{- if eq .id $name }}
    {{- toYaml . | nindent 0 }}
    {{- break }}
  {{- end }}
{{- end }}
{{- end }}

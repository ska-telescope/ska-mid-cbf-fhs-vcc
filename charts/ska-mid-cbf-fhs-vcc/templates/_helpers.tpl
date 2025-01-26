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

{{- define "setToleration" }}
{{- $key := index . 0 -}}
{{- $operator := index . 1 -}}
{{- $value := index . 2 -}}
{{- $effect := index . 3 -}}
tolerations:
  - key: {{ $key | quote }}
    operator: {{ $operator | quote }}
    value: {{ $value | quote }}
    effect: {{ $effect | quote }}
{{- end -}}
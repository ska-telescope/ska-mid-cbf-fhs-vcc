{{/*-------------------------------------------------
  Helper: name of the secret that contains BAR_API_TOKEN
  - shared between ska-mid-cbf-fhs-vcc chart and ska-mid-cbf-umbrella chart
-------------------------------------------------*/}}
{{- define "fhs-bar-secret-name" -}}
{{ .Release.Name }}-bar-secret-fhs-vcc
{{- end -}}
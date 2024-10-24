{{ define "substitute-device-id" }}
{{- $input := index . 0 -}}
{{- $deviceId := ((index . 1) | int) -}}
{{- $receptorId := (mod (sub $deviceId 1) 3) -}}
{{- if kindIs "string" $input -}}
{{- $input | replace "<deviceId>" (printf "%d" $deviceId) | replace "<deviceId000>" (printf "%03d" $deviceId) | replace "<receptorId>" (printf "%d" $receptorId) -}}
{{- else -}}
{{- $input -}}
{{- end -}}
{{ end }}

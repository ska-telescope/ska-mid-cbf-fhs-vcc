{{/*
Common template helpers for the ska-mid-cbf-fhs-vcc chart.
*/}}

{{/*
  Find a vccUnit by name in the list of vccUnits.
  Expects a two-element list, e.g. ["vccUnitName", .Values.vccUnits],
  and returns the vccUnit as a YAML-encoded object.
*/}}
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

{{/*
Generate a sequence from a given range.
Expects a two-element list, e.g. [1, 6],
and returns a YAML-encoded list of numbers from start to end (inclusive).
*/}}
{{- define "generateInstanceSequence" -}}
  {{- $range := . -}}
  {{- $start := index $range 0 -}}
  {{- $end := index $range 1 -}}
  {{- $count := int (add (sub $end $start) 1) -}}
  {{- $numbers := list -}}
  {{- range until $count -}}
    {{- $num := add $start . -}}
    {{- $numbers = append $numbers (printf "fhs-vcc-%d" (int $num)) -}}
  {{- end -}}
  {{- /* wrap the list in an object */ -}}
  {{- toJson (dict "sequence" $numbers) -}}
{{- end -}}
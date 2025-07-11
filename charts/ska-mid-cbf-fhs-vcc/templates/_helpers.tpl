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
and returns a YAML-encoded list of instance names from start to end (inclusive).
*/}}
{{- define "generateInstanceSequence" -}}
  {{- $range := . -}}
  {{- $start := index $range 0 -}}
  {{- $end := index $range 1 -}}
  {{- $count := int (add (sub $end $start) 1) -}}
  {{- $instances := list -}}
  {{- range until $count -}}
    {{- $num := add $start . -}}
    {{- $instances = append $instances (printf "vcc-%d" (int $num)) -}}
  {{- end -}}
  {{- /* wrap the list in an object */ -}}
  {{- toJson (dict "sequence" $instances) -}}
{{- end -}}

{{- define "generateServerInstances" -}}
{{- $instance := index . 0 -}}
{{- $fhsVccUnit := index . 1 -}}
{{- $devices := index . 2 -}}
{{- $globalProperties := index . 3 -}}
{{- $instanceNum := index . 4 -}}
{{- $deviceId := add $instanceNum (mul 6 (sub (int $fhsVccUnit.unitNum) 1)) -}}
{{- $fpgaNum := fromJson (include "calculateFPGANum" (list $fhsVccUnit.unitNum $deviceId) | trim) -}}

- name: "{{ $instance }}"
  classes:
  {{- range $device := $devices }}
    - name: {{ $device.name }}
      devices:
      {{- range $multiplicity := (untilStep 1 ($device.multiplicity | int | default 1 | add1 | int ) 1) }}
      {{- $scope := dict "deviceId" (int $deviceId) "deviceId000" (printf "%03d" (int $deviceId)) "receptorId" (mod (sub (int $deviceId) 1) 3) "unitEmulationMode" (printf "%s" $fhsVccUnit.emulationMode) "networkSwitchId" (printf "%s" $fhsVccUnit.networkSwitchId) "bmcEndpointIp" (printf "%s" $fhsVccUnit.bmcEndpointIp) "multiplicity" $multiplicity "unitNum" (printf "%d" (int $fhsVccUnit.unitNum)) "fpgaNum" (printf "%d" (int $fpgaNum.fpgaNum)) }}
      - name: {{ tpl $device.path $scope }}
        properties:
          {{- range $name, $default := $globalProperties }}
          - name: {{ snakecase $name }}
            values:
            - "{{ tpl ((get $device $name) | default $default) $scope }}"
          {{- end }}
          {{- range $index, $property := $device.properties }}
          - name: {{ $property.name }}
            values:
            {{- range $devicePropMultiplicity := (untilStep 1 ($property.multiplicity | int | default 1 | add1 | int ) 1) }}
            {{- $propScope := merge (dict "devicePropMultiplicity" $devicePropMultiplicity) $scope }}
            {{- range $index, $value := $property.values }}
            - "{{ tpl $value $propScope }}"
            {{- end }}
            {{- end }}
          {{- end }}
      {{- end }}
  {{- end }}
{{- end -}}

{{- define "calculateFPGANum" -}}
  {{- $unitNum := index . 0 -}}
  {{- $vccNum := index . 1 -}}

  {{- $instanceNum :=  sub $vccNum (mul (sub $unitNum 1) 6) -}}
  {{- $fpgaBoardNum := floor (addf (divf (subf $instanceNum 1) 3) 1) -}}

  {{- toJson (dict "fpgaNum" $fpgaBoardNum) -}}
{{- end -}}
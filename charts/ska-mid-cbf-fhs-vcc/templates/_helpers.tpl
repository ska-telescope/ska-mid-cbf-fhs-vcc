{{- define "ska-mid-cbf-fhs-vcc.stack-instance" }}
{{- $values := .Values }}
{{- $instance := .instance }}
  name: "{{ $instance.name }}"
  classes:
  {{- range $index, $device := $values.devices }}
  {{- $deviceId := $device.deviceId | default $instance.deviceId | int }}
  - name: {{ $device.name }}
    devices:
    {{- range $multiplicity := (untilStep 1 ($device.multiplicity | int | default 1 | add1 | int ) 1) }}
    {{- $scope := dict "deviceId" $deviceId "deviceId000" (printf "%03d" $deviceId) "receptorId" (mod (sub $deviceId 1) 3) "multiplicity" $multiplicity }}
    - name: {{ tpl $device.path $scope }}
      properties:
        {{- range $name, $default := $values.properties }}
        - name: {{ snakecase $name }}
          values:
          - "{{ tpl ((get $device $name) | default (get $instance $name) | default $default) $scope }}"
        {{- end }}
        {{- range $index, $property := $device.properties }}
        - name: {{ $property.name }}
          values:
          {{- range $index, $value := $property.values }}
          - "{{ tpl $value $scope }}"
          {{- end }}
        {{- end }}
    {{- end }}
  {{- end }}
{{- end }}
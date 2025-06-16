{{- define "ska-mid-cbf-fhs-vcc.fhsVccStack" -}}
{{- $instances := .instances -}}
{{- $fhsVccUnit := .fhsVccUnit }}
name: fhsvcc
function: fhsvcc
domain: sensing
command: "FhsVccStackDeviceServer"
instances:
{{ toYaml $instances | nindent 2 }}
depends_on:
  - device: sys/database/2
readinessProbe:
  initialDelaySeconds: 20
  periodSeconds: 10
  timeoutSeconds: 5
  successThreshold: 1
  failureThreshold: 10
livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  successThreshold: 1
  failureThreshold: 10
server:
  name: "FhsVccStackDeviceServer"
  instances:
    {{- range $index, $instance := $instances }}
    {{- $deviceId := add (add $index 1) (mul 6 (sub (int $fhsVccUnit.unitNum) 1)) }}
    - name: "{{ $instance }}"
      classes:
      {{- range $device := $.Values.devices }}
        - name: {{ $device.name }}
          devices:
          {{- range $multiplicity := (untilStep 1 ($device.multiplicity | int | default 1 | add1 | int ) 1) }}
          {{- $scope := dict "deviceId" (int $deviceId) "deviceId000" (printf "%03d" (int $deviceId)) "receptorId" (mod (sub (int $deviceId) 1) 3) "unitEmulationMode" (printf "%s" $fhsVccUnit.emulationMode) "networkSwitchId" (printf "%s" $fhsVccUnit.networkSwtichId) "bmcEndpointIp" (printf "%s" $fhsVccUnit.bmcEndpointIp) "multiplicity" $multiplicity  }}
          - name: {{ tpl $device.path $scope }}
            properties:
              {{- range $name, $default := $.Values.properties }}
              - name: {{ snakecase $name }}
                values:
                - "{{ tpl ((get $device $name) | default $default) $scope }}"
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

image:
  registry: "{{.Values.midcbf.image.registry}}"
  image: "{{.Values.midcbf.image.image}}"
  tag: "{{.Values.midcbf.image.tag}}"
  pullPolicy: "{{.Values.midcbf.image.pullPolicy}}"

volume:
  existingClaimName: "fhs-vcc-bitstream-pv"
  mountPath: "{{ .Values.bitstreamMountPath }}"
  readOnly: false

{{- if .fhsVccUnit.toleration }}
{{ $fhsToleration := .fhsVccUnit.toleration }}
tolerations:
  - key: "vcc"
    operator: "Equal"
    value: {{ .fhsVccUnit.id }}
    effect: "NoSchedule"
{{- end }}

{{- if .fhsVccUnit.affinity }}
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
          - key: "vcc"
            operator: In
            values:
              - {{ .fhsVccUnit.affinity }}
{{- end }}

{{- end -}}
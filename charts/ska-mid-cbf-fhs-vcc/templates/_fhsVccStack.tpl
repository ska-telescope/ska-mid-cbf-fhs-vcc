{{- define "ska-mid-cbf-fhs-vcc.fhsVccStack" -}}
{{- $instance := .instance -}}
{{- $fhsVccUnit := .fhsVccUnit -}}
{{- $serverInstances := .serverInstances -}}
name: fhsvcc
function: fhsvcc
domain: sensing
command: "FhsVccStackDeviceServer"
instances:
  {{ list $instance }}
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
    {{ $serverInstances }}
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
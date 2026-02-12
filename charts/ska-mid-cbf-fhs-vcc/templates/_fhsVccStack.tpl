{{- define "ska-mid-cbf-fhs-vcc.fhsVccStack" -}}
{{- $instance := .instance -}}
{{- $fhsVccUnit := .fhsVccUnit -}}
{{- $serverInstances := .serverInstances -}}
{{- $deviceCommand := .deviceCommand -}}
name: fhsvcc
function: fhsvcc
domain: sensing
command: {{ $deviceCommand }}
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
  name: {{ $deviceCommand }}
  instances:
    {{ $serverInstances }}
image:
  registry: "{{.Values.midcbf.image.registry}}"
  image: "{{.Values.midcbf.image.image}}"
  tag: "{{.Values.midcbf.image.tag}}"
  pullPolicy: "{{.Values.midcbf.image.pullPolicy}}"

{{- if $fhsVccUnit.bitstreamDownloadJobEnabled }}
volume:
  existingClaimName: "fhs-vcc-bitstream-pv"
  mountPath: "{{ .Values.bitstreamMountPath }}"
  readOnly: false
{{- end }}

{{- if $fhsVccUnit.toleration }}
tolerations:
  - key: "node-type"
    operator: "Equal"
    value: {{ $fhsVccUnit.toleration }}
    effect: "NoSchedule"
{{- end }}

{{- if $fhsVccUnit.affinity }}
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
          - key: "node-type"
            operator: In
            values:
              - {{ $fhsVccUnit.affinity }}
{{- end }}

{{- end -}}
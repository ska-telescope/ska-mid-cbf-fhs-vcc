# ska-mid-cbf-fhs-vcc

Please see the [readthedocs](https://developer.skao.int/projects/ska-mid-cbf-fhs-vcc/en/latest/) for installation and usage

# AJ Kube Guide:
## Preconditions
1. AJ Kube has already been built using the prototyping repo

## Building the image
```make oci-build```

### Loading the image into the aj kube cluster
```kind load docker-image artefact.skao.int/ska-mid-cbf-sim-devices:0.0.1 --name <cluster-name>``` 

### Installing the chart
```make k8s-install-chart MINIKUBE=true AJ_KUBE=true```


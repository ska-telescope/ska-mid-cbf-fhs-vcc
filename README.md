# ska-mid-cbf-fhs-vcc

Please see the [readthedocs](https://developer.skao.int/projects/ska-mid-cbf-fhs-vcc/en/latest/) for installation and usage

# Using UV

1. Activate your virtual env
2. run `pip install uv`
3. run `uv sync --active`

# AJ Kube Guide:
## Preconditions
1. AJ Kube has already been built using the prototyping repo

## Building the image
```make oci-build```

### Loading the image into the aj kube cluster
```kind load docker-image artefact.skao.int/ska-mid-cbf-fhs-vcc:<tag> --name <cluster-name>``` 

### Installing the chart
```make k8s-deploy-dev```

# Repository Best Practices
* When working in this repository, if using VS Code, please set at least the following in your workspace settings:
```json
{
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.diagnosticSeverityOverrides": {
        "reportPrivateImportUsage": "none",
        "reportRedeclaration": "information",
    },
}
```
This enables very basic type-checking which can help catch unexpected issues early.

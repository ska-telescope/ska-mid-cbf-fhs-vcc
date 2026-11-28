# ska-mid-cbf-fhs-vcc

Please see the [readthedocs](https://developer.skao.int/projects/ska-mid-cbf-fhs-vcc/en/latest/) for installation and usage

## Using UV

1. Activate your virtual env
2. run `pip install uv`
3. run `uv sync --active`

## AJ Kube Guide:
### Preconditions
1. AJ Kube has already been built using the prototyping repo

### Building the image
```make oci-build```

#### Loading the image into the aj kube cluster
```kind load docker-image artefact.skao.int/ska-mid-cbf-fhs-vcc:<tag> --name <cluster-name>``` 

#### Installing the chart
```make k8s-deploy-dev```

## Repository Best Practices
* When working in this repository, basic type-checking is enforced via pyright which can help catch unexpected issues early.
  Most errors will be shown with error/warning squiggles in VS Code, which automatically picks up the pyrightconfig.json configuration.

To validate that the entire repository adheres to the type-checking rules, run:
```bash
make python-typecheck
```


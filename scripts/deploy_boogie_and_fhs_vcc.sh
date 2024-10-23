#!/bin/bash

docker build -t ska-mid-cbf-fhs-vcc-boogie:0.0.1 -f .images/ska-mid-cbf-fhs-vcc-boogie/Dockerfile .

make oci-build-all && make k8s-install-chart

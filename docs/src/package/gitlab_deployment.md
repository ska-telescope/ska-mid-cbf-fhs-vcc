# Gitlab Deployment

This page will describe how to deploy the FHS-VCC device servers in emulation mode by cloning the projct from gitlab.

## Emulator Setup

First thing to do is ensure that the server you're deploying the FHS-VCC server on has been deployed and is running.  This step is performed separately from the deployment of the FHS-VCC device servers.

Please follow the emulator deployment instructions found in the emulators readthedocs here:  [Emulator Deployment Instructions](https://developer.skao.int/projects/ska-mid-cbf-emulators/en/latest/emulator_subpages/emulator_usage.html)

## FHS-VCC Setup

Follow these steps to build a local image of the ska-mid-cbf-fhs-vcc project and deploy in minikube for testing

### Minikube Setup

Follow the [Minikube Setup](./minikube_setup.md) instructions first to get a cluster up and running

### Deployment Steps
1. Clone the repository from gitlab and navigate inside it

```
https://gitlab.com/ska-telescope/ska-mid-cbf-fhs-vcc

cd ska-mid-cbf-fhs-vcc
```

2. Initialize the git submodules
```
git submodule init
git submodule update
```

3. Enter the minikube docker environment
```
eval $(minikube docker-env)
```

4. Build and deploy the local images
```
./scripts/deploy_boogie_and_fhs_vcc.sh
```

6. Verify deployment of the device servers using kubectl or k9s
using kubectl
```
kubectl get pods -n ska-mid-cbf
```

using k9s
```
k9s
```
then navigate the the namespace ska-mid-cbf and verify pods have started up successfully

## Accessing the device servers using Boogie

The ska-mid-cbf-fhs-vcc project comes with a pod that is running Boogie.  Boogie is a GUI that allows you to access the running device servers / devices and access and manipulate their attributes , properties and to also run commands.  

To access boogie please run the following command:
```
kubectl exec -it -n ska-mid-cbf <boogie pod name> -- bash -c boogie
```

Alternativly you can run boogie from k9s by entering the shell of the pod.  From the terminal run
```
k9s
```
- Inside k9s navigate to the container through its namespace ska-mid-cbf -> boogie container -> then press 's' to enter the shell of the container
- From inside the container run
```
boogie
```

For more information regarding boogie please see its gitlab page: [Boogie](https://gitlab.com/nurbldoff/boogie)
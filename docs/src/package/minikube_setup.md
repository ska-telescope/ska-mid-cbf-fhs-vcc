# Minikube setup
The following steps will describe how to setup minikube using the ska-cicd-minikube-deploy project.

1. Clone the repository from gitlab
```
https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-minikube.git
```

2. Initialize the git submodules
```
git submodule init
git submodule update
```

3. Create new minikube cluster
```
make minikube-install CPUS=4 DRIVER=docker
```

optionally you may include the following paramaters

| Param | Desc                                   |
|-------|----------------------------------------|
| CPUS  | How many cpus the cluster should use   |
| MEM   | How much memory the cluster should use |
| PROFILE | The name of the profile to create    |

4. Docker version bug fix
- In the current version of ska-cicd-minikube-deploy the docker version that gets installed with minikube is to high for use with the ska-tango pytango images and needs to be downgraded.  
- Perform the following to downgrade the docker version in the minikube container

    A. Get the container ID where the container is named after the minikube profile (minikube by default)
    ```
    docker container ls
    ```

    B. Enter the container using the following
    ```
    docker exec -it <container id> /bin/bash
    ```

    C. Copy / paste and run the following to downgrade the docker version to 24.0.7
    ```
    apt-get update && VERSION_STRING=5:24.0.7-1~ubuntu.22.04~jammy && apt-get install -y --allow-downgrades docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin && sleep 5 && systemctl restart docker && sleep 5 && systemctl restart docker
    ```

    D. Exit the container
    ```
    exit
    ```

    E. Switch to your minikube profile and start minikube again as the API will have stopped running:
    ```
    minikube profile <profile name> && minikube start
    ```
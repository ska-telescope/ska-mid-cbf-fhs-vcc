# Dev Deployment

This document will outline how to deploy the ska-mid-cbf-fhs-vcc device servers to a minikube cluster running on a development server.  These instructions should not be used for production.


## Deployment Steps


### Local Machine
1. On your local machine Archive and compress the project using tar.gz.  The following command excludes the projects .venv folder and ensures only the projects file structure gets archived.

    `tar --exclude='.venv' -cvzf -C <path to project home directory> <project name>`

2. Copy the archived project to the remote dev server.  This can be done using something like mobaXterm or the following SCP command:

    `scp <archived-project> <username>@<remote-host-name>:<remote-path>`
    
    eg:
    
    `scp ska-mid-cbf-fhs-vcc.tar.gz testUser@your-dev-server.com:/home/testUser/deploy`

### Dev Server
1. On the dev server ensure your minikube cluster is running, that you are using minikubes docker-env and the correct profile by first running:

    `eval $(minikube docker-env)`

    Then
    
    `minikube status`

2. Once confirmed minikube is running and configured to use its docker-evn navigate into directory that received the archived project and untar it

    `tar xvzf <project-name>.tar.gz`

3. Navigate inside the project and build the docker image (note the unique tag should match the ska-mid-cbf-fhs-vcc tag in your charts value.yaml file for deployment)

    `docker build -t ska-mid-cbf-fhs-vcc:<unique-tag> .`

4. Once built run, to install the charts to your cluster run the following from the projects root directory

    `make k8s-install-chart`

    4a. If you recieve a make error where k8s-install-chart doesn't exit run the following commands and then the above command again

        `git submodule init && git submodule update`

5. Check everythings up and running using k9s

    `$> k9s`


## Teardown Steps
1. To uninstall the charts run the following from the projects root directory
 
    `make k8s-uninstall-chart`

2. (Optional) Remove the docker image

    `docker image rm ska-mid-cbf-fhs-vcc:<unique-tag>`

3. (Optional) Remove minikube node

    `minikube delete`


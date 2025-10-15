import logging
import os
from typing import Any

import parse
import yaml
from kubernetes import client, config
from Pyro5.api import Proxy


class PyroDriver:
    def __init__(self, logger: logging.Logger, driver_name: str):
        self.logger = logger
        self.driver_name = driver_name

        self.ns_host = self.get_host_ip()
        self.ns_port = int(os.getenv("NS_PORT", "9090"))

        self.logger.info(f"...locate_ns using host={self.ns_host}, port={self.ns_port}")
        self.pyro_uri = f"PYRONAME:{driver_name}_driver@{self.ns_host}:{self.ns_port}"

    def configure(self, config: dict):
        self.run_command("configure", config)

    def status(self, clear: bool):
        return self.run_command("status", clear)

    def run_command(self, command_name: str, param: Any):
        try:
            with Proxy(self.pyro_uri) as p:
                p._pyroTimeout = 5.0
                fn = getattr(p, command_name)
                return fn(param)
        except Exception as ex:
            self.logger.error(f"Unable to run command {command_name} with param {param}:  {repr(ex)}")
            raise ex

    def get_config_file(self) -> dict:
        try:
            config_file = {}

            with open("/app/mnt/pyro_test_config/pyro-test-configmap.yaml", "r") as file:
                config_file: dict = yaml.safe_load(file)

            return config_file
        except Exception as ex:
            self.logger.error(f"Unable to open test_config.yaml; {repr(ex)}")
            raise ex

    def get_location(self, name: str):
        print(f"::: LOCATION NAME::: {name}")

        forms = {
            "ska-vcc-vcc": "{card}_receptor{lane}_",
            "ska-base": "{card}_",
        }
        for _category, form in forms.items():
            form_rem = form + "{}"
            match = parse.search(form_rem, name, evaluate_result=False)
            if match:
                break
        else:
            self.logger.error(f"Name '{name}' doesn't match any of the known location strings: {forms}")
            return
        result = match.evaluate_result()
        form_parts = result.named.values()
        local_name = result.fixed[0]
        return "-".join(form_parts), local_name

    def get_host_ip(self):
        """
        Fetches the node IP address from inside a pod.
        Requires the pod to have a ServiceAccount with get pod permissions.
        """
        try:
            # Load Kubernetes config from the pod's environment
            config.load_incluster_config()
            v1 = client.CoreV1Api()

            # Get the pod's own name and namespace from the environment
            pod_name = os.getenv("HOSTNAME")

            # In a pod, HOSTNAME is the pod's name
            try:
                with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
                    namespace = f.read().strip()
            except FileNotFoundError:
                return "namespace file not found..."

            if not pod_name or not namespace:
                raise ValueError("Could not determine pod name or namespace from environment.")

            # Get the pod's status from the Kubernetes API
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

            self.logger.info(f":::: POD INFO: {pod}")

            host_ip = pod.status.host_ip
            self.logger.info(f":::: HOST_IP: {host_ip}")

            node_name = pod.spec.node_name
            self.logger.info(f":::: NODE_NAME: {node_name}")

            # The host IP is available under status.host_ip
            return host_ip
        except client.ApiException as e:
            self.logger.error(f"Error accessing Kubernetes API: {e}")
            return None
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            return None

import logging
import os
from typing import Any

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
        self.run_command("status", clear)

    def run_command(self, command_name: str, param: Any):
        try:
            with Proxy(self.pyro_uri) as p:
                p._pyroTimeout = 5.0
                fn = getattr(command_name)
                return fn(param)
        except Exception as ex:
            self.logger.error(f"Unable to run command {command_name} with param {param}:  {repr(ex)}")
            raise ex

    def get_config_file(self) -> dict:
        try:
            config_file = {}

            self.logger.info(f"::::: CURRENT DIR: {os.getcwd()} :::::")

            with open("config/test_config.yaml", "r") as file:
                config_file: dict = yaml.safe_load(file)

            return config_file
        except Exception as ex:
            self.logger.error(f"Unable to open test_config.yaml; {repr(ex)}")
            raise ex

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

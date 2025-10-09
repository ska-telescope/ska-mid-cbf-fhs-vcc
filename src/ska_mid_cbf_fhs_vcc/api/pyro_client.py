import logging
import os

from kubernetes import client, config
from Pyro5.api import locate_ns


class PyroClient:
    def __init__(
        self,
        logger: logging.Logger,
    ):
        self.logger = logger
        self.ns_host = self.get_host_ip()
        self.ns_port = int(os.getenv("NS_PORT", "9090"))

    def ping(self):
        try:
            self.logger.info(f"...locate_ns using host={self.ns_host}, port={self.ns_port}")

            self.ns = locate_ns(host=self.ns_host, port=self.ns_port)
            self.ns._pyroBind()
            self.ns.ping()
            assert self.ns._pyroUri.object == "Pyro.NameServer"
            self.logger.info(f"OK: {self.ns._pyroUri}")
        finally:
            try:
                self.ns._pyroRelease()
            except Exception:
                self.logger.info("Error releasing ns")

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
            with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read() as namespace:
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
            return "unable to get host_ip"
        except client.ApiException as e:
            print(f"Error accessing Kubernetes API: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

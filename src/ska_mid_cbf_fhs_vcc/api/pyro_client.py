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

    def get_host_ip():
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
            namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

            if not pod_name or not namespace:
                raise ValueError("Could not determine pod name or namespace from environment.")

            # Get the pod's status from the Kubernetes API
            pod_info = v1.read_namespaced_pod_status(name=pod_name, namespace=namespace)
            
            # The host IP is available under status.host_ip
            return pod_info.status.host_ip
        except client.ApiException as e:
            print(f"Error accessing Kubernetes API: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


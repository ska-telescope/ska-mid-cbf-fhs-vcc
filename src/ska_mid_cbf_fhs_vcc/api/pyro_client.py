import logging
import os

from Pyro5.api import locate_ns


class PyroClient():
    def __init__(self, logger: logging.Logger,):
        self.logger = logger
        self.ns_host = os.environ["NS_HOST"]
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

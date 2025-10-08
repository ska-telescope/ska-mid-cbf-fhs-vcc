import os

from Pyro5.api import locate_ns


class PyroClient:
    def __init__(self):
        self.ns_host = os.environ["NS_HOST"]
        self.ns_port = int(os.getenv("NS_PORT", "9090"))

    def ping(self):
        try:
            print(f"...locate_ns using host={self.ns_host}, port={self.ns_port}")

            self.ns = locate_ns(host=self.ns_host, port=self.ns_port)
            self.ns._pyroBind()
            self.ns.ping()
            assert self.ns._pyroUri.object == "Pyro.NameServer"
            print(f"OK: {self.ns._pyroUri}")
        finally:
            try:
                self.ns._pyroRelease()
            except Exception:
                print("Error releasing ns")

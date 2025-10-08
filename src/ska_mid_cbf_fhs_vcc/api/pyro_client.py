import os, sys
from Pyro5.api import locate_ns, Proxy
from Pyro5 import errors

class PyroClient():

    def __init__(self):
        self.NS_HOST = os.environ["NS_HOST"]
        self.NS_PORT = int(os.getenv("NS_PORT", "9090"))

    def ping(self):
        try:
            print(f"...locate_ns using host={self.NS_HOST}, port={self.NS_PORT}")

            self.ns = locate_ns(host=self.NS_HOST, port=self.NS_PORT)
            self.ns._pyroBind()
            self.ns.ping()
            assert self.ns._pyroUri.object == "Pyro.NameServer"
            print(f"OK: {self.ns._pyroUri}")
        finally:
            try:
                self.ns._pyroRelease()
            except Exception:
                print("Error releasing ns")

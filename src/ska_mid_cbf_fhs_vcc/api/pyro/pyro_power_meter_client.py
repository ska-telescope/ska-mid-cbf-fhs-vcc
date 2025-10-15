from ska_mid_cbf_fhs_vcc.api.pyro.pyro_driver import PyroDriver


class PyroPowerMeterClient(PyroDriver):
    def __init__(self, logger, driver_name):
        super().__init__(logger, driver_name)

    def configure(self):
        pass

    def status(self, clear: bool = False):
        pass

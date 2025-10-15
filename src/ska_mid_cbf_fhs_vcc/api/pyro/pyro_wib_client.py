from ska_mid_cbf_fhs_vcc.api.pyro.pyro_driver import PyroDriver


class PyroWibClient(PyroDriver):
    def __init__(self, logger, driver_name):
        super().__init__(logger, driver_name)

    def configure(self):
        try:
            config_t = dict(
                expected_sample_rate=3960000000,
                noise_diode_transition_holdoff_seconds=0.0,
                expected_dish_band=1,
            )
            print(config_t)

            super().configure(config_t)

            self.logger.info("[Success] WIB was configured successfully!")
        except Exception as ex:
            self.logger.error(f"Unable to configure the wib, {repr(ex)}")

    def status(self, clear: bool = False):
        self.logger.info(f"::::: {self.driver_name} Driver Status :::::")
        self.logger.info(f"{super().status(clear)}")

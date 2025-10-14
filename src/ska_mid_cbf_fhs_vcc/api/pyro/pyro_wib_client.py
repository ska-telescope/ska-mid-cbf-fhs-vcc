from ska_mid_cbf_fhs_vcc.api.pyro.pyro_driver import PyroDriver


class PyroWibClient(PyroDriver):
    def __init__(self, logger, driver_name):
        super(logger, driver_name)

    def configure(self, config_file):
        try:
            test_config: dict = self.get_config_file(config_file)

            band = test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("band", 1)
            sample_rate = test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("sample_rate", 3.96e9)
            transition_holdoff = (
                test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("noise_diode", {}).setdefault("transition_holdoff", 0.0)
            )

            config_t = dict(
                expected_sample_rate=int(sample_rate),
                noise_diode_transition_holdoff_seconds=float(transition_holdoff),
                expected_dish_band=int(band),
            )
            print(config_t)

            super().configure(config_t)

            self.logger.info("[Success] WIB was configured successfully!")
        except Exception as ex:
            self.logger.error(f"Unable to configure the wib, {repr(ex)}")

    def status(self, clear: bool = False):
        self.logger.info(f"::::: {self.driver_name} Driver Status :::::")
        self.logger.info(f"{self.status(clear)}")

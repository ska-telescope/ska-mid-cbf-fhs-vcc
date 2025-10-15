import parse

from ska_mid_cbf_fhs_vcc.api.pyro.pyro_driver import PyroDriver


class PyroWibClient(PyroDriver):
    def __init__(self, logger, driver_name):
        super().__init__(logger, driver_name)
        self.location, self.local_location = self.get_location(driver_name)

    def configure(self):
        try:
            test_config: dict = self.get_config_file()

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
        self.logger.info(f"{super().status(clear)}")

    def get_location(self, name: str):
        forms = {
            "ska-vcc-vcc": "{card}_receptor{lane}_",
            "ska-base": "{card}_",
        }
        for _category, form in forms.items():
            form_rem = form + "{}_driver"
            match = parse.search(form_rem, name, evaluate_result=False)
            if match:
                break
        else:
            raise ValueError(f"Name '{name}' doesn't match any of the known location strings: {forms}")
        result = match.evaluate_result()
        form_parts = result.named.values()
        local_name = result.fixed[0]
        return "-".join(form_parts), local_name

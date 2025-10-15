from ska_mid_cbf_fhs_vcc.api.pyro.pyro_driver import PyroDriver


class PyroChannelizerClient(PyroDriver):
    INPUT_FRAME_SIZE = 18
    CHANNELS_OUT = 10
    BANDS = [1, 2, 3]

    def __init__(self, logger, driver_name):
        super().__init__(logger, driver_name)
        self.location, self.local_location = self.get_location(driver_name)

    def configure(self):
        try:
            test_config: dict = self.get_config_file()

            self.band = test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("band", 1)
            if self.band not in self.BANDS:
                # nothing to do.
                return
            config_t = {}
            input_sample_rate = test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("sample_rate", 3.96e9)
            self.logger.info(
                f"Setting the VCC sample_rate to {input_sample_rate} samples per second at the outputs. Frequency slice bandwidth will be {input_sample_rate // 2 // self.CHANNELS_OUT:e} Hz"
            )
            config_t["sample_rate"] = int(input_sample_rate)

            first_channel = 0
            last_channel = self.CHANNELS_OUT
            if self.local_location.replace("driver", "").endswith("b"):
                first_channel = 15

            channels_cfg = test_config.setdefault("vcc", {}).setdefault(self.location, {}).setdefault("coarse_channels", {})
            if len(channels_cfg) == 0:
                last_channel = self.CHANNELS_OUT * 2 if self.band == 5 else last_channel
                # add all the channels - for the sake of populating an empty test_config that can then be edited down.
                for chan in range(first_channel, last_channel):
                    channels_cfg.setdefault(chan, {})

            for chan in range(first_channel, last_channel):
                chan_cfg = channels_cfg.get(chan, {})  # get but don't set a default.
                for pol in ("X", "Y"):
                    default_gain = test_config.setdefault("vcc", {}).setdefault(self.location, {}).setdefault("default_gain", {}).setdefault(pol, 1.0)
                    gain = chan_cfg.setdefault("gain", {}).setdefault(pol, default_gain)
                    # Call configure for each pol and channel separately.
                    config_t["pol"] = self.pol_to_int(pol)
                    config_t["channel"] = int(chan - first_channel)
                    config_t["gain"] = float(gain)
                    super().configure(config_t)

            self.logger.info("[Success] VCC_20 Channelizer was configured successfully!")

        except Exception as ex:
            self.logger.error(f"Unable to configure the vcc_20 channelizer, {repr(ex)}")

    def status(self, clear: bool = False):
        self.logger.info(f"::::: {self.driver_name} Driver Status :::::")
        self.logger.info(f"{super().status(clear)}")

    def pol_to_int(self, pol) -> int:
        """Convert a polarisation identifier such as 'X'|'Y' to an integer 0|1"""
        if pol in (0, "X", "x", "H", "h"):
            return 0
        elif pol in (1, "Y", "y", "V", "v"):
            return 1
        else:
            raise ValueError(f"Got '{pol}' which is not a vaild polarisation designator.")

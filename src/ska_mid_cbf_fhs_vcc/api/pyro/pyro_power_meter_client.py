from ska_mid_cbf_fhs_vcc.api.pyro.pyro_driver import PyroDriver


class PyroPowerMeterClient(PyroDriver):
    FLAG = {
        "ignore": 0,
        "use": 1,
        "saturate": 2,
    }

    def __init__(self, logger, driver_name):
        super().__init__(logger, driver_name)
        # work out where in the receptor lane this wpm is.
        self.location, self.local_location = self.get_location(driver_name)
        self.my_loc_split = self.local_location.split('_')
        self.my_loc = self.my_loc_split[2] # first string before the next underscore.
        self.time_resolution = 1.0
        self.enabled = False
        self.coarse_channel = "--"

    def configure(self):
        try:
            test_config: dict = self.get_config_file()
            self.logger.info(f"::: MY_LOC={self.my_loc}; LOCAL_LOCATION={self.local_location}:::")
            band = test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("band", 1)
            if "band" in self.my_loc:
                # wideband power meter.
                if str(band) not in self.my_loc:
                    # this power meter is not used for this band.
                    return
                power_meter_cfg = test_config.setdefault("vcc", {}).setdefault(self.location, {}).setdefault("power_meter", {}).setdefault(self.my_loc, {})
            else:
                # frequency slice power meter. Work out what lane.
                # eg. self.my_loc = "fs22"
                lane = int(self.my_loc.removeprefix("fs"))
                self.coarse_channel = self.lane_to_coarse_channel_from_test_config(test_config, self.location, lane)
                coarse_channel_config = test_config.setdefault("vcc", {}).setdefault(self.location, {}).setdefault("coarse_channels", {})
                if self.coarse_channel not in coarse_channel_config:
                    # coarse channel not configured. Ignore this power meter.
                    return
                power_meter_cfg = coarse_channel_config.get(self.coarse_channel, {}).setdefault("power_meter", {})
                # update the time_resolution so that status can convert the sample rate correctly.
                sample_rate = test_config.setdefault("dish", {}).setdefault(self.location, {}).setdefault("sample_rate", 3.96e9)
                if band <= 3:
                    self.time_resolution = sample_rate // 18
                else:
                    self.time_resolution = sample_rate // 27

            # Either got a power_meter_cfg, or exited early.
            ave_time = power_meter_cfg.setdefault("averaging_time", 0.1)
            flagging = power_meter_cfg.setdefault("flag_behaviour", "ignore")

            config_t = dict(averaging_time=float(ave_time), flagging=int(self.FLAG.get(flagging)))

            super().configure(config_t)
            self.enabled = True

            self.logger.info("[Success] WIB Power Meter was configured successfully!")

        except Exception as ex:
            self.logger.error(f"Unable to configure the band123 power meter, {repr(ex)}\n{ex.with_traceback()}")

    def status(self, clear: bool = False):
        if not self.enabled:
            return
        self.logger.info(f"::::: {self.driver_name} Driver Status :::::")
        self.logger.info(f"{super().status(clear)}")

    def lane_to_coarse_channel_from_test_config(self, test_config, location, lane):
        band = test_config.setdefault("dish", {}).setdefault(location, {}).setdefault("band", 1)
        ch_a, ch_b = self.start_coarse_channels(test_config, location)
        return self.lane_to_coarse_channel(band, int(lane), ch_a, ch_b)

    def start_coarse_channels(self, test_config, location):
        coarse_ch_subband1 = coarse_ch_subband2 = 0
        coarse_channels = test_config.setdefault("vcc", {}).setdefault(location, {}).setdefault("coarse_channels").keys()
        band = test_config.setdefault("dish", {}).setdefault(location, {}).setdefault("band", 1)
        if band >= 4:
            coarse_ch_subband1 = min(2, max(0, min(coarse_channels)))
        if band >= 5:
            coarse_ch_subband2 = min(2, max(0, max(coarse_channels) - 27))
        return coarse_ch_subband1, coarse_ch_subband2

    def lane_to_coarse_channel(self, band: int, lane: int, first_coarse_channel_a: int = 0, first_coarse_channel_b: int = 0) -> int | None:
        if not 0 <= lane <= 25:
            raise ValueError("lane must be between 0 and 25 inclusive, got {lane}.")
        if band == 0:
            raise Exception("freq_slice_selection is not configured.")
        if band in (
            1,
            2,
            3,
        ):
            if 8 <= lane <= 17:
                return lane - 8
            return None
        if band == 4:
            if 2 <= lane <= 12:
                return lane
            if first_coarse_channel_a == 0 and lane < 2:
                return lane
            if first_coarse_channel_a == 1 and lane == 0:
                return 13
            if first_coarse_channel_a == 1 and lane == 1:
                return 1
            if first_coarse_channel_a == 2 and lane == 0:
                return 13
            if first_coarse_channel_a == 2 and lane == 1:
                return 14
            return None
        if band == 5:
            # Subband a/0, channels 0 to 14 inclusive (same as band 4).
            if 2 <= lane <= 12:
                return lane
            if first_coarse_channel_a == 0 and lane < 2:
                return lane
            if first_coarse_channel_a == 1 and lane == 0:
                return 13
            if first_coarse_channel_a == 1 and lane == 1:
                return 1
            if first_coarse_channel_a == 2 and lane == 0:
                return 13
            if first_coarse_channel_a == 2 and lane == 1:
                return 14
            if lane < 13:
                return None
            # Subband b/1, channels 15 to 29 inclusive.
            if 13 <= lane <= 23:
                return lane + 4
            if first_coarse_channel_b == 0 and 24 <= lane <= 25:
                return lane - 24 + 15
            if first_coarse_channel_b == 1 and lane == 24:
                return 28
            if first_coarse_channel_b == 1 and lane == 25:
                return 16
            if first_coarse_channel_b == 2 and lane == 24:
                return 28
            if first_coarse_channel_b == 2 and lane == 25:
                return 29
            return None
        raise Exception(f"Bug. Should have found a channel to match lane {lane} or hit an earlier ValueError")

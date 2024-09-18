import logging

from ska_control_model import ResultCode, SimulationMode

from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import (
    FhsBaseApiInterface,
)
from ska_mid_cbf_fhs_vcc.api.emulator.b123_vcc_osppfb_channeliser_emulator_api import (
    B123VccOsppfbChanneliserEmulatorApi,
)
from ska_mid_cbf_fhs_vcc.api.simulator.b123_vcc_osppfb_channeliser_simulator import (
    B123VccOsppfbChanneliserSimulator,
)


class B123VccOsppfbChanneliserApi(FhsBaseApiInterface):
    def __init__(
        self,
        device_id: str,
        simulation_mode: SimulationMode,
        emulation_mode: bool,
        logger: logging.Logger,
        config_location: str = None,
    ) -> None:
        self.logger = logger

        self.logger.info(f"Emulation mode={emulation_mode} : simulation mode={simulation_mode}")

        if simulation_mode == SimulationMode.TRUE:
            self.logger.info("instantiating simualator api")
            self._api = B123VccOsppfbChanneliserSimulator(device_id, logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            self.logger.info("instantiating emulator api")
            self._api = B123VccOsppfbChanneliserEmulatorApi(
                device_id=device_id, config_location=config_location, logger=logger
            )
        else:
            # TODO todo add FW API here no
            raise NotImplementedError("FW Api not implemented")

    def recover(self) -> tuple[ResultCode, str]:
        return self._api.recover()

    def configure(self, config: str) -> tuple[ResultCode, str]:
        return self._api.configure(config)

    def start(self) -> None:
        raise NotImplementedError("Vcc start command not implemented")

    def stop(self, force: bool = False) -> None:
        raise NotImplementedError("Vcc stop command not implemented")

    def deconfigure(self, config) -> tuple[ResultCode, str]:
        return self._api.deconfigure(config)

    def status(self, status, clear: bool = False) -> tuple[ResultCode, str]:
        return self._api.status(status, clear)

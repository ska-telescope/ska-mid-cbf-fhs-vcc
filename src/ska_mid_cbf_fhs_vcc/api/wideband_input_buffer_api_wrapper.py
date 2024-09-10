import logging

from ska_control_model import ResultCode, SimulationMode

from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.api.emulator.wib_emulator_api import WibEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.wideband_input_buffer_simulator import WidebandInputBufferSimulator


class WidebandInputBufferApi(FhsBaseApiInterface):
    def __init__(
        self,
        device_id: str,
        config_location: str,
        simulation_mode: SimulationMode,
        emulation_mode: bool,
        logger: logging.Logger,
    ) -> None:
        self.logger = logger
        if simulation_mode == SimulationMode.TRUE:
            self.logger.info("instantiating simualator api")
            self._api = WidebandInputBufferSimulator(device_id=device_id, logger=logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            self.logger.info("instantiating emulator api")
            self._api = WibEmulatorApi(device_id=device_id, config_location=config_location, logger=logger)
        else:
            # TODO todo add FW API here no
            raise NotImplementedError("FW Api not implemented")

    def recover(self) -> tuple[ResultCode, str]:
        return self._api.recover()

    def configure(self, config) -> tuple[ResultCode, str]:
        return self._api.configure(config)

    def start(self) -> tuple[ResultCode, str]:
        return self._api.start()

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        return self._api.stop(force)

    def deconfigure(self, config) -> tuple[ResultCode, str]:
        raise NotImplementedError("Wideband Input Buffer Deconfigure command not implemented")

    def status(self, status, clear: bool = False) -> tuple[ResultCode, str]:
        return self._api.status(status, clear)

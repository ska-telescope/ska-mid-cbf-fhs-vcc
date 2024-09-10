import logging

from ska_control_model import ResultCode, SimulationMode

from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.api.simulator.packet_validation_simulator import PacketValidationControllerSimulator


class PacketValidationApi(FhsBaseApiInterface):
    def __init__(
        self,
        device_id: str,
        simulation_mode: SimulationMode,
        emulation_mode: bool,
        logger: logging.Logger,
    ) -> None:
        self.logger = logger

        self.logger.info(f"Emulation mode={emulation_mode} : simulation mode={simulation_mode}")

        if simulation_mode == SimulationMode.TRUE:
            self.logger.info("instantiating simualator api")
            self._api = PacketValidationControllerSimulator(device_id, logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            self.logger.info("instantiating emulator api")
            # TODO add emulator api
            raise NotImplementedError("Emulator Api not implemented")
        else:
            # TODO todo add FW API here no
            raise NotImplementedError("FW Api not implemented")

    def recover(self) -> tuple[ResultCode, str]:
        return self._api.recover()

    def configure(self, config) -> None:
        raise NotImplementedError("Packet Validation Configure command not implemented")

    def start(self) -> tuple[ResultCode, str]:
        return self._api.start()

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        return self._api.stop(force)

    def deconfigure(self, config) -> None:
        raise NotImplementedError("Packet Validation Deconfigure command not implemented")

    def status(self, status, clear: bool = False) -> tuple[ResultCode, str]:
        return self._api.status(status, clear)

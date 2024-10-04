from ska_mid_cbf_fhs_vcc.api.emulator.base_emulator_api import BaseEmulatorApi


class PacketValidationEmulatorApi(BaseEmulatorApi):
    def configure(self, config: dict) -> None:
        raise NotImplementedError("Configure command not implemented for Packet Validation devices")

    def deconfigure(self, config: dict) -> None:
        raise NotImplementedError("Deconfigure command not implemented for Packet Validation devices")

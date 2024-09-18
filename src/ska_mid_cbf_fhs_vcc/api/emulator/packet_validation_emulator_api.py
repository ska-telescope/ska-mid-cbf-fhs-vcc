from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class PacketValidationEmulatorApi(FhsBaseApiInterface):
    # TODO have a way to dynamically grab the emulator host / port values from the emulator config file
    def __init__(self, instance_name: str, hostName: str = "localhost", port: str = "5001") -> None:
        self._instance_name = instance_name
        self.base_url = f"{hostName}:{port}/{instance_name}"

    def configure(self, config: str) -> None:
        raise NotImplementedError("Configure command not implemented for Packet Validation devices")

    def deconfigure(self, config: str) -> None:
        raise NotImplementedError(
            "Deconfigure command not implemented for Packet Validation devices"
        )

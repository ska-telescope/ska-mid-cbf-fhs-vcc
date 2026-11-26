from typing import Any

import requests
from ska_mid_cbf_fhs_common import AdminOnline


class VccAdminOnline(AdminOnline):
    def __init__(
        self,
        *args: Any,
        emulator_id: str,
        emulator_port: str,
        emulation_mode: bool,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self.emulator_state_request = f"{emulator_id}:{emulator_port}/state"
        self.emulation_mode = emulation_mode

        self.logger.debug(f"\temulation_mode: {self.emulation_mode}")
        self.logger.debug(f"emulator_state_request: {self.emulator_state_request}")

    def check_controller_specific(self) -> bool:
        if self.emulation_mode:
            return self.check_emulator_ready()
        return True

    def check_emulator_ready(self) -> bool:
        self.logger.info("Waiting for emulators to be ready...")
        try:
            self.logger.info(f"Sending request {self.emulator_state_request} to emulator")
            resp = requests.get(f"http://{self.emulator_state_request}", timeout=600)
            if resp.status_code >= 300:
                self.logger.error("Unable to get response from the emulator...")
                return False
            return True
        except requests.exceptions.Timeout:
            self.logger.error(f"Unable to connect to the emulators using the following address {self.emulator_state_request} within the given time...")
        return False

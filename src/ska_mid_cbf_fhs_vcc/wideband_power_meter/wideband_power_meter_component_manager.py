from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Any

from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.wideband_power_meter_simulator import WidebandPowerMeterSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


@dataclass_json
@dataclass
class WidebandPowerMeterConfig:
    averaging_time: float  # Averaging interval in seconds
    sample_rate: float  # Sample rate in sampes per second


##
# status class that will be populated by the APIs and returned to provide the status of Wideband Power Meter
##
@dataclass
class WidebandPowerMeterStatus:
    timestamp: float  # Timestamp in seconds of the last sample in the averaging interval
    avg_power_polX: float  # Average signal power
    avg_power_polY: float  # Average signal power
    avg_power_polX_noise_diode_on: float  # Average signal power
    avg_power_polY_noise_diode_on: float  # Average signal power
    avg_power_polX_noise_diode_off: float  # Average signal power
    abg_power_polY_noise_diode_off: float  # Average signal power


class WidebandPowerMeterComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: WidebandPowerMeterComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=WidebandPowerMeterSimulator,
            **kwargs,
        )

    # ------------------
    # Public Commands
    # ------------------

    def configure(self: WidebandPowerMeterComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WPM Configuring..")

            wpmJsonConfig: WidebandPowerMeterConfig = WidebandPowerMeterConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {wpmJsonConfig.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            self.logger.info(f"WPM JSON CONFIG: {wpmJsonConfig.to_json()}")

            result = super().configure(wpmJsonConfig.to_dict())

            if result[0] != ResultCode.OK:
                self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            errorMsg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{errorMsg}: {vex}")
            result = ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            result = ResultCode.FAILED, errorMsg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandPowerMeterComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()

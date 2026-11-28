from __future__ import annotations

from typing import cast, overload

from mpmath import mp, mpf
from ska_mid_cbf_fhs_common import FHS_MPMATH_PRECISION, FloatLike, MPFloat, power_linear_to_db

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAveragedPowerMeasurement, VCCXYAveragedPowerMeasurements, VCCXYPowerMeasurements

_MPF_ZERO = MPFloat("0.0")


class VCCXYPowerAccumulator:
    """Helper class for accumulating and averaging dual-polarization power measurements."""

    @overload
    def __init__(
        self,
        x_total: FloatLike,
        x_on: FloatLike,
        x_off: FloatLike,
        y_total: FloatLike,
        y_on: FloatLike,
        y_off: FloatLike,
        weight: FloatLike,
    ): ...

    @overload
    def __init__(self): ...

    def __init__(
        self,
        x_total: FloatLike = _MPF_ZERO,
        x_on: FloatLike = _MPF_ZERO,
        x_off: FloatLike = _MPF_ZERO,
        y_total: FloatLike = _MPF_ZERO,
        y_on: FloatLike = _MPF_ZERO,
        y_off: FloatLike = _MPF_ZERO,
        weight: FloatLike = _MPF_ZERO,
    ):
        mp.dps = FHS_MPMATH_PRECISION
        self.x_total = cast(mpf, mp.fmul(x_total, weight))
        self.x_on = cast(mpf, mp.fmul(x_on, weight))
        self.x_off = cast(mpf, mp.fmul(x_off, weight))
        self.y_total = cast(mpf, mp.fmul(y_total, weight))
        self.y_on = cast(mpf, mp.fmul(y_on, weight))
        self.y_off = cast(mpf, mp.fmul(y_off, weight))
        self.weight = weight

    def accumulate(
        self,
        x_total: FloatLike,
        x_on: FloatLike,
        x_off: FloatLike,
        y_total: FloatLike,
        y_on: FloatLike,
        y_off: FloatLike,
        weight: FloatLike,
    ) -> None:
        """Add the provided power measurements to the stored accumulations.

        Args:
            x_total (:obj:`FloatLike`): Measured total power for the X polarization.
            x_on (:obj:`FloatLike`): Measured noise-diode-ON power for the X polarization.
            x_off (:obj:`FloatLike`): Measured noise-diode-OFF power for the X polarization.
            y_total (:obj:`FloatLike`): Measured total power for the Y polarization.
            y_on (:obj:`FloatLike`): Measured noise-diode-ON power for the Y polarization.
            y_off (:obj:`FloatLike`): Measured noise-diode-OFF power for the Y polarization.
            weight (:obj:`FloatLike`): Weight to apply to this set of measurements.
        """
        mp.dps = FHS_MPMATH_PRECISION
        self.x_total = cast(mpf, mp.fadd(self.x_total, mp.fmul(x_total, weight)))
        self.x_on = cast(mpf, mp.fadd(self.x_on, mp.fmul(x_on, weight)))
        self.x_off = cast(mpf, mp.fadd(self.x_off, mp.fmul(x_off, weight)))
        self.y_total = cast(mpf, mp.fadd(self.y_total, mp.fmul(y_total, weight)))
        self.y_on = cast(mpf, mp.fadd(self.y_on, mp.fmul(y_on, weight)))
        self.y_off = cast(mpf, mp.fadd(self.y_off, mp.fmul(y_off, weight)))
        self.weight = cast(mpf, mp.fadd(self.weight, weight))

    def accumulate_from_measurements(self, power_measurements: VCCXYPowerMeasurements) -> None:
        """Add the power measurements from the provided `VCCXYPowerMeasurements` class to the stored accumulations.

        Args:
            power_measurements (:obj:`VCCXYPowerMeasurements`): The power measurements to accumulate.
        """
        self.accumulate(
            x_total=power_measurements.x.total,
            x_on=power_measurements.x.nd_on,
            x_off=power_measurements.x.nd_off,
            y_total=power_measurements.y.total,
            y_on=power_measurements.y.nd_on,
            y_off=power_measurements.y.nd_off,
            weight=power_measurements.weight,
        )

    def accumulate_from_other_accumulator(self, other: VCCXYPowerAccumulator) -> None:
        """Add the accumulations from the other provided accumulator to the stored accumulations.

        Args:
            power_measurements (:obj:`VCCXYPowerMeasurements`): The power measurements to accumulate.
        """
        self.x_total = cast(mpf, mp.fadd(self.x_total, other.x_total))
        self.x_on = cast(mpf, mp.fadd(self.x_on, other.x_on))
        self.x_off = cast(mpf, mp.fadd(self.x_off, other.x_off))
        self.y_total = cast(mpf, mp.fadd(self.y_total, other.y_total))
        self.y_on = cast(mpf, mp.fadd(self.y_on, other.y_on))
        self.y_off = cast(mpf, mp.fadd(self.y_off, other.y_off))
        self.weight = cast(mpf, mp.fadd(self.weight, other.weight))

    def average_and_reset(self, convert_to_db: bool = False) -> VCCXYAveragedPowerMeasurements:
        """Compute the average power measurements from the currently stored accumulations and total weight,
        then reset all accumulated values to 0 and return the computed average measurements.

        Args:
            convert_to_db (:obj:`bool`, optional): Whether to convert the final averaged values to dB. Default is False.

        Returns:
            :obj:`VCCXYAveragedPowerMeasurements`: The averaged power measurements.
        """
        resp = VCCXYAveragedPowerMeasurements(
            x=VCCAveragedPowerMeasurement(
                total=self._get_weighted_average(self.x_total, convert_to_db),
                nd_on=self._get_weighted_average(self.x_on, convert_to_db),
                nd_off=self._get_weighted_average(self.x_off, convert_to_db),
            ),
            y=VCCAveragedPowerMeasurement(
                total=self._get_weighted_average(self.y_total, convert_to_db),
                nd_on=self._get_weighted_average(self.y_on, convert_to_db),
                nd_off=self._get_weighted_average(self.y_off, convert_to_db),
            ),
        )
        self.reset()
        return resp

    def reset(self) -> None:
        """Reset all accumulated values to 0."""
        self.x_total = MPFloat("0.0")
        self.x_on = MPFloat("0.0")
        self.x_off = MPFloat("0.0")
        self.y_total = MPFloat("0.0")
        self.y_on = MPFloat("0.0")
        self.y_off = MPFloat("0.0")
        self.weight = MPFloat("0.0")

    def _get_weighted_average(self, combined_power: FloatLike, convert_to_db: bool = False) -> FloatLike:
        """Compute and return the weighted average of a single power measurement component."""
        mp.dps = FHS_MPMATH_PRECISION
        avg_power = cast(mpf, mp.fdiv(combined_power, self.weight))
        if convert_to_db:
            return power_linear_to_db(avg_power)
        return avg_power

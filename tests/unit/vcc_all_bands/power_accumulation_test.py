import pytest
from ska_mid_cbf_fhs_common import MPFloat

from ska_mid_cbf_fhs_vcc.helpers.power_measurement import VCCXYPowerAccumulator
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCPowerMeasurement, VCCXYPowerMeasurements


class TestVCCPowerAccumulation:
    def test_accumulator_init_empty(self):
        _ = VCCXYPowerAccumulator()

    def test_accumulator_init_nonempty(self):
        _ = VCCXYPowerAccumulator(
            x_total=1.0,
            x_on=1.0,
            x_off=1.0,
            y_total=1.0,
            y_on=1.0,
            y_off=1.0,
            weight=1.0,
        )

    def test_accumulate_from_values(self):
        acc = VCCXYPowerAccumulator(
            x_total=1.0,
            x_on=1.0,
            x_off=1.0,
            y_total=1.0,
            y_on=1.0,
            y_off=1.0,
            weight=1.0,
        )
        acc.accumulate(
            x_total=0.5,
            x_on=0.5,
            x_off=0.5,
            y_total=0.6,
            y_on=0.6,
            y_off=0.6,
            weight=0.5,
        )
        assert acc.x_total == pytest.approx(1.25)
        assert acc.y_on == pytest.approx(1.3)
        assert acc.weight == pytest.approx(1.5)

    def test_accumulate_from_measurements(self):
        acc = VCCXYPowerAccumulator(
            x_total=1.0,
            x_on=1.0,
            x_off=1.0,
            y_total=1.0,
            y_on=1.0,
            y_off=1.0,
            weight=1.0,
        )
        measurements = VCCXYPowerMeasurements(
            x=VCCPowerMeasurement(total=0.5, nd_on=0.5, nd_off=0.5),
            y=VCCPowerMeasurement(total=0.6, nd_on=0.6, nd_off=0.6),
            weight=0.5,
        )
        acc.accumulate_from_measurements(measurements)
        assert acc.x_total == pytest.approx(1.25)
        assert acc.y_on == pytest.approx(1.3)
        assert acc.weight == pytest.approx(1.5)

    def test_accumulate_from_other(self):
        acc1 = VCCXYPowerAccumulator(
            x_total=1.0,
            x_on=1.0,
            x_off=1.0,
            y_total=1.0,
            y_on=1.0,
            y_off=1.0,
            weight=1.0,
        )
        acc2 = VCCXYPowerAccumulator(
            x_total=0.5,
            x_on=0.5,
            x_off=0.5,
            y_total=0.6,
            y_on=0.6,
            y_off=0.6,
            weight=0.5,
        )
        acc1.accumulate_from_other_accumulator(acc2)
        assert acc1.x_total == pytest.approx(1.25)
        assert acc1.y_on == pytest.approx(1.3)
        assert acc1.weight == pytest.approx(1.5)

    def test_average_no_convert(self):
        acc = VCCXYPowerAccumulator(
            x_total=1.0,
            x_on=1.0,
            x_off=1.0,
            y_total=1.0,
            y_on=1.0,
            y_off=1.0,
            weight=1.0,
        )
        acc.accumulate(
            x_total=0.5,
            x_on=0.5,
            x_off=0.5,
            y_total=0.6,
            y_on=0.6,
            y_off=0.6,
            weight=0.5,
        )
        assert acc.x_total == pytest.approx(1.25)
        assert acc.y_on == pytest.approx(1.3)
        assert acc.weight == pytest.approx(1.5)

        averaged = acc.average_and_reset(convert_to_db=False)

        assert acc.x_total == pytest.approx(0.0)
        assert acc.y_on == pytest.approx(0.0)
        assert acc.weight == pytest.approx(0.0)

        MPFloat.assert_almosteq(MPFloat(averaged.x.total), MPFloat("0.8333333333333333333333333333"))
        MPFloat.assert_almosteq(MPFloat(averaged.y.total), MPFloat("0.8666666666666666666666666666"))

    def test_average_convert_db(self):
        acc = VCCXYPowerAccumulator(
            x_total=1.0,
            x_on=1.0,
            x_off=1.0,
            y_total=1.0,
            y_on=1.0,
            y_off=1.0,
            weight=1.0,
        )
        acc.accumulate(
            x_total=0.5,
            x_on=0.5,
            x_off=0.5,
            y_total=0.6,
            y_on=0.6,
            y_off=0.6,
            weight=0.5,
        )
        assert acc.x_total == pytest.approx(1.25)
        assert acc.y_on == pytest.approx(1.3)
        assert acc.weight == pytest.approx(1.5)

        averaged = acc.average_and_reset(convert_to_db=True)

        assert acc.x_total == pytest.approx(0.0)
        assert acc.y_on == pytest.approx(0.0)
        assert acc.weight == pytest.approx(0.0)

        MPFloat.assert_almosteq(MPFloat(averaged.x.total), MPFloat("-0.7918"), rel_tolerance=None, abs_tolerance=1e-4)
        MPFloat.assert_almosteq(MPFloat(averaged.y.total), MPFloat("-0.6214"), rel_tolerance=None, abs_tolerance=1e-4)

        averaged.apply_gain(MPFloat("-0.1"), MPFloat("-0.6"))

        MPFloat.assert_almosteq(MPFloat(averaged.x.total_backed_out), MPFloat("-0.6918"), rel_tolerance=None, abs_tolerance=1e-4)
        MPFloat.assert_almosteq(MPFloat(averaged.y.total_backed_out), MPFloat("-0.0214"), rel_tolerance=None, abs_tolerance=1e-4)
        MPFloat.assert_almosteq(MPFloat(averaged.x.headroom), MPFloat("0.7918"), rel_tolerance=None, abs_tolerance=1e-4)

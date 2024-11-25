from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.tvm.future_value import future_value, fv_of_uneven_cashflows, fv_annuity_due
from finpy.tvm.future_value import fv_with_continuous_compounding, fv_uneven_with_continuous_compounding
from finpy.tvm.future_value import fv_continuous_with_pmt, fv_single_amount, fv_continuous_single
from finpy.tvm.future_value import fv_annuity_immediate, fv_of_growing_annuity
from tests._helpers import approx_decimal


class TestFutureValue:
    def test_basic(self):
        result = future_value(0.05, 10, 0, 1000)
        assert result == pytest.approx(Decimal("1628.89"), abs=0.01)

    def test_with_payments(self):
        result = future_value(0.05, 10, 100, 0)
        assert result == pytest.approx(Decimal("1257.79"), abs=0.01)

    def test_zero_rate(self):
        result = future_value(0, 5, 100, 1000)
        assert result == Decimal("1500")

    def test_begin_mode(self):
        result = future_value(0.05, 10, 100, 1000, when="begin")
        assert result > future_value(0.05, 10, 100, 1000)

    def test_zero_pv_zero_pmt(self):
        result = future_value(0.05, 10, 0, 0)
        assert result == Decimal("0")

    def test_negative_rate(self):
        result = future_value(-0.05, 5, 100, 1000)
        assert result == Decimal("1000") * (Decimal("0.95") ** 5) + Decimal("100") * ((Decimal("0.95") ** 5 - Decimal(1)) / Decimal("-0.05"))
        assert result < Decimal("1500")

    def test_with_ndigits(self):
        result = future_value(0.05, 10, 100, 1000, ndigits=2)
        assert result == Decimal("2886.68")

    def test_single_period(self):
        result = future_value(0.10, 1, 0, 100)
        assert result == Decimal("110")

    def test_large_nper(self):
        result = future_value(0.01, 100, 0, 100)
        assert result == pytest.approx(Decimal("270.48"), abs=0.01)


class TestFvOfUnevenCashflows:
    def test_basic(self):
        result = fv_of_uneven_cashflows(0.10, [100, 200, 300])
        assert result == pytest.approx(Decimal("641.00"), abs=0.01)

    def test_single_flow(self):
        result = fv_of_uneven_cashflows(0.10, [100])
        assert result == Decimal("100")

    def test_empty_list(self):
        result = fv_of_uneven_cashflows(0.10, [])
        assert result == Decimal("0")

    def test_mixed_signs(self):
        result = fv_of_uneven_cashflows(0.10, [-100, 200, -300])
        assert result == pytest.approx(Decimal("-201.00"), abs=0.01)

    def test_zero_rate(self):
        result = fv_of_uneven_cashflows(0, [100, 200, 300])
        assert result == Decimal("600")

    def test_with_ndigits(self):
        result = fv_of_uneven_cashflows(0.10, [100, 200, 300], ndigits=2)
        assert result == Decimal("641.00")


class TestFvAnnuityDue:
    def test_basic(self):
        result = fv_annuity_due(0.05, 10, 100)
        assert result == pytest.approx(Decimal("1320.68"), abs=0.01)

    def test_zero_rate(self):
        result = fv_annuity_due(0, 10, 100)
        assert result == Decimal("1000")

    def test_single_period(self):
        result = fv_annuity_due(0.05, 1, 100)
        assert result == Decimal("105")

    def test_zero_pmt(self):
        result = fv_annuity_due(0.05, 10, 0)
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = fv_annuity_due(0.05, 10, 100, ndigits=2)
        assert result == Decimal("1320.68")


class TestFvWithContinuousCompounding:
    def test_basic(self):
        result = fv_with_continuous_compounding(0.05, 10, 1000)
        assert result == pytest.approx(Decimal("1648.72"), abs=0.01)

    def test_zero_rate(self):
        result = fv_with_continuous_compounding(0, 10, 1000)
        assert result == Decimal("1000")

    def test_zero_periods(self):
        result = fv_with_continuous_compounding(0.05, 0, 1000)
        assert result == Decimal("1000")

    def test_negative_rate(self):
        result = fv_with_continuous_compounding(-0.05, 10, 1000)
        assert result < Decimal("1000")

    def test_with_ndigits(self):
        result = fv_with_continuous_compounding(0.05, 10, 1000, ndigits=2)
        assert result == Decimal("1648.72")


class TestFvUnevenWithContinuousCompounding:
    def test_basic(self):
        result = fv_uneven_with_continuous_compounding(0.05, [100, 200, 300])
        assert result == pytest.approx(Decimal("652.60"), abs=0.01)

    def test_single_flow(self):
        result = fv_uneven_with_continuous_compounding(0.05, [100])
        assert result == pytest.approx(Decimal("105.13"), abs=0.01)

    def test_empty_list(self):
        result = fv_uneven_with_continuous_compounding(0.10, [])
        assert result == Decimal("0")

    def test_zero_rate(self):
        result = fv_uneven_with_continuous_compounding(0, [100, 200, 300])
        assert result == Decimal("600")

    def test_with_ndigits(self):
        result = fv_uneven_with_continuous_compounding(0.05, [100, 200, 300], ndigits=2)
        assert result == Decimal("652.60")


class TestFvContinuousWithPmt:
    def test_basic(self):
        result = fv_continuous_with_pmt(0.05, 10, 100)
        assert result == pytest.approx(Decimal("1265.28"), abs=0.01)

    def test_zero_rate(self):
        result = fv_continuous_with_pmt(0, 10, 100)
        assert result == Decimal("1000")

    def test_single_period(self):
        result = fv_continuous_with_pmt(0.05, 1, 100)
        assert result == pytest.approx(Decimal("100.00"), abs=0.01)

    def test_zero_pmt(self):
        result = fv_continuous_with_pmt(0.05, 10, 0)
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = fv_continuous_with_pmt(0.05, 10, 100, ndigits=2)
        assert result == Decimal("1265.28")


class TestFvSingleAmount:
    def test_basic(self):
        result = fv_single_amount(100, 0.05, 10)
        assert result == pytest.approx(Decimal("162.89"), abs=0.01)

    def test_zero_rate(self):
        result = fv_single_amount(100, 0, 10)
        assert result == Decimal("100")

    def test_zero_pv(self):
        result = fv_single_amount(0, 0.05, 10)
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = fv_single_amount(100, 0.05, 10, ndigits=2)
        assert result == Decimal("162.89")


class TestFvContinuousSingle:
    def test_basic(self):
        result = fv_continuous_single(100, 0.05, 10)
        assert result == pytest.approx(Decimal("164.87"), abs=0.01)

    def test_equivalence(self):
        assert fv_continuous_single(100, 0.05, 10) == fv_with_continuous_compounding(0.05, 10, 100)


class TestFvAnnuityImmediate:
    def test_basic(self):
        result = fv_annuity_immediate(0.05, 10, 100)
        assert result == pytest.approx(Decimal("1257.79"), abs=0.01)

    def test_zero_rate(self):
        result = fv_annuity_immediate(0, 10, 100)
        assert result == Decimal("1000")

    def test_single_period(self):
        result = fv_annuity_immediate(0.05, 1, 100)
        assert result == Decimal("100")

    def test_with_ndigits(self):
        result = fv_annuity_immediate(0.05, 10, 100, ndigits=2)
        assert result == Decimal("1257.79")


class TestFvOfGrowingAnnuity:
    def test_basic_end(self):
        result = fv_of_growing_annuity(0.10, 0.03, 5, 100)
        assert result == pytest.approx(Decimal("644.62"), abs=0.01)

    def test_basic_begin(self):
        result = fv_of_growing_annuity(0.10, 0.03, 5, 100, when="begin")
        assert result > fv_of_growing_annuity(0.10, 0.03, 5, 100)

    def test_equal_rate_growth_end(self):
        result = fv_of_growing_annuity(0.05, 0.05, 5, 100)
        assert result == pytest.approx(Decimal("607.75"), abs=0.01)

    def test_equal_rate_growth_begin(self):
        result = fv_of_growing_annuity(0.05, 0.05, 5, 100, when="begin")
        assert result == pytest.approx(Decimal("638.14"), abs=0.01)

    def test_zero_growth(self):
        result = fv_of_growing_annuity(0.10, 0, 5, 100)
        assert result == pytest.approx(Decimal("610.51"), abs=0.01)

    def test_zero_rate(self):
        result = fv_of_growing_annuity(0, 0, 5, 100)
        assert result == Decimal("500")

    def test_single_period(self):
        result = fv_of_growing_annuity(0.10, 0.03, 1, 100)
        assert result == Decimal("100")

    def test_with_ndigits(self):
        result = fv_of_growing_annuity(0.10, 0.03, 5, 100, ndigits=2)
        assert result == Decimal("644.62")


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=1, max_value=30))
def test_fv_annuity_due_greater_than_immediate(rate, nper):
    fv_end = future_value(rate, nper, 100, 0)
    fv_begin = future_value(rate, nper, 100, 0, when="begin")
    assert fv_begin > fv_end


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=1, max_value=20), st.floats(min_value=10, max_value=1000))
def test_future_value_increasing_with_rate(rate, nper, pv):
    fv1 = future_value(rate, nper, 0, pv)
    fv2 = future_value(rate * 2, nper, 0, pv)
    assert fv2 > fv1


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=1, max_value=10))
def test_fv_single_continuous_relationship(rate, nper):
    disc = fv_single_amount(100, rate, nper)
    cont = fv_continuous_single(100, rate, nper)
    assert cont > disc

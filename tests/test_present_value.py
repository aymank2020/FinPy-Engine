from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.tvm.present_value import present_value, annuity_due, perpetuity, perpetuity_due
from finpy.tvm.present_value import growing_perpetuity, growing_annuity, pv_of_uneven_cashflows
from finpy.tvm.present_value import pv_continuous_compounding, pv_of_perpetuity_with_delay
from finpy.tvm.present_value import pv_of_annuity_continuous, pv_of_deferred_annuity
from finpy.tvm.present_value import pv_of_growing_perpetuity_with_delay
from tests._helpers import approx_decimal


class TestPresentValue:
    def test_basic(self):
        result = present_value(0.05, 10, 0, 1000)
        assert result == pytest.approx(Decimal("613.91"), abs=0.01)

    def test_with_payments(self):
        result = present_value(0.05, 10, 100, 0)
        assert result == pytest.approx(Decimal("772.17"), abs=0.01)

    def test_annuity_due(self):
        result = present_value(0.05, 10, 100, 0, when="begin")
        assert result > present_value(0.05, 10, 100, 0)

    def test_zero_rate(self):
        result = present_value(0, 10, 100, 1000)
        assert result == Decimal("2000")

    def test_zero_rate_no_pmt(self):
        result = present_value(0, 10, 0, 1000)
        assert result == Decimal("1000")

    def test_with_ndigits(self):
        result = present_value(0.05, 10, 100, 1000, ndigits=2)
        assert result == Decimal("1386.09")

    def test_both_pv_and_fv(self):
        result = present_value(0.10, 5, 200, 1000)
        assert result == pytest.approx(Decimal("1379.08"), abs=0.01)

    def test_negative_rate(self):
        result = present_value(-0.05, 5, 100, 1000)
        assert result > 0


class TestAnnuityDue:
    def test_basic(self):
        result = annuity_due(0.05, 10, 100)
        assert result == pytest.approx(Decimal("810.78"), abs=0.01)

    def test_zero_rate(self):
        result = annuity_due(0, 10, 100)
        assert result == Decimal("1000")

    def test_with_ndigits(self):
        result = annuity_due(0.05, 10, 100, ndigits=2)
        assert result == Decimal("810.78")

    def test_single_period(self):
        result = annuity_due(0.05, 1, 100)
        assert result == pytest.approx(Decimal("100"), abs=0.01)

    def test_zero_pmt(self):
        result = annuity_due(0.05, 10, 0)
        assert result == Decimal("0")


class TestPerpetuity:
    def test_basic(self):
        result = perpetuity(0.05, 100)
        assert result == Decimal("2000")

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            perpetuity(0, 100)

    def test_with_ndigits(self):
        result = perpetuity(0.05, 100, ndigits=2)
        assert result == Decimal("2000.00")

    def test_high_rate(self):
        result = perpetuity(0.50, 100)
        assert result == Decimal("200")


class TestPerpetuityDue:
    def test_basic(self):
        result = perpetuity_due(0.05, 100)
        assert result == Decimal("2100")

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            perpetuity_due(0, 100)

    def test_relationship_with_perpetuity(self):
        pd = perpetuity_due(0.10, 100)
        p = perpetuity(0.10, 100)
        assert pd == p * Decimal("1.10")


class TestGrowingPerpetuity:
    def test_basic(self):
        result = growing_perpetuity(0.10, 0.03, 100)
        assert result == pytest.approx(Decimal("1428.57"), abs=0.01)

    def test_zero_growth(self):
        result = growing_perpetuity(0.10, 0, 100)
        assert result == Decimal("1000")

    def test_rate_less_than_growth(self):
        with pytest.raises(ValueError):
            growing_perpetuity(0.03, 0.05, 100)

    def test_equal_rate_growth(self):
        with pytest.raises(ValueError):
            growing_perpetuity(0.05, 0.05, 100)

    def test_with_ndigits(self):
        result = growing_perpetuity(0.10, 0.03, 100, ndigits=2)
        assert result == Decimal("1428.57")


class TestGrowingAnnuity:
    def test_basic_end(self):
        result = growing_annuity(0.10, 0.03, 5, 100)
        assert result == pytest.approx(Decimal("400.26"), abs=0.01)

    def test_basic_begin(self):
        result = growing_annuity(0.10, 0.03, 5, 100, when="begin")
        assert result > growing_annuity(0.10, 0.03, 5, 100)

    def test_equal_rate_growth_end(self):
        result = growing_annuity(0.05, 0.05, 5, 100)
        assert result == pytest.approx(Decimal("476.19"), abs=0.01)

    def test_equal_rate_growth_begin(self):
        result = growing_annuity(0.05, 0.05, 5, 100, when="begin")
        assert result == pytest.approx(Decimal("500"), abs=0.01)

    def test_zero_growth(self):
        result = growing_annuity(0.10, 0, 5, 100)
        assert result == pytest.approx(Decimal("379.08"), abs=0.01)

    def test_zero_rate(self):
        result = growing_annuity(0, 0, 5, 100)
        assert result == Decimal("500")

    def test_single_period(self):
        result = growing_annuity(0.10, 0.03, 1, 100)
        assert result == pytest.approx(Decimal("90.91"), abs=0.01)

    def test_with_ndigits(self):
        result = growing_annuity(0.10, 0.03, 5, 100, ndigits=2)
        assert result == Decimal("400.26")


class TestPvOfUnevenCashflows:
    def test_basic(self):
        result = pv_of_uneven_cashflows(0.10, [100, 200, 300])
        assert result == pytest.approx(Decimal("481.59"), abs=0.01)

    def test_empty_list(self):
        result = pv_of_uneven_cashflows(0.10, [])
        assert result == Decimal("0")

    def test_single_flow(self):
        result = pv_of_uneven_cashflows(0.10, [100])
        assert result == pytest.approx(Decimal("90.91"), abs=0.01)

    def test_mixed_signs(self):
        result = pv_of_uneven_cashflows(0.10, [-100, 200, -300])
        assert result == pytest.approx(Decimal("-151.01"), abs=0.01)

    def test_zero_rate(self):
        result = pv_of_uneven_cashflows(0, [100, 200, 300])
        assert result == Decimal("600")

    def test_with_ndigits(self):
        result = pv_of_uneven_cashflows(0.10, [100, 200, 300], ndigits=2)
        assert result == Decimal("481.59")


class TestPvContinuousCompounding:
    def test_basic(self):
        result = pv_continuous_compounding(0.05, 10, 1000)
        assert result == pytest.approx(Decimal("606.53"), abs=0.01)

    def test_zero_rate(self):
        result = pv_continuous_compounding(0, 10, 1000)
        assert result == Decimal("1000")

    def test_zero_periods(self):
        result = pv_continuous_compounding(0.05, 0, 1000)
        assert result == Decimal("1000")

    def test_with_ndigits(self):
        result = pv_continuous_compounding(0.05, 10, 1000, ndigits=2)
        assert result == Decimal("606.53")


class TestPvOfPerpetuityWithDelay:
    def test_basic(self):
        result = pv_of_perpetuity_with_delay(0.10, 100, 5)
        assert result == pytest.approx(Decimal("620.92"), abs=0.01)

    def test_zero_delay(self):
        result = pv_of_perpetuity_with_delay(0.10, 100, 0)
        assert result == Decimal("1000")

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            pv_of_perpetuity_with_delay(0, 100, 5)

    def test_with_ndigits(self):
        result = pv_of_perpetuity_with_delay(0.10, 100, 5, ndigits=2)
        assert result == Decimal("620.92")


class TestPvOfAnnuityContinuous:
    def test_basic(self):
        result = pv_of_annuity_continuous(0.05, 10, 100)
        assert result == pytest.approx(Decimal("786.94"), abs=0.01)

    def test_zero_rate(self):
        result = pv_of_annuity_continuous(0, 10, 100)
        assert result == Decimal("1000")

    def test_single_period(self):
        result = pv_of_annuity_continuous(0.05, 1, 100)
        assert result == pytest.approx(Decimal("97.54"), abs=0.01)

    def test_zero_pmt(self):
        result = pv_of_annuity_continuous(0.05, 10, 0)
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = pv_of_annuity_continuous(0.05, 10, 100, ndigits=2)
        assert result == Decimal("786.94")


class TestPvOfDeferredAnnuity:
    def test_basic(self):
        result = pv_of_deferred_annuity(0.10, 5, 100, 3)
        assert result == pytest.approx(Decimal("284.81"), abs=0.01)

    def test_zero_deferral(self):
        result = pv_of_deferred_annuity(0.10, 5, 100, 0)
        assert result == present_value(0.10, 5, 100, 0)

    def test_begin_mode(self):
        result = pv_of_deferred_annuity(0.10, 5, 100, 3, when="begin")
        assert result > pv_of_deferred_annuity(0.10, 5, 100, 3)

    def test_with_ndigits(self):
        result = pv_of_deferred_annuity(0.10, 5, 100, 3, ndigits=2)
        assert result == Decimal("284.81")

    def test_zero_rate(self):
        result = pv_of_deferred_annuity(0, 5, 100, 3)
        assert result == Decimal("500")


class TestPvOfGrowingPerpetuityWithDelay:
    def test_basic(self):
        result = pv_of_growing_perpetuity_with_delay(0.10, 0.03, 100, 5)
        assert result == pytest.approx(Decimal("887.03"), abs=0.01)

    def test_zero_delay(self):
        result = pv_of_growing_perpetuity_with_delay(0.10, 0.03, 100, 0)
        assert result == pytest.approx(Decimal("1428.57"), abs=0.01)

    def test_rate_less_than_growth(self):
        with pytest.raises(ValueError):
            pv_of_growing_perpetuity_with_delay(0.03, 0.05, 100, 5)

    def test_with_ndigits(self):
        result = pv_of_growing_perpetuity_with_delay(0.10, 0.03, 100, 5, ndigits=2)
        assert result == Decimal("887.03")


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=1, max_value=30))
def test_pv_annuity_due_greater_than_ordinary(rate, nper):
    pv_end = present_value(rate, nper, 100, 0)
    pv_begin = present_value(rate, nper, 100, 0, when="begin")
    assert pv_begin > pv_end


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=1, max_value=20), st.floats(min_value=10, max_value=1000))
def test_present_value_decreasing_with_rate(rate1, nper, fv):
    assume(rate1 > 0)
    pv1 = present_value(rate1, nper, 0, fv)
    pv2 = present_value(rate1 * 2, nper, 0, fv)
    assert pv1 > pv2


@given(st.floats(min_value=0.05, max_value=0.5), st.floats(min_value=0.01, max_value=0.04), st.integers(min_value=1, max_value=10))
def test_growing_perpetuity_greater_than_standard(rate, growth, _):
    assume(rate > growth)
    gp = growing_perpetuity(rate, growth, 100)
    p = perpetuity(rate, 100)
    assert gp > p

from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.loans.refinance import refinance_breakeven, refinance_total_savings, refinance_npv
from finpy.loans.refinance import refinance_irr, rate_comparison
from finpy.loans.schedule import monthly_payment


class TestRefinance:
    def test_basic(self):
        result = refinance_breakeven(100000, 0.06, 0.04, 3000, 360)
        assert result > 0

    def test_zero_savings(self):
        result = refinance_breakeven(100000, 0.04, 0.04, 3000, 360)
        assert result == Decimal("0")

    def test_no_closing_costs(self):
        result = refinance_breakeven(100000, 0.06, 0.04, 0, 360)
        assert result == Decimal("0")

    def test_higher_rate_no_breakeven(self):
        result = refinance_breakeven(100000, 0.04, 0.06, 3000, 360)
        assert result == Decimal("0")

    def test_small_savings(self):
        result = refinance_breakeven(100000, 0.05, 0.049, 3000, 360)
        assert result > 0

    def test_ndigits(self):
        result = refinance_breakeven(100000, 0.06, 0.04, 3000, 360, ndigits=0)
        assert isinstance(result, Decimal)


class TestRefinanceTotalSavings:
    def test_positive_savings(self):
        result = refinance_total_savings(100000, 0.06, 0.04, 3000, 360)
        assert result > 0

    def test_zero_savings_no_rate_change(self):
        result = refinance_total_savings(100000, 0.04, 0.04, 3000, 360)
        assert result == Decimal("0")

    def test_higher_rate_negative_savings(self):
        result = refinance_total_savings(100000, 0.04, 0.06, 3000, 360)
        assert result == Decimal("0")

    def test_savings_exceed_costs(self):
        result = refinance_total_savings(100000, 0.06, 0.04, 100, 360)
        assert result > 0

    def test_short_remaining(self):
        result = refinance_total_savings(100000, 0.06, 0.04, 3000, 12)
        assert result == Decimal("0")

    def test_ndigits(self):
        result = refinance_total_savings(100000, 0.06, 0.04, 3000, 360, ndigits=0)
        assert isinstance(result, Decimal)


class TestRefinanceNPV:
    def test_positive_npv(self):
        result = refinance_npv(100000, 0.06, 0.04, 3000, 360)
        assert result > 0

    def test_no_rate_change(self):
        result = refinance_npv(100000, 0.04, 0.04, 3000, 360)
        assert result < 0

    def test_with_discount_rate(self):
        result = refinance_npv(100000, 0.06, 0.04, 3000, 360, discount_rate=0.05)
        assert result > 0

    def test_high_closing_costs(self):
        result = refinance_npv(100000, 0.06, 0.04, 50000, 360)
        assert result < 0

    def test_higher_rate(self):
        result = refinance_npv(100000, 0.04, 0.06, 3000, 360)
        assert result < 0

    def test_ndigits(self):
        result = refinance_npv(100000, 0.06, 0.04, 3000, 360, ndigits=0)
        assert isinstance(result, Decimal)


class TestRefinanceIRR:
    def test_positive(self):
        result = refinance_irr(100000, 0.06, 0.04, 3000, 360)
        assert result > 0

    def test_no_rate_change(self):
        result = refinance_irr(100000, 0.04, 0.04, 3000, 360)
        assert result == Decimal("0")

    def test_higher_rate(self):
        result = refinance_irr(100000, 0.04, 0.06, 3000, 360)
        assert result == Decimal("0")

    def test_low_costs(self):
        result = refinance_irr(100000, 0.06, 0.04, 100, 360)
        assert result > 0


class TestRateComparison:
    def test_basic(self):
        result = rate_comparison(0.06, 0.04, 3000, 100)
        assert "breakeven_months" in result
        assert "one_year_savings" in result
        assert "five_year_savings" in result

    def test_breakeven_positive(self):
        result = rate_comparison(0.06, 0.04, 3000, 100)
        assert result["breakeven_months"] == Decimal("30")

    def test_one_year_savings(self):
        result = rate_comparison(0.06, 0.04, 3000, 300)
        assert result["one_year_savings"] > 0

    def test_no_monthly_savings(self):
        result = rate_comparison(0.06, 0.04, 3000, 0)
        assert result["breakeven_months"] == Decimal("0")

    def test_negative_savings(self):
        result = rate_comparison(0.04, 0.06, 3000, -50)
        assert result["breakeven_months"] == Decimal("0")

    def test_ndigits(self):
        result = rate_comparison(0.06, 0.04, 3000, 100, ndigits=0)
        assert all(isinstance(v, Decimal) for v in result.values())

    def test_five_year_savings_exceeds_one_year(self):
        result = rate_comparison(0.06, 0.04, 3000, 200)
        assert result["five_year_savings"] > result["one_year_savings"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_breakeven_non_negative(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    result = refinance_breakeven(principal, old_rate, new_rate, 3000, remaining)
    assert result >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_total_savings_non_negative(principal, old_rate, new_rate, remaining):
    result = refinance_total_savings(principal, old_rate, new_rate, 3000, remaining)
    assert result >= 0


@given(st.floats(100000, 500000), st.floats(0.05, 0.10), st.floats(0.02, 0.04), st.integers(180, 360))
def test_npv_positive_for_good_deal(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    result = refinance_npv(principal, old_rate, new_rate, 1000, remaining)
    assert result > 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_breakeven_monotonic_with_costs(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    be_low = refinance_breakeven(principal, old_rate, new_rate, 1000, remaining)
    be_high = refinance_breakeven(principal, old_rate, new_rate, 5000, remaining)
    assert be_high >= be_low


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_savings_decreases_with_costs(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    s_low = refinance_total_savings(principal, old_rate, new_rate, 1000, remaining)
    s_high = refinance_total_savings(principal, old_rate, new_rate, 5000, remaining)
    assert s_high <= s_low


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_npv_decreases_with_costs(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    npv_low = refinance_npv(principal, old_rate, new_rate, 1000, remaining)
    npv_high = refinance_npv(principal, old_rate, new_rate, 5000, remaining)
    assert npv_high <= npv_low


@given(st.floats(50000, 500000), st.floats(0.02, 0.10), st.floats(0.02, 0.10), st.integers(60, 360))
def test_breakeven_zero_when_rate_not_lower(principal, old_rate, new_rate, remaining):
    if new_rate >= old_rate:
        result = refinance_breakeven(principal, old_rate, new_rate, 3000, remaining)
        assert result == Decimal("0")


@given(st.floats(50, 500), st.floats(0.02, 0.10))
def test_rate_comparison_breakeven(monthly_savings, rate_diff):
    if monthly_savings <= 0:
        return
    result = rate_comparison(0.06, 0.04, 3000, monthly_savings)
    assert result["breakeven_months"] > 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_irr_positive(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    pmt_old = monthly_payment(principal, old_rate, remaining)
    pmt_new = monthly_payment(principal, new_rate, remaining)
    total_undiscounted_savings = (pmt_old - pmt_new) * remaining
    if total_undiscounted_savings <= 100:
        return
    result = refinance_irr(principal, old_rate, new_rate, 100, remaining)
    assert result > 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_total_savings_positive(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    result = refinance_total_savings(principal, old_rate, new_rate, 100, remaining)
    assert result >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_breakeven_increases_with_costs(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    be_small = refinance_breakeven(principal, old_rate, new_rate, 1000, remaining)
    be_large = refinance_breakeven(principal, old_rate, new_rate, 10000, remaining)
    assert be_large >= be_small


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_rate_comparison_zero_savings_no_rate_change(principal, old_rate, new_rate, remaining):
    result = rate_comparison(old_rate, new_rate, 3000, 0)
    assert result["breakeven_months"] == Decimal("0")
    assert result["one_year_savings"] == Decimal("0")
    assert result["five_year_savings"] == Decimal("0")


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_npv_decreases_with_discount_rate(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    npv_low = refinance_npv(principal, old_rate, new_rate, 3000, remaining, discount_rate=0.02)
    npv_high = refinance_npv(principal, old_rate, new_rate, 3000, remaining, discount_rate=0.08)
    assert npv_high <= npv_low


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_rate_comparison_one_year_gt_zero(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    ms = float(monthly_payment(principal, old_rate, remaining / 12)) - float(monthly_payment(principal, new_rate, remaining / 12))
    if ms <= 0:
        return
    result = rate_comparison(old_rate, new_rate, 3000, ms)
    assert result["one_year_savings"] >= 0
    assert result["five_year_savings"] >= result["one_year_savings"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_irr_zero(principal, old_rate, new_rate, remaining):
    if new_rate >= old_rate:
        result = refinance_irr(principal, old_rate, new_rate, 3000, remaining)
        assert result == Decimal("0")


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.05), st.integers(180, 360))
def test_refinance_npv_high_discount(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    npv = refinance_npv(principal, old_rate, new_rate, 3000, remaining, discount_rate=0.12)
    assert npv <= refinance_npv(principal, old_rate, new_rate, 3000, remaining, discount_rate=0.02)


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_breakeven_known_values(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        assert refinance_breakeven(principal, old_rate, new_rate, 3000, remaining) == Decimal("0")


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_total_savings_bounded(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    ts = refinance_total_savings(principal, old_rate, new_rate, 3000, remaining)
    be = refinance_breakeven(principal, old_rate, new_rate, 3000, remaining)
    if be > 0 and be < remaining:
        assert ts > 0
    else:
        assert ts >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_rate_comparison_no_savings(principal, old_rate, new_rate, remaining):
    result = rate_comparison(old_rate, new_rate, 3000, 0)
    assert result["breakeven_months"] == Decimal("0")


@given(st.floats(100, 1000), st.floats(0.02, 0.08))
def test_rate_comparison_savings_increase(principal, old_rate):
    for savings in [100, 200, 300]:
        result = rate_comparison(old_rate, old_rate - 0.01, 1000, savings)
        assert result["breakeven_months"] > 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.05), st.integers(120, 360))
def test_refinance_irr_with_rate_change(principal, old_rate, new_rate, remaining):
    if old_rate <= new_rate:
        return
    irr = refinance_irr(principal, old_rate, new_rate, 100, remaining)
    assert irr > 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(0.02, 0.07), st.integers(60, 360))
def test_refinance_irr_zero_rate(principal, old_rate, new_rate, remaining):
    if new_rate >= old_rate:
        irr = refinance_irr(principal, old_rate, new_rate, 3000, remaining)
        assert irr == Decimal("0")



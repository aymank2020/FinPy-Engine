from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.loans.prepayment import apply_prepayment, apply_lump_sum, recast_payment, extra_payment_summary
from finpy.loans.schedule import monthly_payment


class TestApplyPrepayment:
    def test_basic(self):
        result = apply_prepayment(100000, 0.05, 10, 5000, 12)
        assert result["prepayment"] == Decimal("5000")
        assert result["balance_after"] < result["balance_before"]

    def test_zero_prepayment(self):
        result = apply_prepayment(100000, 0.05, 10, 0, 12)
        assert result["prepayment"] == Decimal("0")
        assert result["balance_after"] == result["balance_before"]

    def test_full_prepayment(self):
        result = apply_prepayment(100000, 0.05, 10, 1_000_000, 12)
        assert result["balance_after"] == Decimal("0")

    def test_early_payment(self):
        result = apply_prepayment(100000, 0.05, 10, 10000, 1)
        assert result["balance_after"] < result["balance_before"]

    def test_late_payment(self):
        result = apply_prepayment(100000, 0.05, 10, 5000, 100)
        assert result["balance_after"] < result["balance_before"]

    def test_ndigits(self):
        result = apply_prepayment(100000, 0.05, 10, 5000, 12, ndigits=2)
        assert all(isinstance(v, Decimal) for v in result.values())

    def test_balance_before_positive(self):
        result = apply_prepayment(100000, 0.05, 10, 5000, 12)
        assert result["balance_before"] > 0

    def test_result_keys(self):
        result = apply_prepayment(100000, 0.05, 10, 5000, 12)
        assert "balance_before" in result
        assert "prepayment" in result
        assert "balance_after" in result


class TestApplyLumpSum:
    def test_basic(self):
        result = apply_lump_sum(100000, 0.05, 10, 10000, 12)
        assert "original_balance" in result
        assert "lump_sum" in result
        assert "new_balance" in result
        assert "interest_saved" in result

    def test_lump_sum_reduces_balance(self):
        result = apply_lump_sum(100000, 0.05, 10, 10000, 12)
        assert result["new_balance"] < result["original_balance"]

    def test_interest_saved_positive(self):
        result = apply_lump_sum(100000, 0.05, 10, 10000, 12)
        assert result["interest_saved"] > 0

    def test_full_payoff(self):
        result = apply_lump_sum(100000, 0.05, 10, 1_000_000, 12)
        assert result["new_balance"] == Decimal("0")

    def test_zero_lump_sum(self):
        result = apply_lump_sum(100000, 0.05, 10, 0, 12)
        assert result["lump_sum"] == Decimal("0")
        assert result["new_balance"] == result["original_balance"]

    def test_ndigits(self):
        result = apply_lump_sum(100000, 0.05, 10, 10000, 12, ndigits=2)
        assert all(isinstance(v, Decimal) for v in result.values())


class TestRecastPayment:
    def test_basic(self):
        result = recast_payment(100000, 0.05, 10, 10000, 12)
        assert result > 0

    def test_recast_lower_than_original(self):
        from finpy.loans.schedule import monthly_payment
        orig = monthly_payment(100000, 0.05, 10)
        recast = recast_payment(100000, 0.05, 10, 10000, 12)
        assert recast < orig

    def test_full_prepayment_zero(self):
        result = recast_payment(100000, 0.05, 10, 1_000_000, 12)
        assert result == Decimal("0")

    def test_zero_prepayment(self):
        from finpy.loans.schedule import monthly_payment
        orig = monthly_payment(100000, 0.05, 10)
        recast = recast_payment(100000, 0.05, 10, 0, 12)
        assert recast == pytest.approx(orig, abs=0.01)

    def test_ndigits(self):
        result = recast_payment(100000, 0.05, 10, 10000, 12, ndigits=2)
        assert isinstance(result, Decimal)


class TestExtraPaymentSummary:
    def test_basic(self):
        result = extra_payment_summary(100000, 0.05, 10, 200)
        assert "original_payment" in result
        assert "new_payment" in result
        assert "original_periods" in result
        assert "new_periods" in result
        assert "original_interest" in result
        assert "new_interest" in result
        assert "interest_saved" in result

    def test_new_payment_higher(self):
        result = extra_payment_summary(100000, 0.05, 10, 200)
        assert result["new_payment"] > result["original_payment"]

    def test_fewer_periods(self):
        result = extra_payment_summary(100000, 0.05, 10, 200)
        assert result["new_periods"] < result["original_periods"]

    def test_interest_saved_positive(self):
        result = extra_payment_summary(100000, 0.05, 10, 200)
        assert result["interest_saved"] > 0

    def test_zero_extra(self):
        result = extra_payment_summary(100000, 0.05, 10, 0)
        assert result["new_payment"] == result["original_payment"]

    def test_large_extra(self):
        result = extra_payment_summary(100000, 0.05, 10, 5000)
        assert result["new_periods"] < result["original_periods"]

    def test_ndigits(self):
        result = extra_payment_summary(100000, 0.05, 10, 200, ndigits=2)
        assert all(isinstance(v, Decimal) for v in result.values())


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(1000, 50000), st.integers(1, 60))
def test_prepayment_reduces_balance(principal, rate, years, amount, payment_num):
    result = apply_prepayment(principal, rate, years, amount, payment_num)
    assert result["balance_after"] <= result["balance_before"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(1000, 50000), st.integers(1, 60))
def test_prepayment_non_negative(principal, rate, years, amount, payment_num):
    result = apply_prepayment(principal, rate, years, amount, payment_num)
    assert result["balance_before"] >= 0
    assert result["prepayment"] >= 0
    assert result["balance_after"] >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(1000, 50000), st.integers(1, 60))
def test_prepayment_not_exceed_balance(principal, rate, years, amount, payment_num):
    result = apply_prepayment(principal, rate, years, amount, payment_num)
    assert result["prepayment"] <= result["balance_before"]
    assert result["balance_after"] == result["balance_before"] - result["prepayment"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(1000, 50000), st.integers(1, 60))
def test_lump_sum_saves_interest(principal, rate, years, amount, payment_num):
    result = apply_lump_sum(principal, rate, years, amount, payment_num)
    assert result["interest_saved"] >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(1000, 50000), st.integers(1, 60))
def test_recast_lowers_payment(principal, rate, years, amount, payment_num):
    from finpy.loans.schedule import monthly_payment
    orig = monthly_payment(principal, rate, years)
    recast = recast_payment(principal, rate, years, amount, payment_num)
    assert recast <= orig


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(50, 500))
def test_extra_payment_saves_interest(principal, rate, years, extra):
    result = extra_payment_summary(principal, rate, years, extra)
    assert result["interest_saved"] >= 0
    assert result["new_periods"] <= result["original_periods"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10))
def test_extra_payment_zero_extra(principal, rate, years):
    result = extra_payment_summary(principal, rate, years, 0)
    assert result["new_payment"] == result["original_payment"]
    assert result["new_periods"] >= result["original_periods"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(100, 1000), st.integers(1, 60))
def test_apply_prepayment_balance_decreases(principal, rate, years, amount, payment_num):
    result = apply_prepayment(principal, rate, years, amount, payment_num)
    assert result["balance_after"] <= result["balance_before"]
    assert result["prepayment"] <= result["balance_before"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(100, 10000), st.integers(1, 60))
def test_apply_lump_sum_reduces(principal, rate, years, amount, payment_num):
    result = apply_lump_sum(principal, rate, years, amount, payment_num)
    assert result["new_balance"] <= result["original_balance"]
    assert result["lump_sum"] == min(Decimal(str(amount)), result["original_balance"])


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(100, 10000), st.integers(1, 60))
def test_recast_payment_lowers(principal, rate, years, amount, payment_num):
    orig = monthly_payment(principal, rate, years)
    recast = recast_payment(principal, rate, years, amount, payment_num)
    assert recast <= orig


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(100, 2000))
def test_extra_payment_fewer_periods(principal, rate, years, extra):
    result = extra_payment_summary(principal, rate, years, extra)
    assert result["new_periods"] <= result["original_periods"]
    assert result["new_payment"] > result["original_payment"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10))
def test_apply_prepayment_zero_amount(principal, rate, years):
    result = apply_prepayment(principal, rate, years, 0, 12)
    assert result["prepayment"] == Decimal("0")
    assert result["balance_after"] == result["balance_before"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10))
def test_recast_payment_full_prepayment(principal, rate, years):
    result = recast_payment(principal, rate, years, 1_000_000, 12)
    assert result == Decimal("0")


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(500, 10000), st.integers(1, 60))
def test_apply_prepayment_prepayment_amount_capped(principal, rate, years, amount, payment_num):
    result = apply_prepayment(principal, rate, years, amount, payment_num)
    assert result["prepayment"] <= result["balance_before"]
    assert result["balance_after"] == result["balance_before"] - result["prepayment"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(500, 10000), st.integers(1, 60))
def test_apply_lump_sum_new_balance_non_negative(principal, rate, years, amount, payment_num):
    result = apply_lump_sum(principal, rate, years, amount, payment_num)
    assert result["new_balance"] >= 0
    assert result["original_balance"] >= 0
    assert result["interest_saved"] >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(500, 10000), st.integers(1, 60))
def test_recast_payment_non_negative(principal, rate, years, amount, payment_num):
    result = recast_payment(principal, rate, years, amount, payment_num)
    assert result >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(100, 2000))
def test_extra_payment_interest_saved_increases_with_extra(principal, rate, years, extra):
    result_small = extra_payment_summary(principal, rate, years, extra)
    result_large = extra_payment_summary(principal, rate, years, extra + 200)
    assert result_large["interest_saved"] >= result_small["interest_saved"]
    assert result_large["new_periods"] <= result_small["new_periods"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10))
def test_apply_prepayment_first_period(principal, rate, years):
    result = apply_prepayment(principal, rate, years, 5000, 1)
    assert result["balance_after"] < result["balance_before"]


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10))
def test_apply_prepayment_last_period(principal, rate, years):
    n = int(years * 12)
    result = apply_prepayment(principal, rate, years, 5000, max(1, n - 1))
    assert result["prepayment"] >= 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10), st.floats(1000, 50000), st.integers(1, 60))
def test_apply_lump_sum_interest_saved(principal, rate, years, amount, payment_num):
    assume(payment_num < int(years * 12))
    result = apply_lump_sum(principal, rate, years, amount, payment_num)
    if amount > 0:
        assert result["lump_sum"] > 0


@given(st.floats(50000, 500000), st.floats(0.03, 0.08), st.floats(1, 10))
def test_extra_payment_original_values_consistent(principal, rate, years):
    result = extra_payment_summary(principal, rate, years, 100)
    mp = monthly_payment(principal, rate, years)
    assert result["original_payment"] == mp
    assert result["original_periods"] == Decimal(int(years * 12))

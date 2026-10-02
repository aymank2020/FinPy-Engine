from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.loans.schedule import amortization_schedule, outstanding_balance, total_interest
from finpy.loans.schedule import monthly_payment, interest_only_payment, balloon_payment
from finpy.loans.schedule import apr_from_apy, apy_from_apr, loan_payoff_time, amortization_summary
from tests._helpers import approx_decimal


class TestSchedule:
    def test_length(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        assert len(s) == 12

    def test_ends_at_zero(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        assert s[-1]["balance"] == Decimal("0")

    def test_decreasing_balance(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        for i in range(1, len(s)):
            assert s[i]["balance"] <= s[i - 1]["balance"]

    def test_decreasing_interest(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        for i in range(1, len(s)):
            assert s[i]["interest"] <= s[i - 1]["interest"]

    def test_increasing_principal(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        for i in range(1, len(s)):
            assert s[i]["principal"] >= s[i - 1]["principal"]

    def test_constant_payment(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        pmts = [row["payment"] for row in s[:-1]]
        assert all(p == pmts[0] for p in pmts)

    def test_zero_rate(self):
        s = amortization_schedule(10000, 0.0, 1, 12)
        assert s[-1]["balance"] == Decimal("0")
        assert s[0]["interest"] == Decimal("0")

    def test_short_schedule(self):
        s = amortization_schedule(1000, 0.05, 0.25, 12)
        assert len(s) == 3

    def test_large_principal(self):
        s = amortization_schedule(1_000_000, 0.05, 30, 12)
        assert len(s) == 360
        assert s[-1]["balance"] == Decimal("0")

    def test_annual_payments(self):
        s = amortization_schedule(10000, 0.05, 5, 1)
        assert len(s) == 5
        assert s[-1]["balance"] == Decimal("0")

    def test_quarterly_payments(self):
        s = amortization_schedule(10000, 0.05, 5, 4)
        assert len(s) == 20
        assert s[-1]["balance"] == Decimal("0")

    def test_fields_present(self):
        s = amortization_schedule(10000, 0.05, 1, 12)
        entry = s[0]
        assert "period" in entry
        assert "payment" in entry
        assert "interest" in entry
        assert "principal" in entry
        assert "balance" in entry

    def test_ndigits(self):
        s = amortization_schedule(10000, 0.05, 1, 12, ndigits=2)
        for entry in s:
            for v in entry.values():
                assert isinstance(v, Decimal)


class TestOutstandingBalance:
    def test_initial(self):
        result = outstanding_balance(10000, 0.05, 30, 0)
        assert result == pytest.approx(Decimal("10000"), abs=0.01)

    def test_fully_paid(self):
        result = outstanding_balance(10000, 0.05, 30, 360)
        assert result == Decimal("0")

    def test_mid_loan(self):
        result = outstanding_balance(10000, 0.05, 30, 60)
        assert result < Decimal("10000")
        assert result > 0

    def test_zero_rate(self):
        result = outstanding_balance(10000, 0.0, 30, 60)
        assert result == pytest.approx(Decimal("10000") * (Decimal(360 - 60) / Decimal(360)), abs=0.01)

    def test_ndigits(self):
        result = outstanding_balance(10000, 0.05, 30, 60, ndigits=2)
        assert isinstance(result, Decimal)

    def test_positive_exceeds(self):
        result = outstanding_balance(10000, 0.05, 30, 400)
        assert result == Decimal("0")


class TestTotalInterest:
    def test_zero_rate(self):
        result = total_interest(10000, 0.0, 30)
        assert result == Decimal("0")

    def test_positive_rate(self):
        result = total_interest(10000, 0.05, 30)
        assert result > 0

    def test_short_term(self):
        result = total_interest(10000, 0.05, 1)
        assert result > 0

    def test_ndigits(self):
        result = total_interest(10000, 0.05, 30, ndigits=2)
        assert isinstance(result, Decimal)


class TestMonthlyPayment:
    def test_basic(self):
        result = monthly_payment(10000, 0.05, 30)
        assert result > 0

    def test_zero_rate(self):
        result = monthly_payment(10000, 0.0, 30)
        assert result == Decimal("10000") / Decimal(360)

    def test_short_term_higher_payment(self):
        short = monthly_payment(10000, 0.05, 5)
        long = monthly_payment(10000, 0.05, 30)
        assert short > long


class TestInterestOnlyPayment:
    def test_basic(self):
        result = interest_only_payment(10000, 0.05)
        assert result == pytest.approx(Decimal("41.6666666667"), abs=1e-9)

    def test_zero_rate(self):
        result = interest_only_payment(10000, 0.0)
        assert result == Decimal("0")


class TestBalloonPayment:
    def test_fully_amortized(self):
        result = balloon_payment(10000, 0.05, 30, 30)
        assert result == Decimal("0")

    def test_balloon_exists(self):
        result = balloon_payment(10000, 0.05, 25, 30)
        assert result >= 0

    def test_zero_rate(self):
        result = balloon_payment(10000, 0.0, 25, 30)
        assert result == pytest.approx(Decimal("10000") * Decimal(5) / Decimal(30), abs=Decimal("1e-20"))

    def test_short_balloon_positive(self):
        result = balloon_payment(100000, 0.06, 5, 30)
        assert result >= 0


class TestAPRAPY:
    def test_apr_to_apy_roundtrip(self):
        apy = apy_from_apr(Decimal("0.05"), 12)
        apr = apr_from_apy(apy, 12)
        assert apr == pytest.approx(Decimal("0.05"), abs=1e-10)

    def test_apy_gt_apr(self):
        apy = apy_from_apr(Decimal("0.05"), 12)
        assert apy > Decimal("0.05")

    def test_apr_non_negative(self):
        with pytest.raises(ValueError):
            apr_from_apy(Decimal("-2"), 12)

    def test_negative_nominal_rate_roundtrip(self):
        effective = apy_from_apr(Decimal("-0.01"), 12)
        assert -1 < effective < 0
        assert apr_from_apy(effective, 12) == pytest.approx(Decimal("-0.01"), abs=Decimal("1e-20"))

    def test_annual_equivalent(self):
        apy = apy_from_apr(Decimal("0.05"), 1)
        assert apy == Decimal("0.05")

    def test_apr_from_apy_annual(self):
        apr = apr_from_apy(Decimal("0.05"), 1)
        assert apr == Decimal("0.05")


class TestLoanPayoffTime:
    def test_basic(self):
        result = loan_payoff_time(10000, 0.05, 200, 12)
        assert result > 0

    def test_high_payment(self):
        result = loan_payoff_time(10000, 0.05, 1000, 12)
        assert result < 12

    def test_zero_rate(self):
        result = loan_payoff_time(10000, 0.0, 1000, 12)
        assert result == Decimal("10")

    def test_payment_too_low(self):
        with pytest.raises(ValueError):
            loan_payoff_time(10000, 0.05, 10, 12)


class TestAmortizationSummary:
    def test_basic(self):
        result = amortization_summary(10000, 0.05, 30)
        assert "total_paid" in result
        assert "total_interest" in result
        assert "first_year_interest" in result
        assert "num_payments" in result

    def test_total_paid_gt_principal(self):
        result = amortization_summary(10000, 0.05, 30)
        assert result["total_paid"] > Decimal("10000")

    def test_total_interest_positive(self):
        result = amortization_summary(10000, 0.05, 30)
        assert result["total_interest"] > 0

    def test_zero_rate(self):
        result = amortization_summary(10000, 0.0, 30)
        assert result["total_paid"] == Decimal("10000")
        assert result["total_interest"] == Decimal("0")

    def test_first_year_interest_positive(self):
        result = amortization_summary(10000, 0.05, 30)
        assert result["first_year_interest"] > 0

    def test_num_payments(self):
        result = amortization_summary(10000, 0.05, 30, 12)
        assert result["num_payments"] == Decimal(360)

    def test_ndigits(self):
        result = amortization_summary(10000, 0.05, 30, ndigits=2)
        assert all(isinstance(v, Decimal) for v in result.values())


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_schedule_conservation(principal, rate, years):
    s = amortization_schedule(principal, rate, years, 12)
    total_principal = sum(row["principal"] for row in s)
    assert total_principal == pytest.approx(Decimal(str(principal)), abs=1)
    assert s[-1]["balance"] == Decimal("0")


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_schedule_ends_at_zero(principal, rate, years):
    s = amortization_schedule(principal, rate, years, 12)
    assert s[-1]["balance"] == Decimal("0")


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_schedule_monotonic_balance(principal, rate, years):
    s = amortization_schedule(principal, rate, years, 12)
    for i in range(1, len(s)):
        assert s[i]["balance"] <= s[i - 1]["balance"]


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_schedule_monotonic_interest(principal, rate, years):
    s = amortization_schedule(principal, rate, years, 12)
    for i in range(1, len(s)):
        assert s[i]["interest"] <= s[i - 1]["interest"] + Decimal("0.01")


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_total_interest_non_negative(principal, rate, years):
    ti = total_interest(principal, rate, years)
    assert ti >= 0


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_outstanding_balance_decreases(principal, rate, years):
    n = int(years * 12)
    bal_early = outstanding_balance(principal, rate, years, n // 4)
    bal_late = outstanding_balance(principal, rate, years, n // 2)
    assert bal_late <= bal_early


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_amort_summary_consistency(principal, rate, years):
    result = amortization_summary(principal, rate, years)
    assert result["total_paid"] == pytest.approx(result["total_interest"] + Decimal(str(principal)), abs=1)
    assert result["num_payments"] == Decimal(int(years * 12))


@given(st.decimals(0.01, 0.30))
def test_apr_apy_roundtrip(apr):
    apy = apy_from_apr(apr, 12)
    apr2 = apr_from_apy(apy, 12)
    assert apr2 == pytest.approx(apr, abs=1e-10)


@given(st.floats(1000, 100000), st.floats(0.01, 0.15))
def test_monthly_payment_positive(principal, rate):
    pmt = monthly_payment(principal, rate, 30)
    assert pmt > 0


@given(st.floats(1000, 100000), st.floats(0.01, 0.15))
def test_balloon_zero_when_fully_amortized(principal, rate):
    b = balloon_payment(principal, rate, 10, 10)
    assert b == pytest.approx(Decimal("0"), abs=Decimal("1e-10"))


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_outstanding_balance_initial(principal, rate, years):
    result = outstanding_balance(principal, rate, years, 0)
    assert result == pytest.approx(Decimal(str(principal)), abs=1)


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_outstanding_balance_final(principal, rate, years):
    n = int(years * 12)
    result = outstanding_balance(principal, rate, years, n)
    assert result == pytest.approx(Decimal("0"), abs=Decimal("1e-20"))


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_monthly_payment_same_as_schedule(principal, rate, years):
    mp = monthly_payment(principal, rate, years)
    s = amortization_schedule(principal, rate, years, 12)
    assert s[0]["payment"] == pytest.approx(mp, abs=0.01)


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_interest_only_payment_less_than_monthly(principal, rate, years):
    io = interest_only_payment(principal, rate)
    mp = monthly_payment(principal, rate, years)
    assert io < mp


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_apr_from_apy_reciprocal(principal, rate, years):
    apr = Decimal(str(rate))
    apy = apy_from_apr(apr, 12)
    apr_back = apr_from_apy(apy, 12)
    assert apr_back == pytest.approx(apr, abs=1e-10)


@given(st.decimals(0.001, 0.50))
def test_apy_increasing_with_periods(apr):
    apy_annual = apy_from_apr(apr, 1)
    apy_monthly = apy_from_apr(apr, 12)
    apy_daily = apy_from_apr(apr, 365)
    assert apy_annual <= apy_monthly <= apy_daily


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_loan_payoff_time_decreases_with_payment(principal, rate, years):
    mp = float(monthly_payment(principal, rate, years))
    t1 = loan_payoff_time(principal, rate, mp * 1.5)
    t2 = loan_payoff_time(principal, rate, mp * 2.0)
    assert t2 < t1


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_amortization_summary_positive(principal, rate, years):
    result = amortization_summary(principal, rate, years)
    assert result["total_paid"] > 0
    assert result["total_interest"] >= 0
    assert result["first_year_interest"] >= 0
    assert result["num_payments"] > 0


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_zero_rate_schedule(principal, rate, years):
    s = amortization_schedule(principal, 0.0, years, 12)
    assert all(row["interest"] == Decimal("0") for row in s)
    assert s[-1]["balance"] == Decimal("0")
    total_p = sum(row["principal"] for row in s)
    assert total_p == pytest.approx(Decimal(str(principal)), abs=1)


@given(st.floats(1000, 100000), st.floats(0.01, 0.15), st.integers(1, 10))
def test_total_interest_less_for_shorter_term(principal, rate, years):
    i_short = total_interest(principal, rate, years)
    i_long = total_interest(principal, rate, years + 10)
    assert i_long > i_short


@given(st.floats(1000, 100000), st.floats(0.01, 0.15))
def test_monthly_payment_decreasing_with_years(principal, rate):
    p_short = monthly_payment(principal, rate, 5)
    p_long = monthly_payment(principal, rate, 30)
    assert p_short > p_long

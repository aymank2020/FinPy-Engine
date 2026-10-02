from decimal import Decimal, localcontext

import pytest

from finpy.core.compounding import continuous_equiv, discrete_equiv
from finpy.core.discount import discount_factor, zero_coupon_rate, modified_duration
from finpy.loans.schedule import amortization_schedule, monthly_payment, amortization_summary
from finpy.loans.prepayment import apply_lump_sum, extra_payment_schedule, extra_payment_summary
from finpy.loans.refinance import refinance_irr, refinance_npv
from finpy.returns.log_returns import annualized_return, std


@pytest.mark.parametrize("frequency", [1, 2, 4, 12, 52, 365])
@pytest.mark.parametrize("nominal", [Decimal("-0.02"), Decimal("0"), Decimal("0.08")])
def test_nominal_continuous_inverse(frequency, nominal):
    continuous = continuous_equiv(nominal, frequency)
    assert discrete_equiv(continuous, frequency) == pytest.approx(nominal, abs=Decimal("1e-24"))


@pytest.mark.parametrize("mode", ["annual", "semi-annual", "quarterly", "monthly", "weekly", "daily", "continuous", "money-market", "bond-basis"])
@pytest.mark.parametrize("rate", [Decimal("-0.02"), Decimal("0.07")])
def test_discount_implied_yield_inverse(mode, rate):
    time = Decimal("730") if mode == "bond-basis" else Decimal("2")
    factor = discount_factor(rate, time, mode)
    assert zero_coupon_rate(factor, time, mode=mode) == pytest.approx(rate, abs=Decimal("1e-24"))


def test_modified_duration_matches_price_sensitivity():
    cashflows = [(Decimal(5), Decimal("0.5")), (Decimal(105), Decimal(1))]
    rate, shift = Decimal("0.04"), Decimal("1e-8")

    def price(yield_):
        return sum(amount * discount_factor(yield_, time, "semi-annual") for amount, time in cashflows)

    sensitivity = -(price(rate + shift) - price(rate - shift)) / (2 * shift * price(rate))
    assert modified_duration(cashflows, rate, periods_per_year=2) == pytest.approx(sensitivity, abs=Decimal("1e-14"))


def test_one_year_interest_and_summary_aliases():
    rows = amortization_schedule(12000, Decimal("0.06"), 2)
    summary = amortization_summary(12000, Decimal("0.06"), 2)
    assert summary["first_year_interest"] == sum(row["interest"] for row in rows[:12])
    assert summary["total_paid"] == summary["total_payments"]
    assert summary["num_payments"] == summary["n_periods"] == 24
    assert summary["total_paid"] - summary["total_interest"] == pytest.approx(Decimal(12000), abs=Decimal("1e-20"))


def test_extra_payment_rows_conserve_cash_and_principal():
    rows = extra_payment_schedule(10000, Decimal("0.06"), 5, 100)
    summary = extra_payment_summary(10000, Decimal("0.06"), 5, 100)
    assert isinstance(rows, list)
    assert rows[-1]["balance"] == 0
    assert sum(row["principal"] for row in rows) == pytest.approx(Decimal(10000), abs=Decimal("1e-20"))
    assert all(row["payment"] == row["principal"] + row["interest"] for row in rows)
    assert summary["new_interest"] == sum(row["interest"] for row in rows)
    assert summary["new_periods"] == len(rows)
    assert summary["interest_saved"] > 0


def test_zero_interest_prepayment_has_no_interest_savings():
    result = apply_lump_sum(1200, 0, 1, 200, 3)
    assert result == {"original_balance": Decimal(900), "lump_sum": Decimal(200), "new_balance": Decimal(700), "interest_saved": Decimal(0)}


@pytest.mark.parametrize("cost", [Decimal("0.01"), Decimal("3000"), Decimal("50000")])
def test_refinance_irr_zeros_actual_npv_beyond_old_bracket(cost):
    irr = refinance_irr(100000, Decimal("0.06"), Decimal("0.04"), cost, 120, tol=Decimal("1e-16"))
    residual = refinance_npv(100000, Decimal("0.06"), Decimal("0.04"), cost, 120, discount_rate=irr)
    assert abs(residual) < Decimal("1e-15")


def test_no_finite_irr_for_zero_initial_cost():
    with pytest.raises(ValueError, match="costs"):
        refinance_irr(100000, Decimal("0.06"), Decimal("0.04"), 0, 120)


def test_decimal_tiny_standard_deviation_is_not_float_underflow():
    with localcontext() as context:
        context.prec = 40
        assert std([Decimal(0), Decimal("1e-200")]) > 0


def test_annualization_both_supported_contracts():
    assert annualized_return(Decimal("0.21"), 2) == Decimal("0.1")
    assert annualized_return([Decimal("0.1"), Decimal("0.1")], 1) == Decimal("0.1")


@pytest.mark.parametrize("years, frequency", [(0, 12), (-1, 12), (1, 0), (1, -1)])
def test_invalid_payment_horizon_is_explicit(years, frequency):
    with pytest.raises(ValueError):
        monthly_payment(1000, Decimal("0.05"), years, payments_per_year=frequency)

"""Loan prepayment scenarios.

Tests use:
    apply_prepayment(principal, rate, years, prepay_amount, period, *, ndigits)
        -> {"balance_before", "prepayment", "balance_after"}
    apply_lump_sum(principal, rate, years, lump, period, *, ndigits)
        -> {"original_balance", "lump_sum", "new_balance", "interest_saved"}
    recast_payment(principal, rate, years, lump, period, *, ndigits) -> Decimal
    extra_payment_schedule(principal, rate, years, extra) -> list[dict]
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from finpy.loans.schedule import (
    monthly_payment,
    outstanding_balance,
    _period_count,
    amortization_schedule,
)


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def _quantize_dict(d, ndigits):
    if ndigits is None:
        return d
    return {k: v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP) for k, v in d.items()}


def apply_prepayment(principal, annual_rate, years, prepay_amount, period, *, payments_per_year=12, ndigits=None):
    """Apply a one-time `prepay_amount` after `period` regular payments."""
    bal_before = outstanding_balance(principal, annual_rate, years, period, payments_per_year=payments_per_year)
    prepay = Decimal(str(prepay_amount))
    bal_after = bal_before - prepay
    if bal_after < 0:
        prepay = bal_before
        bal_after = Decimal(0)
    out = {
        "balance_before": bal_before,
        "prepayment": prepay,
        "balance_after": bal_after,
    }
    return _quantize_dict(out, ndigits)


def apply_lump_sum(principal, annual_rate, years, lump_sum, period, *, payments_per_year=12, ndigits=None):
    """Prepay after period payments, keep the payment, and shorten the term.

    Interest savings compare actual remaining amortization interest, including
    the smaller final payment. Recasting is a separate operation. Whole payment
    counts accept int, float and Decimal, including schedule row periods.
    """
    try:
        period_number = Decimal(str(period))
    except InvalidOperation as exc:
        raise ValueError("period must be a finite non-negative integer") from exc
    if not period_number.is_finite() or period_number < 0 or period_number != period_number.to_integral_value():
        raise ValueError("period must be a finite non-negative integer")
    period = int(period_number)
    if Decimal(str(lump_sum)) < 0:
        raise ValueError("lump_sum must be non-negative")
    before = outstanding_balance(principal, annual_rate, years, period, payments_per_year=payments_per_year)
    lump = min(Decimal(str(lump_sum)), before)
    after = before - lump
    remaining = max(0, _period_count(years, payments_per_year) - period)
    payment = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    rate = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))

    def remaining_interest(balance):
        total = Decimal(0)
        for i in range(remaining):
            if balance <= 0:
                break
            interest = balance * rate
            total += interest
            principal_part = min(payment - interest, balance)
            if i == remaining - 1:
                principal_part = balance
            balance -= principal_part
        return total

    out = {
        "original_balance": before,
        "lump_sum": lump,
        "new_balance": after,
        "interest_saved": remaining_interest(before) - remaining_interest(after),
    }
    return _quantize_dict(out, ndigits)


def recast_payment(principal, annual_rate, years, lump_sum, period, *, payments_per_year=12, ndigits=None) -> Decimal:
    """New monthly payment after lump_sum prepayment, keeping original term."""
    bal_before = outstanding_balance(principal, annual_rate, years, period, payments_per_year=payments_per_year)
    lump = Decimal(str(lump_sum))
    new_balance = bal_before - lump
    if new_balance <= 0:
        return _quantize(Decimal(0), ndigits)
    n_total = _period_count(years, payments_per_year)
    remaining = max(1, n_total - period)
    remaining_years = Decimal(remaining) / Decimal(str(payments_per_year))
    return monthly_payment(new_balance, annual_rate, remaining_years, payments_per_year=payments_per_year, ndigits=ndigits)


def extra_payment_schedule(principal, annual_rate, years, extra, *, payments_per_year=12, ndigits=None):
    """Return payment rows with extra principal each period until payoff."""
    n = _period_count(years, payments_per_year)
    pmt = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    extra_d = Decimal(str(extra))
    if extra_d < 0:
        raise ValueError("extra must be non-negative")
    balance = Decimal(str(principal))
    rate = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    rows = []
    for period in range(1, n + 1):
        if balance <= 0:
            break
        interest = balance * rate
        regular_principal = pmt - interest
        principal_part = min(regular_principal + extra_d, balance)
        if period == n:
            principal_part = balance
        actual_extra = min(extra_d, max(Decimal(0), principal_part - regular_principal))
        balance -= principal_part
        rows.append(_quantize_dict({
            "period": Decimal(period),
            "payment": interest + principal_part,
            "interest": interest,
            "principal": principal_part,
            "balance": balance,
            "extra": actual_extra,
        }, ndigits))
    return rows


def extra_payment_summary(principal, annual_rate, years, extra, *, payments_per_year=12, ndigits=None):
    """Summary of extra payments; extra_payment_schedule retains its list API."""
    original = amortization_schedule(principal, annual_rate, years, payments_per_year)
    revised = extra_payment_schedule(principal, annual_rate, years, extra, payments_per_year=payments_per_year)
    payment = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    original_interest = sum((row["interest"] for row in original), Decimal(0))
    new_interest = sum((row["interest"] for row in revised), Decimal(0))
    return _quantize_dict({
        "original_payment": payment,
        "new_payment": payment + Decimal(str(extra)),
        "original_periods": Decimal(len(original)),
        "new_periods": Decimal(len(revised)),
        "original_interest": original_interest,
        "new_interest": new_interest,
        "interest_saved": original_interest - new_interest,
    }, ndigits)

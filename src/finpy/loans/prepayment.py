"""Loan prepayment scenarios.

Tests use:
    apply_prepayment(principal, rate, years, prepay_amount, period, *, ndigits)
        -> {"balance_before", "prepayment", "balance_after"}
    apply_lump_sum(principal, rate, years, lump, period, *, ndigits)
        -> {"original_balance", "lump_sum", "new_balance", "interest_saved"}
    recast_payment(principal, rate, years, lump, period, *, ndigits) -> Decimal
    extra_payment_schedule(principal, rate, years, extra) -> list[dict]
"""

from decimal import Decimal, ROUND_HALF_UP

from finpy.loans.schedule import (
    monthly_payment,
    outstanding_balance,
    total_interest,
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
    """Apply a lump-sum prepayment and report interest savings.

    Interest saved is computed by comparing total interest of the original
    schedule to the total interest if the loan were re-amortised at the
    reduced balance over the remaining periods at the same payment.
    """
    pv = Decimal(str(principal))
    lump = Decimal(str(lump_sum))
    bal_before = outstanding_balance(principal, annual_rate, years, period, payments_per_year=payments_per_year)
    new_balance = bal_before - lump
    if new_balance < 0:
        lump = bal_before
        new_balance = Decimal(0)

    # Interest saved estimate: original total interest minus
    # interest_paid_so_far minus interest on new (smaller) balance over remaining periods at same monthly payment.
    n_total = int(years * payments_per_year)
    remaining = max(0, n_total - period)
    pmt = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    # interest paid in first `period` payments = period*pmt - (pv - bal_before)
    interest_so_far = pmt * Decimal(period) - (pv - bal_before)
    # remaining interest had we not prepaid
    remaining_interest_no_lump = pmt * Decimal(remaining) - bal_before
    if remaining_interest_no_lump < 0:
        remaining_interest_no_lump = Decimal(0)
    # remaining interest with lump: payment stays, but balance is smaller — payoff sooner; treat saved interest as the difference between bal_before and new_balance projected over remaining periods at rate.
    if new_balance == 0:
        interest_saved = remaining_interest_no_lump
    else:
        r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
        # interest you'd still pay on new_balance over `remaining` periods (very rough)
        remaining_interest_with_lump = pmt * Decimal(remaining) - new_balance
        if remaining_interest_with_lump < 0:
            remaining_interest_with_lump = Decimal(0)
        interest_saved = remaining_interest_no_lump - remaining_interest_with_lump
        if interest_saved < 0:
            interest_saved = Decimal(0)

    out = {
        "original_balance": bal_before,
        "lump_sum": lump,
        "new_balance": new_balance,
        "interest_saved": interest_saved,
    }
    return _quantize_dict(out, ndigits)


def recast_payment(principal, annual_rate, years, lump_sum, period, *, payments_per_year=12, ndigits=None) -> Decimal:
    """New monthly payment after lump_sum prepayment, keeping original term."""
    bal_before = outstanding_balance(principal, annual_rate, years, period, payments_per_year=payments_per_year)
    lump = Decimal(str(lump_sum))
    new_balance = bal_before - lump
    if new_balance <= 0:
        return _quantize(Decimal(0), ndigits)
    n_total = int(years * payments_per_year)
    remaining = max(1, n_total - period)
    remaining_years = Decimal(remaining) / Decimal(str(payments_per_year))
    return monthly_payment(float(new_balance), annual_rate, float(remaining_years), payments_per_year=payments_per_year, ndigits=ndigits)


def extra_payment_schedule(principal, annual_rate, years, extra, *, payments_per_year=12):
    """Schedule with an additional `extra` paid every period until payoff."""
    schedule = amortization_schedule(principal, annual_rate, years, payments_per_year=payments_per_year)
    pmt = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    extra_d = Decimal(str(extra))
    out = []
    balance = Decimal(str(principal))
    r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    period = 0
    while balance > 0 and period < len(schedule) * 2:  # safety bound
        period += 1
        interest = balance * r
        principal_part = pmt - interest + extra_d
        if principal_part > balance:
            principal_part = balance
        balance -= principal_part
        if balance < 0:
            balance = Decimal(0)
        out.append({
            "period": Decimal(period),
            "payment": pmt + extra_d if balance > 0 else interest + principal_part,
            "interest": interest,
            "principal": principal_part,
            "balance": balance,
            "extra": extra_d if balance > 0 else Decimal(0),
        })
    return out

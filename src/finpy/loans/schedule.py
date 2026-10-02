"""Loan schedule + payment helpers.

Tests use signatures of the form (principal, rate, years, *, payments_per_year)
or (principal, rate, years, period, *, ndigits) — all annual rate, "years"
counted in years, monthly payments by default.
"""

from decimal import Decimal, ROUND_HALF_UP


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)



def _period_count(years, payments_per_year):
    frequency = Decimal(str(payments_per_year))
    duration = Decimal(str(years))
    if not frequency.is_finite() or frequency <= 0 or frequency != int(frequency):
        raise ValueError("payments_per_year must be a positive integer")
    if not duration.is_finite() or duration <= 0:
        raise ValueError("years must be positive and finite")
    count = duration * frequency
    nearest = count.to_integral_value(rounding=ROUND_HALF_UP)
    # Recover an integer period count after decimal or binary division by m.
    n = int(nearest if abs(count - nearest) <= Decimal("1e-12") else count)
    if n <= 0:
        raise ValueError("term must contain at least one payment period")
    return n


def amortization_schedule(principal, annual_rate, years, payments_per_year=12, *, ndigits=None):
    n = _period_count(years, payments_per_year)
    r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    pv = Decimal(str(principal))
    one = Decimal(1)
    if r == 0:
        pmt = pv / Decimal(str(n))
    else:
        pmt = pv * r * (one + r) ** n / ((one + r) ** n - one)
    schedule = []
    balance = pv
    for period in range(1, n + 1):
        interest = balance * r
        principal_part = pmt - interest
        balance -= principal_part
        if period == n:
            principal_part += balance
            interest = Decimal(0) if r == 0 else interest
            pmt_row = principal_part + interest
            balance = Decimal(0)
        else:
            pmt_row = pmt
        if balance < 0:
            balance = Decimal(0)
        entry = {
            "period": Decimal(str(period)),
            "payment": pmt_row,
            "interest": interest,
            "principal": principal_part,
            "balance": balance,
        }
        if ndigits is not None:
            entry = {k: v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP) for k, v in entry.items()}
        schedule.append(entry)
    return schedule


def monthly_payment(principal, annual_rate, years, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Standard mortgage-style payment formula."""
    n = Decimal(str(_period_count(years, payments_per_year)))
    r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    pv = Decimal(str(principal))
    one = Decimal(1)
    if r == 0:
        return _quantize(pv / n, ndigits)
    pmt = pv * r * (one + r) ** n / ((one + r) ** n - one)
    return _quantize(pmt, ndigits)


def outstanding_balance(principal, annual_rate, years, period, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Remaining balance after `period` payments (0..n)."""
    n = _period_count(years, payments_per_year)
    if period < 0:
        raise ValueError("period must be non-negative")
    if period >= n:
        return _quantize(Decimal(0), ndigits)
    r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    pv = Decimal(str(principal))
    one = Decimal(1)
    if r == 0:
        # linear amortization
        pmt = pv / Decimal(n)
        bal = pv - pmt * Decimal(period)
        if bal < 0:
            bal = Decimal(0)
        return _quantize(bal, ndigits)
    pmt = pv * r * (one + r) ** n / ((one + r) ** n - one)
    # closed-form remaining balance
    bal = pv * (one + r) ** Decimal(period) - pmt * (((one + r) ** Decimal(period) - one) / r)
    if bal < 0:
        bal = Decimal(0)
    return _quantize(bal, ndigits)


def total_interest(principal, annual_rate, years, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Sum of all interest paid over the life of the loan."""
    n = _period_count(years, payments_per_year)
    pmt = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    return _quantize(pmt * Decimal(n) - Decimal(str(principal)), ndigits)


def interest_only_payment(principal, annual_rate, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Interest-only payment per period: principal * rate / payments_per_year."""
    pv = Decimal(str(principal))
    r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    return _quantize(pv * r, ndigits)


def balloon_payment(principal, annual_rate, balloon_years, full_term_years, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Balloon payment — outstanding balance at end of `balloon_years`."""
    if balloon_years >= full_term_years:
        return _quantize(Decimal(0), ndigits)
    period = _period_count(balloon_years, payments_per_year) if balloon_years > 0 else 0
    return outstanding_balance(principal, annual_rate, full_term_years, period, payments_per_year=payments_per_year, ndigits=ndigits)


def apr_from_apy(apy, payments_per_year, *, ndigits=None) -> Decimal:
    """Convert APY (effective annual yield) to nominal APR."""
    apy_d = Decimal(str(apy))
    m = Decimal(str(payments_per_year))
    one = Decimal(1)
    if apy_d <= -1:
        raise ValueError("apy must exceed -1")
    if m <= 0:
        raise ValueError("payments_per_year must be positive")
    apr = m * ((one + apy_d) ** (one / m) - one)
    return _quantize(apr, ndigits)


def apy_from_apr(apr, payments_per_year, *, ndigits=None) -> Decimal:
    """Convert nominal APR to APY (effective annual yield)."""
    apr_d = Decimal(str(apr))
    m = Decimal(str(payments_per_year))
    one = Decimal(1)
    if apr_d <= -m:
        raise ValueError("apr too negative")
    apy = (one + apr_d / m) ** m - one
    return _quantize(apy, ndigits)


def loan_payoff_time(principal, annual_rate, payment, payments_per_year=12, *, ndigits=None) -> Decimal:
    """Number of periods to pay off `principal` at constant `payment`."""
    pv = Decimal(str(principal))
    p = Decimal(str(payment))
    r = Decimal(str(annual_rate)) / Decimal(str(payments_per_year))
    one = Decimal(1)
    if p <= 0:
        raise ValueError("payment must be positive")
    if r == 0:
        if p == 0:
            raise ValueError("undefined for zero payment and zero rate")
        return _quantize(pv / p, ndigits)
    if p <= pv * r:
        raise ValueError("payment too small to amortize at this rate")
    if one + r <= 0:
        raise ValueError("periodic rate must exceed -1")
    n = -(one - pv * r / p).ln() / (one + r).ln()
    return _quantize(n, ndigits)


def amortization_summary(principal, annual_rate, years, payments_per_year=12, *, ndigits=None) -> dict:
    """Aggregate the unrounded schedule; keep original keys and add aliases."""
    rows = amortization_schedule(principal, annual_rate, years, payments_per_year)
    pmt = monthly_payment(principal, annual_rate, years, payments_per_year=payments_per_year)
    paid = sum((row["payment"] for row in rows), Decimal(0))
    interest = sum((row["interest"] for row in rows), Decimal(0))
    n = Decimal(len(rows))
    out = {
        "principal": Decimal(str(principal)),
        "monthly_payment": pmt,
        "total_payments": paid,
        "total_paid": paid,
        "total_interest": interest,
        "first_year_interest": sum((row["interest"] for row in rows[:int(payments_per_year)]), Decimal(0)),
        "n_periods": n,
        "num_payments": n,
    }
    return {k: _quantize(v, ndigits) for k, v in out.items()}

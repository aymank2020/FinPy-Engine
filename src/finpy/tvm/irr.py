from decimal import Decimal, ROUND_HALF_UP, DecimalException
from typing import Optional
from datetime import date
from finpy.core.errors import NoSolutionFoundError


def irr(cash_flows: list[float], guess: float = 0.1, max_iter: int = 1000, tol: float = 1e-10, *, ndigits: Optional[int] = None) -> Decimal:
    rate = Decimal(str(guess))
    one = Decimal(1)
    for _ in range(max_iter):
        npv = Decimal(0)
        dnpv = Decimal(0)
        for t, cf in enumerate(cash_flows):
            cf_dec = Decimal(str(cf))
            denom = (one + rate) ** Decimal(str(t))
            npv += cf_dec / denom
            if t > 0 and cf_dec != 0:
                try:
                    dnpv -= Decimal(str(t)) * cf_dec / ((one + rate) ** Decimal(str(t + 1)))
                except (Overflow, DecimalException):
                    pass
        if abs(npv) < Decimal(str(tol)):
            if ndigits is not None:
                rate = rate.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
            return rate
        if dnpv == 0:
            break
        rate -= npv / dnpv
        if rate < -one + Decimal("1e-10") or rate > Decimal("1e6"):
            break
    raise NoSolutionFoundError("IRR did not converge")


def _calculate_xnpv(rate: Decimal, cash_flows: list[float], dates: list[date]) -> Decimal:
    one = Decimal(1)
    base_date = dates[0]
    result = Decimal(0)
    for cf, d in zip(cash_flows, dates):
        days = (d - base_date).days
        year_frac = Decimal(str(days)) / Decimal("365")
        result += Decimal(str(cf)) / (one + rate) ** year_frac
    return result


def xirr(cash_flows: list[float], dates: list[date], guess: float = 0.1, max_iter: int = 1000, tol: float = 1e-10, *, ndigits: Optional[int] = None) -> Decimal:
    if len(cash_flows) != len(dates):
        raise ValueError("cash_flows and dates must have the same length")
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows")
    if sum(1 for cf in cash_flows if cf > 0) == 0 or sum(1 for cf in cash_flows if cf < 0) == 0:
        raise ValueError("Must have both positive and negative cash flows")
    rate = Decimal(str(guess))
    one = Decimal(1)
    for _ in range(max_iter):
        npv_val = Decimal(0)
        dnpv = Decimal(0)
        base_date = dates[0]
        for cf, d in zip(cash_flows, dates):
            cf_dec = Decimal(str(cf))
            days = (d - base_date).days
            year_frac = Decimal(str(days)) / Decimal("365")
            denom = (one + rate) ** year_frac
            npv_val += cf_dec / denom
            try:
                dnpv -= year_frac * cf_dec / ((one + rate) ** (year_frac + one))
            except (Overflow, DecimalException):
                pass
        if abs(npv_val) < Decimal(str(tol)):
            if ndigits is not None:
                rate = rate.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
            return rate
        if dnpv == 0:
            break
        rate -= npv_val / dnpv
        if rate < -one + Decimal("1e-10") or rate > Decimal("1e6"):
            break
    raise NoSolutionFoundError("XIRR did not converge")


def modified_irr_with_reinvestment(cash_flows: list[float], finance_rate: float, reinvest_rate: float, *, ndigits: Optional[int] = None) -> Decimal:
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows")
    has_negative = any(cf < 0 for cf in cash_flows)
    has_positive = any(cf > 0 for cf in cash_flows)
    if not has_negative or not has_positive:
        raise ValueError("Must have both positive and negative cash flows")
    finance_dec = Decimal(str(finance_rate))
    reinvest_dec = Decimal(str(reinvest_rate))
    one = Decimal(1)
    n = len(cash_flows)
    pv_neg = Decimal(0)
    fv_pos = Decimal(0)
    for t, cf in enumerate(cash_flows):
        cf_dec = Decimal(str(cf))
        if cf_dec < 0:
            pv_neg += cf_dec / (one + finance_dec) ** Decimal(str(t))
        elif cf_dec > 0:
            fv_pos += cf_dec * (one + reinvest_dec) ** Decimal(str(n - 1 - t))
    if pv_neg == 0:
        raise ValueError("No negative cash flows to discount")
    mirr_val = (fv_pos / -pv_neg) ** (Decimal(1) / Decimal(str(n - 1))) - one
    if ndigits is not None:
        mirr_val = mirr_val.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return mirr_val


def irr_with_bisection(cash_flows: list[float], low: float = -0.99, high: float = 10.0, max_iter: int = 1000, tol: float = 1e-10, *, ndigits: Optional[int] = None) -> Decimal:
    one = Decimal(1)
    low_dec = Decimal(str(low))
    high_dec = Decimal(str(high))
    npv_low = Decimal(0)
    for t, cf in enumerate(cash_flows):
        npv_low += Decimal(str(cf)) / (one + low_dec) ** Decimal(str(t))
    npv_high = Decimal(0)
    for t, cf in enumerate(cash_flows):
        npv_high += Decimal(str(cf)) / (one + high_dec) ** Decimal(str(t))
    if npv_low == 0:
        if ndigits is not None:
            low_dec = low_dec.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
        return low_dec
    if npv_high == 0:
        if ndigits is not None:
            high_dec = high_dec.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
        return high_dec
    if npv_low * npv_high > 0:
        raise NoSolutionFoundError("IRR with bisection: no sign change in interval")
    for _ in range(max_iter):
        mid = (low_dec + high_dec) / Decimal(2)
        npv_mid = Decimal(0)
        for t, cf in enumerate(cash_flows):
            npv_mid += Decimal(str(cf)) / (one + mid) ** Decimal(str(t))
        if abs(npv_mid) < Decimal(str(tol)):
            if ndigits is not None:
                mid = mid.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
            return mid
        if npv_low * npv_mid > 0:
            low_dec = mid
            npv_low = npv_mid
        else:
            high_dec = mid
            npv_high = npv_mid
        if high_dec - low_dec < Decimal(str(tol)):
            mid = (low_dec + high_dec) / Decimal(2)
            if ndigits is not None:
                mid = mid.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
            return mid
    raise NoSolutionFoundError("IRR with bisection did not converge")


def irr_npv_profile(cash_flows: list[float], low_rate: float = -0.5, high_rate: float = 5.0, steps: int = 100, *, ndigits: Optional[int] = None) -> list[tuple[Decimal, Decimal]]:
    one = Decimal(1)
    low = Decimal(str(low_rate))
    high = Decimal(str(high_rate))
    step_size = (high - low) / Decimal(str(steps))
    profile = []
    for i in range(steps + 1):
        rate = low + step_size * Decimal(str(i))
        npv_val = Decimal(0)
        for t, cf in enumerate(cash_flows):
            npv_val += Decimal(str(cf)) / (one + rate) ** Decimal(str(t))
        if ndigits is not None:
            npv_val = npv_val.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
            rate_r = rate.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
        else:
            rate_r = rate
        profile.append((rate_r, npv_val))
    return profile


def multiple_irr_check(cash_flows: list[float], guesses: Optional[list[float]] = None, max_iter: int = 1000, tol: float = 1e-10, *, ndigits: Optional[int] = None) -> list[Decimal]:
    if guesses is None:
        guesses = [0.1, 0.5, 1.0, 2.0, 5.0]
    results = []
    for g in guesses:
        try:
            result = irr(cash_flows, guess=g, max_iter=max_iter, tol=tol, ndigits=ndigits)
            rounded = result.quantize(Decimal("0.00000001"))
            already_found = any(abs(rounded - r) < Decimal("0.000001") for r in results)
            if not already_found:
                results.append(result)
        except (NoSolutionFoundError, ValueError, ArithmeticError):
            continue
    if not results:
        raise NoSolutionFoundError("No IRR found from any starting guess")
    return results


def irr_approximate(cash_flows: list[float]) -> Decimal:
    n = len(cash_flows)
    total_inflow = Decimal(0)
    total_outflow = Decimal(0)
    for cf in cash_flows:
        val = Decimal(str(cf))
        if val > 0:
            total_inflow += val
        else:
            total_outflow += abs(val)
    if total_outflow == 0:
        return Decimal(0)
    if total_inflow <= total_outflow:
        return Decimal(0)
    ratio = total_inflow / total_outflow
    one = Decimal(1)
    return ratio ** (one / Decimal(n)) - one


def irr_annual(cash_flows: list[float], guess: float = 0.1) -> Decimal:
    return irr(cash_flows, guess)


def irr_semi_annual(cash_flows_per_period: list[float], guess: float = 0.1) -> Decimal:
    periodic_rate = irr(cash_flows_per_period, guess)
    return (Decimal(1) + periodic_rate) ** 2 - Decimal(1)


def irr_monthly(cash_flows_per_period: list[float], guess: float = 0.1) -> Decimal:
    periodic_rate = irr(cash_flows_per_period, guess)
    return (Decimal(1) + periodic_rate) ** 12 - Decimal(1)

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional


def mirr(cash_flows: list[float], finance_rate: float, reinvest_rate: float, *, ndigits: Optional[int] = None) -> Decimal:
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows")
    has_positive = any(cf > 0 for cf in cash_flows)
    has_negative = any(cf < 0 for cf in cash_flows)
    if not has_positive or not has_negative:
        raise ValueError("MIRR requires both positive and negative cash flows")
    if finance_rate < -1:
        raise ValueError("Finance rate cannot be less than -100%")
    if reinvest_rate < -1:
        raise ValueError("Reinvest rate cannot be less than -100%")
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
    if fv_pos == 0:
        raise ValueError("No positive cash flows to compound")
    try:
        ratio = fv_pos / -pv_neg
        if ratio <= 0:
            raise ValueError("Invalid ratio for MIRR calculation")
        exponent = Decimal(1) / Decimal(str(n - 1))
        result = ratio ** exponent - one
    except (InvalidOperation, OverflowError, ZeroDivisionError):
        raise ValueError("MIRR calculation produced an invalid result")
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def mirr_with_terminal_growth(cash_flows: list[float], finance_rate: float, reinvest_rate: float, terminal_growth: float = 0.0, *, ndigits: Optional[int] = None) -> Decimal:
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows")
    finance_dec = Decimal(str(finance_rate))
    reinvest_dec = Decimal(str(reinvest_rate))
    growth_dec = Decimal(str(terminal_growth))
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
    if fv_pos == 0:
        raise ValueError("No positive cash flows to compound")
    fv_pos = fv_pos * (one + growth_dec)
    ratio = fv_pos / -pv_neg
    if ratio <= 0:
        raise ValueError("Invalid ratio for MIRR calculation")
    exponent = Decimal(1) / Decimal(str(n - 1))
    result = ratio ** exponent - one
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def mirr_from_separate_cashflows(positive_cash_flows: list[float], negative_cash_flows: list[float], finance_rate: float, reinvest_rate: float, *, ndigits: Optional[int] = None) -> Decimal:
    if len(positive_cash_flows) < 1 or len(negative_cash_flows) < 1:
        raise ValueError("Must have at least one positive and one negative cash flow")
    finance_dec = Decimal(str(finance_rate))
    reinvest_dec = Decimal(str(reinvest_rate))
    one = Decimal(1)
    n_pos = len(positive_cash_flows)
    n_neg = len(negative_cash_flows)
    total_periods = n_pos + n_neg - 1
    pv_neg = Decimal(0)
    for t, cf in enumerate(negative_cash_flows):
        pv_neg += Decimal(str(cf)) / (one + finance_dec) ** Decimal(str(t))
    fv_pos = Decimal(0)
    for t, cf in enumerate(positive_cash_flows):
        fv_pos += Decimal(str(cf)) * (one + reinvest_dec) ** Decimal(str(n_pos - 1 - t))
    if pv_neg == 0:
        raise ValueError("No negative cash flows to discount")
    if fv_pos == 0:
        raise ValueError("No positive cash flows to compound")
    ratio = fv_pos / -pv_neg
    if ratio <= 0:
        raise ValueError("Invalid ratio for MIRR calculation")
    exponent = Decimal(1) / Decimal(str(total_periods))
    result = ratio ** exponent - one
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def mirr_with_periodic_rates(cash_flows: list[float], finance_rate: float, reinvest_rate: float, payments_per_year: int = 1, *, ndigits: Optional[int] = None) -> Decimal:
    if payments_per_year <= 0:
        raise ValueError("payments_per_year must be positive")
    periodic_finance = Decimal(str(finance_rate)) / Decimal(payments_per_year)
    periodic_reinvest = Decimal(str(reinvest_rate)) / Decimal(payments_per_year)
    return mirr(cash_flows, float(periodic_finance), float(periodic_reinvest), ndigits=ndigits)


def mirr_with_investment_timing(cash_flows: list[float], finance_rate: float, reinvest_rate: float, investment_timing: list[float], *, ndigits: Optional[int] = None) -> Decimal:
    if len(cash_flows) != len(investment_timing):
        raise ValueError("cash_flows and investment_timing must have same length")
    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows")
    finance_dec = Decimal(str(finance_rate))
    reinvest_dec = Decimal(str(reinvest_rate))
    one = Decimal(1)
    n = len(cash_flows)
    last_time = Decimal(str(investment_timing[-1]))
    pv_neg = Decimal(0)
    fv_pos = Decimal(0)
    for t, cf in enumerate(cash_flows):
        cf_dec = Decimal(str(cf))
        time = Decimal(str(investment_timing[t]))
        if cf_dec < 0:
            pv_neg += cf_dec / (one + finance_dec) ** time
        elif cf_dec > 0:
            remaining = last_time - time
            fv_pos += cf_dec * (one + reinvest_dec) ** remaining
    if pv_neg == 0:
        raise ValueError("No negative cash flows to discount")
    if fv_pos == 0:
        raise ValueError("No positive cash flows to compound")
    ratio = fv_pos / -pv_neg
    if ratio <= 0:
        raise ValueError("Invalid ratio for MIRR calculation")
    exponent = Decimal(1) / last_time
    result = ratio ** exponent - one
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result

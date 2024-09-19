from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from finpy.core.errors import UnknownCurrencyError
from finpy.fx.iso4217 import is_valid_currency


def convert_spot(amount: float, from_currency: str, to_currency: str, rate: float, *, ndigits: Optional[int] = None) -> Decimal:
    if not is_valid_currency(from_currency):
        raise UnknownCurrencyError(f"Unknown currency: {from_currency}")
    if not is_valid_currency(to_currency):
        raise UnknownCurrencyError(f"Unknown currency: {to_currency}")
    result = Decimal(str(amount)) * Decimal(str(rate))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def convert_bid_ask(amount: float, from_currency: str, to_currency: str, bid_rate: float, ask_rate: float, *, ndigits: Optional[int] = None) -> dict[str, Decimal]:
    if not is_valid_currency(from_currency):
        raise UnknownCurrencyError(f"Unknown currency: {from_currency}")
    if not is_valid_currency(to_currency):
        raise UnknownCurrencyError(f"Unknown currency: {to_currency}")
    if bid_rate > ask_rate:
        raise ValueError(f"bid_rate ({bid_rate}) cannot exceed ask_rate ({ask_rate})")
    amt = Decimal(str(amount))
    bid_result = amt * Decimal(str(bid_rate))
    ask_result = amt * Decimal(str(ask_rate))
    mid = (bid_result + ask_result) / Decimal(2)
    spread = ask_result - bid_result
    result = {"bid": bid_result, "ask": ask_result, "mid": mid, "spread": spread}
    if ndigits is not None:
        result = {k: v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP) for k, v in result.items()}
    return result


def cross_rate(rate_a: float, rate_b: float, base_currency: str, quote_currency: str, target_currency: str, *, ndigits: Optional[int] = None) -> Decimal:
    from finpy.fx.iso4217 import is_valid_currency
    if not is_valid_currency(base_currency):
        raise UnknownCurrencyError(f"Unknown currency: {base_currency}")
    if not is_valid_currency(quote_currency):
        raise UnknownCurrencyError(f"Unknown currency: {quote_currency}")
    if not is_valid_currency(target_currency):
        raise UnknownCurrencyError(f"Unknown currency: {target_currency}")
    r_a = Decimal(str(rate_a))
    r_b = Decimal(str(rate_b))
    result = r_a / r_b
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def inverse_rate(rate: float, *, ndigits: Optional[int] = None) -> Decimal:
    if rate <= 0:
        raise ValueError(f"rate must be positive, got {rate}")
    result = Decimal(1) / Decimal(str(rate))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def pips_to_points(rate: float, pips: float) -> Decimal:
    return Decimal(str(rate)) + Decimal(str(pips)) / Decimal(10000)


def points_to_pips(larger_rate: float, smaller_rate: float) -> Decimal:
    return (Decimal(str(larger_rate)) - Decimal(str(smaller_rate))) * Decimal(10000)


def midpoint_rate(bid: float, ask: float, *, ndigits: Optional[int] = None) -> Decimal:
    if bid > ask:
        raise ValueError(f"bid ({bid}) cannot exceed ask ({ask})")
    result = (Decimal(str(bid)) + Decimal(str(ask))) / Decimal(2)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def is_positive_carry(short_rate: float, long_rate: float) -> bool:
    return long_rate > short_rate


def forward_points(spot_rate: float, forward_rate_val: float, *, ndigits: Optional[int] = None) -> Decimal:
    result = (Decimal(str(forward_rate_val)) - Decimal(str(spot_rate))) * Decimal(10000)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result

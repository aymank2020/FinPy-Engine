"""Core domain dataclasses used throughout finpy.

The dataclasses follow a uniform style: ``frozen=True``, ``slots=True``,
explicit ``__post_init__`` validation, and ``to_dict``/``from_dict`` helpers
for serialisation. Equality semantics are tailored per type (some compare on
identity-like keys such as ``trade_id`` or ``symbol``; others compare on all
fields). Methods that perform numerical work use :class:`Decimal` for exact
arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


FXHistory = dict[str, dict[str, Decimal]]


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class Cashflow:
    amount: Decimal
    t: float

    def __post_init__(self) -> None:
        if self.t < 0:
            raise ValueError("Cashflow time t must be non-negative")

    def is_zero(self) -> bool:
        return self.amount == Decimal(0)

    def discounted(self, rate: Decimal, mode: str = "discrete") -> Decimal:
        rate = _to_decimal(rate)
        if mode == "continuous":
            from math import exp
            factor = Decimal(str(exp(-float(rate) * float(self.t))))
            return self.amount * factor
        # discrete: amount / (1 + rate)^t
        factor = (Decimal(1) + rate) ** Decimal(str(self.t))
        return self.amount / factor

    def to_dict(self) -> dict[str, Any]:
        return {"amount": str(self.amount), "t": self.t}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Cashflow":
        return cls(amount=Decimal(str(d["amount"])), t=float(d["t"]))

    def __repr__(self) -> str:
        return f"Cashflow(amount={self.amount}, t={self.t})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cashflow):
            return NotImplemented
        return self.amount == other.amount and self.t == other.t

    def __hash__(self) -> int:
        return hash((self.amount, self.t))


@dataclass(frozen=True, slots=True)
class Instrument:
    face_value: Decimal
    coupon_rate: Decimal
    maturity_years: float
    payments_per_year: int = 2

    def __post_init__(self) -> None:
        if self.face_value <= 0:
            raise ValueError("face_value must be positive")
        if self.coupon_rate < 0:
            raise ValueError("coupon_rate must be non-negative")
        if self.maturity_years <= 0:
            raise ValueError("maturity_years must be positive")
        if self.payments_per_year not in (1, 2, 4, 12):
            raise ValueError("payments_per_year must be one of 1, 2, 4, 12")

    def coupon_amount(self) -> Decimal:
        return self.face_value * self.coupon_rate / Decimal(self.payments_per_year)

    def total_payments(self) -> int:
        return int(round(self.maturity_years * self.payments_per_year))

    def cashflows(self) -> list[Cashflow]:
        n = self.total_payments()
        coupon = self.coupon_amount()
        out: list[Cashflow] = []
        step = 1.0 / self.payments_per_year
        for i in range(1, n + 1):
            t = i * step
            amt = coupon + self.face_value if i == n else coupon
            out.append(Cashflow(amount=amt, t=t))
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "face_value": str(self.face_value),
            "coupon_rate": str(self.coupon_rate),
            "maturity_years": self.maturity_years,
            "payments_per_year": self.payments_per_year,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Instrument":
        return cls(
            face_value=Decimal(str(d["face_value"])),
            coupon_rate=Decimal(str(d["coupon_rate"])),
            maturity_years=float(d["maturity_years"]),
            payments_per_year=int(d.get("payments_per_year", 2)),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Instrument):
            return NotImplemented
        return (
            self.face_value == other.face_value
            and self.coupon_rate == other.coupon_rate
            and self.maturity_years == other.maturity_years
            and self.payments_per_year == other.payments_per_year
        )

    def __hash__(self) -> int:
        return hash((self.face_value, self.coupon_rate, self.maturity_years, self.payments_per_year))


@dataclass(frozen=True, slots=True)
class YieldCurve:
    rates: dict[float, Decimal]

    def __post_init__(self) -> None:
        if not self.rates:
            raise ValueError("YieldCurve requires at least one rate")

    def tenors(self) -> list[float]:
        return sorted(self.rates.keys())

    def interpolate(self, t: float) -> Decimal:
        ts = self.tenors()
        if t <= ts[0]:
            return self.rates[ts[0]]
        if t >= ts[-1]:
            return self.rates[ts[-1]]
        # linear interpolation between bracket points
        for i in range(len(ts) - 1):
            lo, hi = ts[i], ts[i + 1]
            if lo <= t <= hi:
                r_lo = self.rates[lo]
                r_hi = self.rates[hi]
                frac = Decimal(str((t - lo) / (hi - lo)))
                return r_lo + (r_hi - r_lo) * frac
        return self.rates[ts[-1]]

    def discount_factor(self, t: float) -> Decimal:
        rate = self.interpolate(t)
        from math import exp; return Decimal(str(exp(-float(rate) * t)))

    def parallel_shift(self, basis_points: Decimal) -> "YieldCurve":
        bps = _to_decimal(basis_points)
        delta = bps / Decimal(10000)
        new_rates = {tenor: r + delta for tenor, r in self.rates.items()}
        return YieldCurve(rates=new_rates)

    def to_dict(self) -> dict[str, Any]:
        return {"rates": {str(t): str(r) for t, r in self.rates.items()}}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "YieldCurve":
        rates = {float(k): Decimal(str(v)) for k, v in d["rates"].items()}
        return cls(rates=rates)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, YieldCurve):
            return NotImplemented
        return self.rates == other.rates

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.rates.items())))


@dataclass(frozen=True, slots=True)
class ReturnSeries:
    values: list[Decimal]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("ReturnSeries requires at least two values")
        if len(self.values) < 2:
            raise ValueError("ReturnSeries requires at least two values")

    def total_return(self) -> Decimal:
        product = Decimal(1)
        for r in self.values:
            product *= Decimal(1) + r
        return product - Decimal(1)

    def arithmetic_mean(self) -> Decimal:
        return sum(self.values, Decimal(0)) / Decimal(len(self.values))

    def geometric_mean(self) -> Decimal:
        n = len(self.values)
        product = Decimal(1)
        for r in self.values:
            product *= Decimal(1) + r
        # compute (product)^(1/n) - 1 via float power, return Decimal
        from math import pow as fpow
        gm = Decimal(str(fpow(float(product), 1.0 / n))) - Decimal(1)
        return gm

    def variance(self, ddof: int = 1) -> Decimal:
        n = len(self.values)
        if n - ddof <= 0:
            raise ValueError("ddof too large for sample size")
        mean = self.arithmetic_mean()
        squared = sum((r - mean) ** 2 for r in self.values)
        return squared / Decimal(n - ddof)

    def std(self, ddof: int = 1) -> Decimal:
        var = self.variance(ddof=ddof)
        return Decimal(str(float(var) ** 0.5))

    def sharpe_ratio(self, risk_free: Decimal = Decimal(0)) -> Decimal:
        s = self.std()
        if s == 0:
            return Decimal(0)
        excess = self.arithmetic_mean() - _to_decimal(risk_free)
        return excess / s

    def max_drawdown(self) -> Decimal:
        peak = Decimal(1)
        cum = Decimal(1)
        max_dd = Decimal(0)
        for r in self.values:
            cum *= Decimal(1) + r
            if cum > peak:
                peak = cum
            dd = (peak - cum) / peak if peak != 0 else Decimal(0)
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def sortino_ratio(self, risk_free: Decimal = Decimal(0)) -> Decimal:
        rf = _to_decimal(risk_free)
        downside = [r for r in self.values if r < rf]
        if not downside:
            return Decimal(0)
        mean_excess = self.arithmetic_mean() - rf
        sq = sum((r - rf) ** 2 for r in downside)
        downside_dev = Decimal(str((float(sq) / len(downside)) ** 0.5))
        if downside_dev == 0:
            return Decimal(0)
        return mean_excess / downside_dev

    def to_dict(self) -> dict[str, Any]:
        return {"values": [str(v) for v in self.values]}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReturnSeries":
        return cls(values=[Decimal(str(v)) for v in d["values"]])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReturnSeries):
            return NotImplemented
        return self.values == other.values

    def __hash__(self) -> int:
        return hash(tuple(self.values))


@dataclass(frozen=True, slots=True)
class FXRate:
    currency_pair: str
    rate: Decimal
    as_of: str

    def __post_init__(self) -> None:
        if "/" not in self.currency_pair or len(self.currency_pair.split("/")) != 2:
            raise ValueError("currency_pair must be 'BASE/QUOTE'")
        base, quote = self.currency_pair.split("/")
        if len(base) != 3 or len(quote) != 3:
            raise ValueError("currency components must be 3 letters")
        if self.rate <= 0:
            raise ValueError("rate must be positive")

    def base_currency(self) -> str:
        return self.currency_pair.split("/")[0]

    def quote_currency(self) -> str:
        return self.currency_pair.split("/")[1]

    def convert(self, amount: Decimal) -> Decimal:
        return _to_decimal(amount) * self.rate

    def invert(self) -> "FXRate":
        new_pair = f"{self.quote_currency()}/{self.base_currency()}"
        return FXRate(
            currency_pair=new_pair,
            rate=Decimal(1) / self.rate,
            as_of=self.as_of,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency_pair": self.currency_pair,
            "rate": str(self.rate),
            "as_of": self.as_of,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FXRate":
        return cls(
            currency_pair=d["currency_pair"],
            rate=Decimal(str(d["rate"])),
            as_of=d["as_of"],
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FXRate):
            return NotImplemented
        return (
            self.currency_pair == other.currency_pair
            and self.rate == other.rate
            and self.as_of == other.as_of
        )

    def __hash__(self) -> int:
        return hash((self.currency_pair, self.rate, self.as_of))


@dataclass(frozen=True, slots=True)
class ScheduleRow:
    period: int
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "payment": str(self.payment),
            "interest": str(self.interest),
            "principal": str(self.principal),
            "balance": str(self.balance),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ScheduleRow":
        return cls(
            period=int(d["period"]),
            payment=Decimal(str(d["payment"])),
            interest=Decimal(str(d["interest"])),
            principal=Decimal(str(d["principal"])),
            balance=Decimal(str(d["balance"])),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScheduleRow):
            return NotImplemented
        return (
            self.period == other.period
            and self.payment == other.payment
            and self.interest == other.interest
            and self.principal == other.principal
            and self.balance == other.balance
        )

    def __hash__(self) -> int:
        return hash((self.period, self.payment, self.interest, self.principal, self.balance))


@dataclass(frozen=True, slots=True)
class Result:
    value: Decimal
    label: str = ""

    def __repr__(self) -> str:
        return f"Result(value={self.value}, label={self.label})"

    def __add__(self, other: "Result") -> "Result":
        if not isinstance(other, Result):
            return NotImplemented
        return Result(value=self.value + other.value, label=self.label)

    def __sub__(self, other: "Result") -> "Result":
        if not isinstance(other, Result):
            return NotImplemented
        return Result(value=self.value - other.value, label=self.label)

    def __mul__(self, factor: Decimal) -> "Result":
        return Result(value=self.value * _to_decimal(factor), label=self.label)

    def __truediv__(self, divisor: Decimal) -> "Result":
        d = _to_decimal(divisor)
        if d == 0:
            raise ZeroDivisionError("Result division by zero")
        return Result(value=self.value / d, label=self.label)

    def to_dict(self) -> dict[str, Any]:
        return {"value": str(self.value), "label": self.label}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Result":
        return cls(value=Decimal(str(d["value"])), label=d.get("label", ""))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Result):
            return NotImplemented
        return self.value == other.value and self.label == other.label

    def __hash__(self) -> int:
        return hash((self.value, self.label))


@dataclass(frozen=True, slots=True)
class MarketData:
    symbol: str
    price: Decimal
    volume: int | None = None
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must be a non-empty string")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume must be non-negative")

    def spread(self, bid: Decimal, ask: Decimal) -> Decimal:
        return _to_decimal(ask) - _to_decimal(bid)

    def mid_price(self, bid: Decimal, ask: Decimal) -> Decimal:
        return (_to_decimal(bid) + _to_decimal(ask)) / Decimal(2)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"symbol": self.symbol, "price": str(self.price)}
        if self.volume is not None:
            d["volume"] = self.volume
        if self.timestamp is not None:
            d["timestamp"] = self.timestamp
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MarketData":
        return cls(
            symbol=d["symbol"],
            price=Decimal(str(d["price"])),
            volume=d.get("volume"),
            timestamp=d.get("timestamp"),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MarketData):
            return NotImplemented
        return (
            self.symbol == other.symbol
            and self.price == other.price
            and self.volume == other.volume
            and self.timestamp == other.timestamp
        )

    def __hash__(self) -> int:
        return hash((self.symbol, self.price, self.volume, self.timestamp))


@dataclass(frozen=True, slots=True)
class Trade:
    trade_id: str
    symbol: str
    quantity: int
    price: Decimal
    trade_date: str
    trade_type: str = "buy"
    commission: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        if not self.trade_id:
            raise ValueError("trade_id must be non-empty")
        if not self.symbol:
            raise ValueError("symbol must be non-empty")
        if self.quantity == 0:
            raise ValueError("quantity must be non-zero")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.trade_type not in ("buy", "sell"):
            raise ValueError("trade_type must be 'buy' or 'sell'")
        if self.commission < 0:
            raise ValueError("commission must be non-negative")

    def notional(self) -> Decimal:
        return abs(Decimal(self.quantity) * self.price)

    def gross_value(self) -> Decimal:
        return Decimal(self.quantity) * self.price

    def is_buy(self) -> bool:
        return self.trade_type == "buy"

    def is_sell(self) -> bool:
        return self.trade_type == "sell"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "price": str(self.price),
            "trade_date": self.trade_date,
            "trade_type": self.trade_type,
            "commission": str(self.commission),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Trade":
        return cls(
            trade_id=d["trade_id"],
            symbol=d["symbol"],
            quantity=int(d["quantity"]),
            price=Decimal(str(d["price"])),
            trade_date=d["trade_date"],
            trade_type=d.get("trade_type", "buy"),
            commission=Decimal(str(d.get("commission", "0"))),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Trade):
            return NotImplemented
        return self.trade_id == other.trade_id

    def __hash__(self) -> int:
        return hash(self.trade_id)


@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    quantity: int
    cost_basis: Decimal
    current_price: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must be non-empty")
        if self.cost_basis < 0:
            raise ValueError("cost_basis must be non-negative")
        if self.current_price is not None and self.current_price < 0:
            raise ValueError("current_price must be non-negative")

    def market_value(self) -> Decimal | None:
        if self.current_price is None:
            return None
        return Decimal(self.quantity) * self.current_price

    def unrealized_pnl(self) -> Decimal | None:
        if self.current_price is None:
            return None
        return Decimal(self.quantity) * (self.current_price - self.cost_basis)

    def is_long(self) -> bool:
        return self.quantity > 0

    def is_short(self) -> bool:
        return self.quantity < 0

    def is_closed(self) -> bool:
        return self.quantity == 0

    def weighted_cost_basis(self, additional_cost: Decimal, additional_qty: int) -> Decimal:
        new_qty = self.quantity + additional_qty
        if new_qty == 0:
            return Decimal(0)
        if self.quantity == 0:
            return _to_decimal(additional_cost)
        total_cost = self.cost_basis * Decimal(self.quantity) + _to_decimal(additional_cost) * Decimal(additional_qty)
        return total_cost / Decimal(new_qty)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "cost_basis": str(self.cost_basis),
        }
        if self.current_price is not None:
            d["current_price"] = str(self.current_price)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Position":
        cp = d.get("current_price")
        return cls(
            symbol=d["symbol"],
            quantity=int(d["quantity"]),
            cost_basis=Decimal(str(d["cost_basis"])),
            current_price=Decimal(str(cp)) if cp is not None else None,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return NotImplemented
        return self.symbol == other.symbol

    def __hash__(self) -> int:
        return hash(self.symbol)


@dataclass(frozen=True, slots=True)
class Portfolio:
    positions: list[Position]
    cash: Decimal = Decimal(0)
    name: str = ""

    def __post_init__(self) -> None:
        if self.cash < 0:
            raise ValueError("cash must be non-negative")

    def position_count(self) -> int:
        return len(self.positions)

    def has_position(self, symbol: str) -> bool:
        return any(p.symbol == symbol for p in self.positions)

    def get_position(self, symbol: str) -> Position | None:
        for p in self.positions:
            if p.symbol == symbol:
                return p
        return None

    def total_value(self) -> Decimal:
        total = self.cash
        for p in self.positions:
            mv = p.market_value()
            if mv is not None:
                total += mv
        return total

    def total_unrealized_pnl(self) -> Decimal:
        total = Decimal(0)
        for p in self.positions:
            pnl = p.unrealized_pnl()
            if pnl is not None:
                total += pnl
        return total

    def exposure_by_symbol(self) -> dict[str, Decimal]:
        out: dict[str, Decimal] = {}
        for p in self.positions:
            mv = p.market_value()
            if mv is not None:
                out[p.symbol] = mv
        return out

    def net_exposure(self) -> Decimal:
        total = Decimal(0)
        for p in self.positions:
            mv = p.market_value()
            if mv is not None:
                total += mv
        return total

    def gross_exposure(self) -> Decimal:
        total = Decimal(0)
        for p in self.positions:
            mv = p.market_value()
            if mv is not None:
                total += abs(mv)
        return total

    def to_dict(self) -> dict[str, Any]:
        return {
            "positions": [p.to_dict() for p in self.positions],
            "cash": str(self.cash),
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Portfolio":
        positions = [Position.from_dict(p) for p in d.get("positions", [])]
        return cls(
            positions=positions,
            cash=Decimal(str(d.get("cash", "0"))),
            name=d.get("name", ""),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Portfolio):
            return NotImplemented
        return (
            self.positions == other.positions
            and self.cash == other.cash
            and self.name == other.name
        )

    def __hash__(self) -> int:
        return hash((tuple(self.positions), self.cash, self.name))


@dataclass(frozen=True, slots=True)
class OrderBook:
    symbol: str
    bids: list[tuple[Decimal, int]]
    asks: list[tuple[Decimal, int]]
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must be non-empty")
        # bids must be sorted high->low
        for i in range(len(self.bids) - 1):
            if self.bids[i][0] < self.bids[i + 1][0]:
                raise ValueError("bids must be sorted from highest to lowest price")
        # asks must be sorted low->high
        for i in range(len(self.asks) - 1):
            if self.asks[i][0] > self.asks[i + 1][0]:
                raise ValueError("asks must be sorted from lowest to highest price")

    def best_bid(self) -> Decimal | None:
        return self.bids[0][0] if self.bids else None

    def best_ask(self) -> Decimal | None:
        return self.asks[0][0] if self.asks else None

    def spread(self) -> Decimal | None:
        bb = self.best_bid()
        ba = self.best_ask()
        if bb is None or ba is None:
            return None
        return ba - bb

    def mid_price(self) -> Decimal | None:
        bb = self.best_bid()
        ba = self.best_ask()
        if bb is None or ba is None:
            return None
        return (bb + ba) / Decimal(2)

    def total_bid_volume(self) -> int:
        return sum(q for _, q in self.bids)

    def total_ask_volume(self) -> int:
        return sum(q for _, q in self.asks)

    def bid_depth(self, n: int) -> list[tuple[Decimal, int]]:
        return list(self.bids[:n])

    def ask_depth(self, n: int) -> list[tuple[Decimal, int]]:
        return list(self.asks[:n])

    def imbalance_ratio(self) -> Decimal | None:
        bv = self.total_bid_volume()
        av = self.total_ask_volume()
        total = bv + av
        if total == 0:
            return None
        return Decimal(bv - av) / Decimal(total)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "symbol": self.symbol,
            "bids": [[str(p), q] for p, q in self.bids],
            "asks": [[str(p), q] for p, q in self.asks],
        }
        if self.timestamp is not None:
            d["timestamp"] = self.timestamp
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "OrderBook":
        bids = [(Decimal(str(b[0])), int(b[1])) for b in d.get("bids", [])]
        asks = [(Decimal(str(a[0])), int(a[1])) for a in d.get("asks", [])]
        return cls(
            symbol=d["symbol"],
            bids=bids,
            asks=asks,
            timestamp=d.get("timestamp"),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OrderBook):
            return NotImplemented
        return (
            self.symbol == other.symbol
            and self.bids == other.bids
            and self.asks == other.asks
            and self.timestamp == other.timestamp
        )

    def __hash__(self) -> int:
        return hash((self.symbol, tuple(self.bids), tuple(self.asks), self.timestamp))


@dataclass(frozen=True, slots=True)
class TimeSeries:
    dates: list[str]
    values: list[Decimal]

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.values):
            raise ValueError("dates and values must have the same length")
        if len(self.values) < 2:
            raise ValueError("TimeSeries requires at least two points")

    def __len__(self) -> int:
        return len(self.values)

    def first(self) -> Decimal:
        return self.values[0]

    def last(self) -> Decimal:
        return self.values[-1]

    def min(self) -> Decimal:
        return min(self.values)

    def max(self) -> Decimal:
        return max(self.values)

    def mean(self) -> Decimal:
        return sum(self.values, Decimal(0)) / Decimal(len(self.values))

    def std(self, ddof: int = 1) -> Decimal:
        n = len(self.values)
        if n - ddof <= 0:
            raise ValueError("ddof too large for sample size")
        mean = self.mean()
        sq = sum((v - mean) ** 2 for v in self.values)
        return Decimal(str(float(sq / Decimal(n - ddof)) ** 0.5))

    def pct_change(self) -> "TimeSeries":
        new_dates = self.dates[1:]
        new_values: list[Decimal] = []
        for i in range(1, len(self.values)):
            prev = self.values[i - 1]
            if prev == 0:
                raise ZeroDivisionError("cannot compute pct_change with zero base")
            new_values.append((self.values[i] - prev) / prev)
        return TimeSeries(dates=new_dates, values=new_values)

    def log_returns(self) -> "TimeSeries":
        from math import log
        new_dates = self.dates[1:]
        new_values: list[Decimal] = []
        for i in range(1, len(self.values)):
            prev = self.values[i - 1]
            curr = self.values[i]
            if prev <= 0 or curr <= 0:
                raise ValueError("log_returns requires positive values")
            new_values.append(Decimal(str(log(float(curr) / float(prev)))))
        return TimeSeries(dates=new_dates, values=new_values)

    def cumulative(self) -> "TimeSeries":
        new_values: list[Decimal] = []
        cum = Decimal(1)
        for r in self.values:
            cum *= Decimal(1) + r
            new_values.append(cum)
        return TimeSeries(dates=list(self.dates), values=new_values)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return TimeSeries(dates=self.dates[idx], values=self.values[idx])
        return self.values[idx]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dates": list(self.dates),
            "values": [str(v) for v in self.values],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TimeSeries":
        return cls(
            dates=list(d["dates"]),
            values=[Decimal(str(v)) for v in d["values"]],
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeSeries):
            return NotImplemented
        return self.dates == other.dates and self.values == other.values

    def __hash__(self) -> int:
        return hash((tuple(self.dates), tuple(self.values)))


__all__ = [
    "FXHistory",
    "Cashflow",
    "Instrument",
    "YieldCurve",
    "ReturnSeries",
    "FXRate",
    "ScheduleRow",
    "Result",
    "MarketData",
    "Trade",
    "Position",
    "Portfolio",
    "OrderBook",
    "TimeSeries",
]

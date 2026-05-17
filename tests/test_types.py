from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.core.types import Cashflow, Instrument, YieldCurve, ReturnSeries, FXRate, ScheduleRow, Result
from finpy.core.types import MarketData, Trade, Position, Portfolio, OrderBook, TimeSeries
from finpy.core.errors import FinPyError
from tests._helpers import approx_decimal


class TestCashflow:
    def test_create(self):
        cf = Cashflow(amount=Decimal("100"), t=0.5)
        assert cf.amount == Decimal("100")
        assert cf.t == 0.5

    def test_negative_time(self):
        with pytest.raises(ValueError):
            Cashflow(amount=Decimal("100"), t=-1)

    def test_zero_time(self):
        cf = Cashflow(amount=Decimal("100"), t=0)
        assert cf.t == 0

    def test_zero_amount(self):
        cf = Cashflow(amount=Decimal("0"), t=1.0)
        assert cf.is_zero()
        assert cf.amount == Decimal("0")

    def test_negative_amount(self):
        cf = Cashflow(amount=Decimal("-50"), t=1.0)
        assert cf.amount == Decimal("-50")
        assert not cf.is_zero()

    def test_repr(self):
        cf = Cashflow(amount=Decimal("100"), t=0.5)
        assert repr(cf) == "Cashflow(amount=100, t=0.5)"

    def test_eq(self):
        cf1 = Cashflow(amount=Decimal("100"), t=0.5)
        cf2 = Cashflow(amount=Decimal("100"), t=0.5)
        cf3 = Cashflow(amount=Decimal("200"), t=0.5)
        assert cf1 == cf2
        assert cf1 != cf3
        assert cf1 != object()

    def test_hash(self):
        cf1 = Cashflow(amount=Decimal("100"), t=0.5)
        cf2 = Cashflow(amount=Decimal("100"), t=0.5)
        assert hash(cf1) == hash(cf2)

    def test_to_dict(self):
        cf = Cashflow(amount=Decimal("100"), t=0.5)
        d = cf.to_dict()
        assert d == {"amount": "100", "t": 0.5}

    def test_from_dict(self):
        d = {"amount": "100", "t": 0.5}
        cf = Cashflow.from_dict(d)
        assert cf.amount == Decimal("100")
        assert cf.t == 0.5

    def test_discounted(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        result = cf.discounted(Decimal("0.05"))
        assert result == pytest.approx(Decimal("95.238"), abs=0.001)

    @given(st.decimals(min_value=-10000, max_value=10000), st.floats(min_value=0, max_value=100))
    def test_discounted_property(self, amount, t):
        assume(amount is not None)
        cf = Cashflow(amount=amount, t=t)
        d = cf.discounted(Decimal("0.05"))
        assert isinstance(d, Decimal)

    def test_discounted_continuous(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        result = cf.discounted(Decimal("0.05"), mode="continuous")
        assert result < Decimal("100")

    def test_not_implemented_eq(self):
        cf = Cashflow(amount=Decimal("100"), t=0.5)
        assert cf.__eq__("not a cashflow") is NotImplemented


class TestInstrument:
    def test_create(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert inst.face_value == Decimal("1000")
        assert inst.coupon_rate == Decimal("0.05")
        assert inst.maturity_years == 5.0
        assert inst.payments_per_year == 2

    def test_invalid_face_value(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("0"), coupon_rate=Decimal("0.05"), maturity_years=5.0)

    def test_invalid_face_value_negative(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("-100"), coupon_rate=Decimal("0.05"), maturity_years=5.0)

    def test_invalid_payments(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=3)

    def test_invalid_coupon_rate_negative(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("-0.05"), maturity_years=5.0)

    def test_invalid_maturity_years_zero(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=0)

    def test_valid_payments_per_year_values(self):
        for ppy in (1, 2, 4, 12):
            inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=ppy)
            assert inst.payments_per_year == ppy

    def test_coupon_amount(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=2)
        assert inst.coupon_amount() == Decimal("25")

    def test_coupon_amount_annual(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.06"), maturity_years=5.0, payments_per_year=1)
        assert inst.coupon_amount() == Decimal("60")

    def test_total_payments(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=2)
        assert inst.total_payments() == 10

    def test_total_payments_annual(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=10.0, payments_per_year=1)
        assert inst.total_payments() == 10

    def test_cashflows_length(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=2)
        cfs = inst.cashflows()
        assert len(cfs) == 10

    def test_cashflows_last_is_face_value_plus_coupon(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=2)
        cfs = inst.cashflows()
        assert cfs[-1].amount == Decimal("1025")
        assert cfs[-1].t == 5.0

    def test_cashflows_first_coupon(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=2)
        cfs = inst.cashflows()
        assert cfs[0].amount == Decimal("25")
        assert cfs[0].t == 0.5

    def test_repr(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        r = repr(inst)
        assert "Instrument" in r
        assert "1000" in r

    def test_eq(self):
        inst1 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        inst2 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        inst3 = Instrument(face_value=Decimal("2000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert inst1 == inst2
        assert inst1 != inst3
        assert inst1 != object()

    def test_hash(self):
        inst1 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        inst2 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert hash(inst1) == hash(inst2)

    def test_to_dict(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        d = inst.to_dict()
        assert d["face_value"] == "1000"
        assert d["coupon_rate"] == "0.05"
        assert d["maturity_years"] == 5.0
        assert d["payments_per_year"] == 2

    def test_from_dict(self):
        d = {"face_value": "1000", "coupon_rate": "0.05", "maturity_years": 5.0}
        inst = Instrument.from_dict(d)
        assert inst.face_value == Decimal("1000")

    def test_from_dict_with_payments(self):
        d = {"face_value": "1000", "coupon_rate": "0.05", "maturity_years": 5.0, "payments_per_year": 4}
        inst = Instrument.from_dict(d)
        assert inst.payments_per_year == 4

    def test_not_implemented_eq(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert inst.__eq__("not an instrument") is NotImplemented


class TestYieldCurve:
    def test_create(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        assert len(yc.rates) == 2

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            YieldCurve(rates={})

    def test_interpolate_exact(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        assert yc.interpolate(1.0) == Decimal("0.05")
        assert yc.interpolate(5.0) == Decimal("0.06")

    def test_interpolate_mid(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        val = yc.interpolate(3.0)
        assert val == Decimal("0.055")

    def test_interpolate_below_min(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        assert yc.interpolate(0.5) == Decimal("0.05")

    def test_interpolate_above_max(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        assert yc.interpolate(10.0) == Decimal("0.06")

    def test_discount_factor(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        df = yc.discount_factor(1.0)
        assert df == pytest.approx(Decimal("0.95123"), abs=0.001)

    def test_tenors(self):
        yc = YieldCurve(rates={5.0: Decimal("0.06"), 1.0: Decimal("0.05")})
        assert yc.tenors() == [1.0, 5.0]

    def test_parallel_shift(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        shifted = yc.parallel_shift(Decimal("50"))
        assert shifted.rates[1.0] == Decimal("0.055")
        assert shifted.rates[5.0] == Decimal("0.065")

    def test_parallel_shift_negative(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05"), 5.0: Decimal("0.06")})
        shifted = yc.parallel_shift(Decimal("-25"))
        assert shifted.rates[1.0] == Decimal("0.0475")

    def test_repr(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05")})
        r = repr(yc)
        assert "YieldCurve" in r

    def test_eq(self):
        yc1 = YieldCurve(rates={1.0: Decimal("0.05")})
        yc2 = YieldCurve(rates={1.0: Decimal("0.05")})
        yc3 = YieldCurve(rates={1.0: Decimal("0.06")})
        assert yc1 == yc2
        assert yc1 != yc3
        assert yc1 != object()

    def test_hash(self):
        yc1 = YieldCurve(rates={1.0: Decimal("0.05")})
        yc2 = YieldCurve(rates={1.0: Decimal("0.05")})
        assert hash(yc1) == hash(yc2)

    def test_to_dict(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05")})
        d = yc.to_dict()
        assert d["rates"]["1.0"] == "0.05"

    def test_from_dict(self):
        d = {"rates": {"1.0": "0.05", "5.0": "0.06"}}
        yc = YieldCurve.from_dict(d)
        assert yc.rates[1.0] == Decimal("0.05")
        assert yc.rates[5.0] == Decimal("0.06")

    def test_not_implemented_eq(self):
        yc = YieldCurve(rates={1.0: Decimal("0.05")})
        assert yc.__eq__("not a yield curve") is NotImplemented


class TestReturnSeries:
    def test_create(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        assert len(rs.values) == 2

    def test_insufficient(self):
        with pytest.raises(ValueError):
            ReturnSeries(values=[Decimal("0.01")])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ReturnSeries(values=[])

    def test_total_return(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20")])
        total = rs.total_return()
        assert total == pytest.approx(Decimal("0.32"), abs=1e-10)

    def test_total_return_negative(self):
        rs = ReturnSeries(values=[Decimal("-0.10"), Decimal("-0.20")])
        total = rs.total_return()
        assert total < 0

    def test_arithmetic_mean(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20"), Decimal("0.30")])
        assert rs.arithmetic_mean() == Decimal("0.20")

    def test_geometric_mean(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20")])
        gm = rs.geometric_mean()
        assert gm == pytest.approx(Decimal("0.14891"), abs=1e-5)

    def test_variance(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20"), Decimal("0.30")])
        var = rs.variance()
        assert var > 0

    def test_variance_ddof_zero(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20"), Decimal("0.30")])
        var = rs.variance(ddof=0)
        assert var > 0

    def test_variance_insufficient(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20")])
        with pytest.raises(ValueError):
            rs.variance(ddof=2)

    def test_std(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20"), Decimal("0.30")])
        s = rs.std()
        assert s > 0

    def test_sharpe_ratio(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02"), Decimal("0.03")])
        sr = rs.sharpe_ratio(risk_free=Decimal("0.005"))
        assert isinstance(sr, Decimal)

    def test_sharpe_ratio_zero_std(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("0.01")])
        sr = rs.sharpe_ratio()
        assert sr == Decimal(0)

    def test_max_drawdown(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("-0.05"), Decimal("0.20")])
        dd = rs.max_drawdown()
        assert dd > 0

    def test_max_drawdown_all_positive(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20"), Decimal("0.30")])
        dd = rs.max_drawdown()
        assert dd == Decimal(0)

    def test_sortino_ratio(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("-0.02"), Decimal("0.03")])
        sr = rs.sortino_ratio(risk_free=Decimal("0.005"))
        assert isinstance(sr, Decimal)

    def test_sortino_no_downside(self):
        rs = ReturnSeries(values=[Decimal("0.10"), Decimal("0.20"), Decimal("0.30")])
        sr = rs.sortino_ratio(risk_free=Decimal("0.05"))
        assert sr == Decimal(0)

    def test_repr(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        r = repr(rs)
        assert "ReturnSeries" in r

    def test_eq(self):
        rs1 = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        rs2 = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        rs3 = ReturnSeries(values=[Decimal("0.03"), Decimal("0.04")])
        assert rs1 == rs2
        assert rs1 != rs3
        assert rs1 != object()

    def test_hash(self):
        rs1 = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        rs2 = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        assert hash(rs1) == hash(rs2)

    def test_to_dict(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        d = rs.to_dict()
        assert d == {"values": ["0.01", "0.02"]}

    def test_from_dict(self):
        d = {"values": ["0.01", "0.02"]}
        rs = ReturnSeries.from_dict(d)
        assert rs.values == [Decimal("0.01"), Decimal("0.02")]

    def test_not_implemented_eq(self):
        rs = ReturnSeries(values=[Decimal("0.01"), Decimal("0.02")])
        assert rs.__eq__("not a return series") is NotImplemented

    @given(st.lists(st.decimals(min_value=-0.5, max_value=0.5), min_size=2, max_size=20))
    def test_total_return_consistent(self, values):
        rs = ReturnSeries(values=[Decimal(str(v)) for v in values])
        tr = rs.total_return()
        assert tr > Decimal("-1")


class TestFXRate:
    def test_create(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        assert fx.rate == Decimal("0.85")

    def test_invalid_pair(self):
        with pytest.raises(ValueError):
            FXRate(currency_pair="USDEUR", rate=Decimal("0.85"), as_of="2024-01-01")

    def test_invalid_pair_short(self):
        with pytest.raises(ValueError):
            FXRate(currency_pair="USD", rate=Decimal("0.85"), as_of="2024-01-01")

    def test_invalid_rate_zero(self):
        with pytest.raises(ValueError):
            FXRate(currency_pair="USD/EUR", rate=Decimal("0"), as_of="2024-01-01")

    def test_invalid_rate_negative(self):
        with pytest.raises(ValueError):
            FXRate(currency_pair="USD/EUR", rate=Decimal("-0.85"), as_of="2024-01-01")

    def test_convert(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        result = fx.convert(Decimal("100"))
        assert result == Decimal("85")

    def test_invert(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        inv = fx.invert()
        assert inv.currency_pair == "EUR/USD"
        assert inv.rate == pytest.approx(Decimal("1.17647"), abs=1e-5)

    def test_base_currency(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        assert fx.base_currency() == "USD"

    def test_quote_currency(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        assert fx.quote_currency() == "EUR"

    def test_repr(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        r = repr(fx)
        assert "FXRate" in r
        assert "0.85" in r

    def test_eq(self):
        fx1 = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        fx2 = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        fx3 = FXRate(currency_pair="USD/GBP", rate=Decimal("0.75"), as_of="2024-01-01")
        assert fx1 == fx2
        assert fx1 != fx3

    def test_hash(self):
        fx1 = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        fx2 = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        assert hash(fx1) == hash(fx2)

    def test_to_dict(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        d = fx.to_dict()
        assert d["currency_pair"] == "USD/EUR"
        assert d["rate"] == "0.85"

    def test_from_dict(self):
        d = {"currency_pair": "USD/EUR", "rate": "0.85", "as_of": "2024-01-01"}
        fx = FXRate.from_dict(d)
        assert fx.rate == Decimal("0.85")

    def test_not_implemented_eq(self):
        fx = FXRate(currency_pair="USD/EUR", rate=Decimal("0.85"), as_of="2024-01-01")
        assert fx.__eq__("not an fxrate") is NotImplemented


class TestScheduleRow:
    def test_create(self):
        sr = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        assert sr.period == 1
        assert sr.payment == Decimal("500")

    def test_repr(self):
        sr = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        r = repr(sr)
        assert "ScheduleRow" in r
        assert "1" in r

    def test_eq(self):
        sr1 = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        sr2 = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        sr3 = ScheduleRow(period=2, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        assert sr1 == sr2
        assert sr1 != sr3

    def test_hash(self):
        sr1 = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        sr2 = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        assert hash(sr1) == hash(sr2)

    def test_to_dict(self):
        sr = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        d = sr.to_dict()
        assert d["period"] == 1
        assert d["payment"] == "500"

    def test_from_dict(self):
        d = {"period": 1, "payment": "500", "interest": "50", "principal": "450", "balance": "9550"}
        sr = ScheduleRow.from_dict(d)
        assert sr.period == 1
        assert sr.balance == Decimal("9550")

    def test_not_implemented_eq(self):
        sr = ScheduleRow(period=1, payment=Decimal("500"), interest=Decimal("50"), principal=Decimal("450"), balance=Decimal("9550"))
        assert sr.__eq__("not a schedul row") is NotImplemented


class TestResult:
    def test_create(self):
        r = Result(value=Decimal("100"), label="npv")
        assert r.value == Decimal("100")
        assert r.label == "npv"

    def test_default_label(self):
        r = Result(value=Decimal("100"))
        assert r.label == ""

    def test_repr(self):
        r = Result(value=Decimal("100"), label="npv")
        assert repr(r) == "Result(value=100, label=npv)"

    def test_eq(self):
        r1 = Result(value=Decimal("100"), label="npv")
        r2 = Result(value=Decimal("100"), label="npv")
        r3 = Result(value=Decimal("200"), label="npv")
        assert r1 == r2
        assert r1 != r3

    def test_hash(self):
        r1 = Result(value=Decimal("100"), label="npv")
        r2 = Result(value=Decimal("100"), label="npv")
        assert hash(r1) == hash(r2)

    def test_add(self):
        r1 = Result(value=Decimal("100"))
        r2 = Result(value=Decimal("50"))
        r3 = r1 + r2
        assert r3.value == Decimal("150")

    def test_sub(self):
        r1 = Result(value=Decimal("100"))
        r2 = Result(value=Decimal("50"))
        r3 = r1 - r2
        assert r3.value == Decimal("50")

    def test_mul(self):
        r = Result(value=Decimal("100"))
        r2 = r * Decimal("2")
        assert r2.value == Decimal("200")

    def test_truediv(self):
        r = Result(value=Decimal("100"))
        r2 = r / Decimal("2")
        assert r2.value == Decimal("50")

    def test_truediv_zero(self):
        r = Result(value=Decimal("100"))
        with pytest.raises(ZeroDivisionError):
            r / Decimal("0")

    def test_to_dict(self):
        r = Result(value=Decimal("100"), label="npv")
        d = r.to_dict()
        assert d == {"value": "100", "label": "npv"}

    def test_from_dict(self):
        d = {"value": "100", "label": "npv"}
        r = Result.from_dict(d)
        assert r.value == Decimal("100")

    def test_from_dict_no_label(self):
        d = {"value": "100"}
        r = Result.from_dict(d)
        assert r.label == ""

    def test_not_implemented_add(self):
        r = Result(value=Decimal("100"))
        assert r.__add__("not a result") is NotImplemented

    def test_not_implemented_sub(self):
        r = Result(value=Decimal("100"))
        assert r.__sub__("not a result") is NotImplemented


class TestMarketData:
    def test_create_minimal(self):
        md = MarketData(symbol="AAPL", price=Decimal("150.00"))
        assert md.symbol == "AAPL"
        assert md.price == Decimal("150.00")
        assert md.volume is None
        assert md.timestamp is None

    def test_create_full(self):
        md = MarketData(symbol="AAPL", price=Decimal("150.00"), volume=1000, timestamp="2024-01-01T09:30:00")
        assert md.volume == 1000
        assert md.timestamp == "2024-01-01T09:30:00"

    def test_empty_symbol(self):
        with pytest.raises(ValueError):
            MarketData(symbol="", price=Decimal("150.00"))

    def test_zero_price(self):
        with pytest.raises(ValueError):
            MarketData(symbol="AAPL", price=Decimal("0"))

    def test_negative_price(self):
        with pytest.raises(ValueError):
            MarketData(symbol="AAPL", price=Decimal("-10"))

    def test_negative_volume(self):
        with pytest.raises(ValueError):
            MarketData(symbol="AAPL", price=Decimal("150"), volume=-5)

    def test_zero_volume(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"), volume=0)
        assert md.volume == 0

    def test_spread(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"))
        spread = md.spread(bid=Decimal("149.50"), ask=Decimal("150.50"))
        assert spread == Decimal("1.00")

    def test_mid_price(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"))
        mid = md.mid_price(bid=Decimal("149.50"), ask=Decimal("150.50"))
        assert mid == Decimal("150.00")

    def test_repr(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"))
        r = repr(md)
        assert "MarketData" in r
        assert "AAPL" in r

    def test_eq(self):
        md1 = MarketData(symbol="AAPL", price=Decimal("150"))
        md2 = MarketData(symbol="AAPL", price=Decimal("150"))
        md3 = MarketData(symbol="GOOG", price=Decimal("150"))
        assert md1 == md2
        assert md1 != md3

    def test_hash(self):
        md1 = MarketData(symbol="AAPL", price=Decimal("150"))
        md2 = MarketData(symbol="AAPL", price=Decimal("150"))
        assert hash(md1) == hash(md2)

    def test_to_dict_minimal(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"))
        d = md.to_dict()
        assert d == {"symbol": "AAPL", "price": "150"}

    def test_to_dict_full(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"), volume=500, timestamp="now")
        d = md.to_dict()
        assert d["volume"] == 500
        assert d["timestamp"] == "now"

    def test_from_dict_minimal(self):
        d = {"symbol": "AAPL", "price": "150.00"}
        md = MarketData.from_dict(d)
        assert md.symbol == "AAPL"
        assert md.price == Decimal("150.00")
        assert md.volume is None

    def test_from_dict_full(self):
        d = {"symbol": "AAPL", "price": "150.00", "volume": 100, "timestamp": "now"}
        md = MarketData.from_dict(d)
        assert md.volume == 100
        assert md.timestamp == "now"

    def test_not_implemented_eq(self):
        md = MarketData(symbol="AAPL", price=Decimal("150"))
        assert md.__eq__("not market data") is NotImplemented


class TestTrade:
    def test_create_buy(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.trade_id == "T1"
        assert t.trade_type == "buy"
        assert t.commission == Decimal(0)

    def test_create_sell(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=-100, price=Decimal("150"), trade_date="2024-01-01", trade_type="sell")
        assert t.trade_type == "sell"

    def test_empty_trade_id(self):
        with pytest.raises(ValueError):
            Trade(trade_id="", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")

    def test_empty_symbol(self):
        with pytest.raises(ValueError):
            Trade(trade_id="T1", symbol="", quantity=100, price=Decimal("150"), trade_date="2024-01-01")

    def test_zero_quantity(self):
        with pytest.raises(ValueError):
            Trade(trade_id="T1", symbol="AAPL", quantity=0, price=Decimal("150"), trade_date="2024-01-01")

    def test_zero_price(self):
        with pytest.raises(ValueError):
            Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("0"), trade_date="2024-01-01")

    def test_negative_price(self):
        with pytest.raises(ValueError):
            Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("-10"), trade_date="2024-01-01")

    def test_invalid_trade_type(self):
        with pytest.raises(ValueError):
            Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01", trade_type="hold")

    def test_negative_commission(self):
        with pytest.raises(ValueError):
            Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01", commission=Decimal("-1"))

    def test_notional(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.notional() == Decimal("15000")

    def test_notional_short(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=-100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.notional() == Decimal("15000")

    def test_gross_value(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.gross_value() == Decimal("15000")

    def test_gross_value_short(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=-100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.gross_value() == Decimal("-15000")

    def test_is_buy(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.is_buy()
        assert not t.is_sell()

    def test_is_sell(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=-100, price=Decimal("150"), trade_date="2024-01-01", trade_type="sell")
        assert t.is_sell()
        assert not t.is_buy()

    def test_repr(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        r = repr(t)
        assert "Trade" in r
        assert "T1" in r

    def test_eq_by_trade_id(self):
        t1 = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        t2 = Trade(trade_id="T1", symbol="GOOG", quantity=200, price=Decimal("100"), trade_date="2024-01-02")
        assert t1 == t2

    def test_hash_by_trade_id(self):
        t1 = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        t2 = Trade(trade_id="T1", symbol="GOOG", quantity=200, price=Decimal("100"), trade_date="2024-01-02")
        assert hash(t1) == hash(t2)

    def test_to_dict(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        d = t.to_dict()
        assert d["trade_id"] == "T1"
        assert d["commission"] == "0"

    def test_from_dict(self):
        d = {"trade_id": "T1", "symbol": "AAPL", "quantity": 100, "price": "150", "trade_date": "2024-01-01"}
        t = Trade.from_dict(d)
        assert t.quantity == 100
        assert t.commission == Decimal(0)

    def test_from_dict_with_commission(self):
        d = {"trade_id": "T1", "symbol": "AAPL", "quantity": 100, "price": "150", "trade_date": "2024-01-01", "commission": "5.00", "trade_type": "sell"}
        t = Trade.from_dict(d)
        assert t.commission == Decimal("5.00")
        assert t.trade_type == "sell"

    def test_not_implemented_eq(self):
        t = Trade(trade_id="T1", symbol="AAPL", quantity=100, price=Decimal("150"), trade_date="2024-01-01")
        assert t.__eq__("not a trade") is NotImplemented


class TestPosition:
    def test_create(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.symbol == "AAPL"
        assert pos.quantity == 100
        assert pos.cost_basis == Decimal("150")
        assert pos.current_price is None

    def test_create_with_current_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        assert pos.current_price == Decimal("160")

    def test_empty_symbol(self):
        with pytest.raises(ValueError):
            Position(symbol="", quantity=100, cost_basis=Decimal("150"))

    def test_negative_cost_basis(self):
        with pytest.raises(ValueError):
            Position(symbol="AAPL", quantity=100, cost_basis=Decimal("-10"))

    def test_zero_cost_basis(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("0"))
        assert pos.cost_basis == Decimal(0)

    def test_negative_current_price(self):
        with pytest.raises(ValueError):
            Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("-1"))

    def test_market_value(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        assert pos.market_value() == Decimal("16000")

    def test_market_value_no_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.market_value() is None

    def test_unrealized_pnl(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        assert pos.unrealized_pnl() == Decimal("1000")

    def test_unrealized_pnl_loss(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("140"))
        assert pos.unrealized_pnl() == Decimal("-1000")

    def test_unrealized_pnl_no_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.unrealized_pnl() is None

    def test_is_long(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.is_long()
        assert not pos.is_short()
        assert not pos.is_closed()

    def test_is_short(self):
        pos = Position(symbol="AAPL", quantity=-100, cost_basis=Decimal("150"))
        assert pos.is_short()
        assert not pos.is_long()

    def test_is_closed(self):
        pos = Position(symbol="AAPL", quantity=0, cost_basis=Decimal("150"))
        assert pos.is_closed()
        assert not pos.is_long()
        assert not pos.is_short()

    def test_weighted_cost_basis(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        new_cb = pos.weighted_cost_basis(additional_cost=Decimal("160"), additional_qty=100)
        assert new_cb == Decimal("155")

    def test_weighted_cost_basis_zero_qty(self):
        pos = Position(symbol="AAPL", quantity=0, cost_basis=Decimal("0"))
        new_cb = pos.weighted_cost_basis(additional_cost=Decimal("100"), additional_qty=10)
        assert new_cb == Decimal("100")

    def test_repr(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        r = repr(pos)
        assert "Position" in r
        assert "AAPL" in r

    def test_eq_by_symbol(self):
        p1 = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        p2 = Position(symbol="AAPL", quantity=200, cost_basis=Decimal("160"))
        assert p1 == p2

    def test_hash_by_symbol(self):
        p1 = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        p2 = Position(symbol="AAPL", quantity=200, cost_basis=Decimal("160"))
        assert hash(p1) == hash(p2)

    def test_to_dict(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        d = pos.to_dict()
        assert d == {"symbol": "AAPL", "quantity": 100, "cost_basis": "150"}

    def test_to_dict_with_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        d = pos.to_dict()
        assert d["current_price"] == "160"

    def test_from_dict(self):
        d = {"symbol": "AAPL", "quantity": 100, "cost_basis": "150"}
        pos = Position.from_dict(d)
        assert pos.cost_basis == Decimal("150")
        assert pos.current_price is None

    def test_from_dict_with_price(self):
        d = {"symbol": "AAPL", "quantity": 100, "cost_basis": "150", "current_price": "160"}
        pos = Position.from_dict(d)
        assert pos.current_price == Decimal("160")

    def test_not_implemented_eq(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.__eq__("not a position") is NotImplemented


class TestPortfolio:
    def test_create_empty(self):
        pf = Portfolio(positions=[])
        assert pf.positions == []
        assert pf.cash == Decimal(0)
        assert pf.name == ""

    def test_create_with_positions(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pf = Portfolio(positions=[pos], cash=Decimal("10000"), name="test")
        assert pf.position_count() == 1
        assert pf.cash == Decimal("10000")
        assert pf.name == "test"

    def test_negative_cash(self):
        with pytest.raises(ValueError):
            Portfolio(positions=[], cash=Decimal("-1"))

    def test_total_value(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pf = Portfolio(positions=[pos], cash=Decimal("5000"))
        assert pf.total_value() == Decimal("21000")

    def test_total_value_no_market_prices(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        pf = Portfolio(positions=[pos], cash=Decimal("5000"))
        assert pf.total_value() == Decimal("5000")

    def test_total_unrealized_pnl(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pf = Portfolio(positions=[pos], cash=Decimal("5000"))
        assert pf.total_unrealized_pnl() == Decimal("1000")

    def test_has_position(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        pf = Portfolio(positions=[pos])
        assert pf.has_position("AAPL")
        assert not pf.has_position("GOOG")

    def test_get_position(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        pf = Portfolio(positions=[pos])
        assert pf.get_position("AAPL") == pos
        assert pf.get_position("GOOG") is None

    def test_exposure_by_symbol(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pf = Portfolio(positions=[pos])
        exp = pf.exposure_by_symbol()
        assert exp["AAPL"] == Decimal("16000")

    def test_net_exposure_long(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pf = Portfolio(positions=[pos])
        assert pf.net_exposure() == Decimal("16000")

    def test_net_exposure_short(self):
        pos = Position(symbol="AAPL", quantity=-100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pf = Portfolio(positions=[pos])
        assert pf.net_exposure() == Decimal("-16000")

    def test_gross_exposure(self):
        pos1 = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"), current_price=Decimal("160"))
        pos2 = Position(symbol="GOOG", quantity=-50, cost_basis=Decimal("100"), current_price=Decimal("110"))
        pf = Portfolio(positions=[pos1, pos2])
        assert pf.gross_exposure() == Decimal("16000") + Decimal("5500")

    def test_repr(self):
        pf = Portfolio(positions=[])
        r = repr(pf)
        assert "Portfolio" in r

    def test_eq(self):
        pf1 = Portfolio(positions=[], cash=Decimal(0), name="test")
        pf2 = Portfolio(positions=[], cash=Decimal(0), name="test")
        pf3 = Portfolio(positions=[], cash=Decimal("100"), name="test")
        assert pf1 == pf2
        assert pf1 != pf3

    def test_hash(self):
        pf1 = Portfolio(positions=[], cash=Decimal(0), name="test")
        pf2 = Portfolio(positions=[], cash=Decimal(0), name="test")
        assert hash(pf1) == hash(pf2)

    def test_to_dict(self):
        pf = Portfolio(positions=[], cash=Decimal("5000"), name="test")
        d = pf.to_dict()
        assert d["cash"] == "5000"
        assert d["name"] == "test"

    def test_from_dict(self):
        d = {"positions": [], "cash": "5000", "name": "test"}
        pf = Portfolio.from_dict(d)
        assert pf.cash == Decimal("5000")
        assert pf.name == "test"

    def test_not_implemented_eq(self):
        pf = Portfolio(positions=[])
        assert pf.__eq__("not a portfolio") is NotImplemented

    def test_multiple_positions_count(self):
        p1 = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        p2 = Position(symbol="GOOG", quantity=50, cost_basis=Decimal("100"))
        pf = Portfolio(positions=[p1, p2])
        assert pf.position_count() == 2


class TestOrderBook:
    def test_create(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        assert ob.symbol == "AAPL"
        assert ob.best_bid() == Decimal("150")
        assert ob.best_ask() == Decimal("151")

    def test_empty_symbol(self):
        with pytest.raises(ValueError):
            OrderBook(symbol="", bids=[], asks=[])

    def test_bids_not_sorted(self):
        with pytest.raises(ValueError):
            OrderBook(symbol="AAPL", bids=[(Decimal("149"), 100), (Decimal("151"), 200)], asks=[])

    def test_asks_not_sorted(self):
        with pytest.raises(ValueError):
            OrderBook(symbol="AAPL", bids=[], asks=[(Decimal("152"), 100), (Decimal("151"), 200)])

    def test_empty_order_book(self):
        ob = OrderBook(symbol="AAPL", bids=[], asks=[])
        assert ob.best_bid() is None
        assert ob.best_ask() is None
        assert ob.spread() is None
        assert ob.mid_price() is None

    def test_spread(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100), (Decimal("149"), 300)], asks=[(Decimal("151"), 200), (Decimal("152"), 400)])
        assert ob.spread() == Decimal("1")

    def test_mid_price(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        assert ob.mid_price() == Decimal("150.5")

    def test_total_bid_volume(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100), (Decimal("149"), 300)], asks=[])
        assert ob.total_bid_volume() == 400

    def test_total_ask_volume(self):
        ob = OrderBook(symbol="AAPL", bids=[], asks=[(Decimal("151"), 200), (Decimal("152"), 400)])
        assert ob.total_ask_volume() == 600

    def test_bid_depth(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100), (Decimal("149"), 300), (Decimal("148"), 500)], asks=[])
        depth = ob.bid_depth(2)
        assert len(depth) == 2
        assert depth[0][0] == Decimal("150")

    def test_ask_depth(self):
        ob = OrderBook(symbol="AAPL", bids=[], asks=[(Decimal("151"), 200), (Decimal("152"), 400), (Decimal("153"), 600)])
        depth = ob.ask_depth(2)
        assert len(depth) == 2

    def test_imbalance_ratio(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        ir = ob.imbalance_ratio()
        assert ir == pytest.approx(Decimal("-0.33333"), abs=1e-5)

    def test_imbalance_ratio_zero(self):
        ob = OrderBook(symbol="AAPL", bids=[], asks=[])
        assert ob.imbalance_ratio() is None

    def test_imbalance_ratio_equal(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 100)])
        assert ob.imbalance_ratio() == Decimal("0")

    def test_repr(self):
        ob = OrderBook(symbol="AAPL", bids=[], asks=[])
        r = repr(ob)
        assert "OrderBook" in r
        assert "AAPL" in r

    def test_eq(self):
        ob1 = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        ob2 = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        ob3 = OrderBook(symbol="GOOG", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        assert ob1 == ob2
        assert ob1 != ob3

    def test_hash(self):
        ob1 = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        ob2 = OrderBook(symbol="AAPL", bids=[(Decimal("150"), 100)], asks=[(Decimal("151"), 200)])
        assert hash(ob1) == hash(ob2)

    def test_to_dict(self):
        ob = OrderBook(symbol="AAPL", bids=[(Decimal("150.5"), 100)], asks=[], timestamp="now")
        d = ob.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["bids"] == [["150.5", 100]]

    def test_from_dict(self):
        d = {"symbol": "AAPL", "bids": [["150.5", 100]], "asks": [["151.5", 200]]}
        ob = OrderBook.from_dict(d)
        assert ob.best_bid() == Decimal("150.5")
        assert ob.best_ask() == Decimal("151.5")

    def test_not_implemented_eq(self):
        ob = OrderBook(symbol="AAPL", bids=[], asks=[])
        assert ob.__eq__("not orderbook") is NotImplemented


class TestTimeSeries:
    def test_create(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        assert len(ts) == 2
        assert ts.first() == Decimal("100")
        assert ts.last() == Decimal("101")

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            TimeSeries(dates=["2024-01-01"], values=[Decimal("100"), Decimal("101")])

    def test_single_point(self):
        with pytest.raises(ValueError):
            TimeSeries(dates=["2024-01-01"], values=[Decimal("100")])

    def test_empty(self):
        with pytest.raises(ValueError):
            TimeSeries(dates=[], values=[])

    def test_min(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("99"), Decimal("101")])
        assert ts.min() == Decimal("99")

    def test_max(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("99"), Decimal("101")])
        assert ts.max() == Decimal("101")

    def test_mean(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("102"), Decimal("104")])
        assert ts.mean() == Decimal("102")

    def test_std(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"], values=[Decimal("100"), Decimal("102"), Decimal("104"), Decimal("106")])
        s = ts.std()
        assert s > 0

    def test_std_ddof_zero(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"], values=[Decimal("100"), Decimal("102"), Decimal("104"), Decimal("106")])
        s = ts.std(ddof=0)
        assert s > 0

    def test_std_insufficient(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        with pytest.raises(ValueError):
            ts.std(ddof=2)

    def test_pct_change(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("110"), Decimal("121")])
        pct = ts.pct_change()
        assert len(pct) == 2
        assert pct.values[0] == Decimal("0.10")
        assert pct.values[1] == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_pct_change_zero_base(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("0"), Decimal("100")])
        with pytest.raises(ZeroDivisionError):
            ts.pct_change()

    def test_log_returns(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("110"), Decimal("121")])
        lr = ts.log_returns()
        assert len(lr) == 2
        assert lr.values[0] > 0

    def test_log_returns_non_positive(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("0"), Decimal("100")])
        with pytest.raises(Exception):
            ts.log_returns()

    def test_cumulative(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("0.10"), Decimal("0.10"), Decimal("0.10")])
        cum = ts.cumulative()
        assert len(cum) == 3
        assert cum.values[0] == Decimal("1.10")
        assert cum.values[1] == Decimal("1.21")
        assert cum.values[2] == pytest.approx(Decimal("1.331"), abs=1e-10)

    def test_getitem(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("101"), Decimal("102")])
        assert ts[0] == Decimal("100")
        assert ts[1] == Decimal("101")

    def test_getitem_slice(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02", "2024-01-03"], values=[Decimal("100"), Decimal("101"), Decimal("102")])
        sub = ts[0:2]
        assert len(sub) == 2
        assert sub.dates == ["2024-01-01", "2024-01-02"]

    def test_repr(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        r = repr(ts)
        assert "TimeSeries" in r

    def test_eq(self):
        ts1 = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        ts2 = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        ts3 = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("200"), Decimal("201")])
        assert ts1 == ts2
        assert ts1 != ts3

    def test_hash(self):
        ts1 = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        ts2 = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        assert hash(ts1) == hash(ts2)

    def test_to_dict(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        d = ts.to_dict()
        assert d["dates"] == ["2024-01-01", "2024-01-02"]
        assert d["values"] == ["100", "101"]

    def test_from_dict(self):
        d = {"dates": ["2024-01-01", "2024-01-02"], "values": ["100", "101"]}
        ts = TimeSeries.from_dict(d)
        assert ts.values == [Decimal("100"), Decimal("101")]

    def test_not_implemented_eq(self):
        ts = TimeSeries(dates=["2024-01-01", "2024-01-02"], values=[Decimal("100"), Decimal("101")])
        assert ts.__eq__("not a timeseries") is NotImplemented

    @given(st.lists(st.decimals(min_value=1, max_value=1000), min_size=3, max_size=20))
    def test_pct_change_property(self, values):
        ts = TimeSeries(dates=[f"2024-01-{i+1:02d}" for i in range(len(values))], values=[Decimal(str(v)) for v in values])
        pct = ts.pct_change()
        assert len(pct) == len(ts) - 1

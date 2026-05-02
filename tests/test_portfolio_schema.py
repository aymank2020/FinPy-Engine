from decimal import Decimal
from hypothesis import given, strategies as st, assume
from finpy.core.types import Position, Portfolio
import pytest


def sample_position(symbol="AAPL", qty=100, cost=Decimal("150"), price=Decimal("160")):
    return Position(symbol=symbol, quantity=qty, cost_basis=cost, current_price=price)


def sample_portfolio():
    pos1 = sample_position()
    pos2 = sample_position("GOOG", 50, Decimal("2000"), Decimal("2100"))
    return Portfolio(positions=[pos1, pos2], cash=Decimal("1000"), name="TestPortfolio")


class TestPortfolioSchema:
    def test_roundtrip(self):
        pf = sample_portfolio()
        data = pf.to_dict()
        pf2 = Portfolio.from_dict(data)
        assert pf == pf2

    def test_to_dict(self):
        pf = sample_portfolio()
        d = pf.to_dict()
        assert len(d["positions"]) == 2
        assert d["cash"] == "1000"
        assert d["name"] == "TestPortfolio"

    def test_from_dict(self):
        data = {
            "positions": [
                {"symbol": "AAPL", "quantity": 100, "cost_basis": "150", "current_price": "160"},
                {"symbol": "GOOG", "quantity": 50, "cost_basis": "2000", "current_price": "2100"},
            ],
            "cash": "500",
            "name": "FromDict",
        }
        pf = Portfolio.from_dict(data)
        assert pf.name == "FromDict"
        assert pf.cash == Decimal("500")
        assert len(pf.positions) == 2

    def test_empty_portfolio(self):
        pf = Portfolio(positions=[], cash=Decimal("0"), name="Empty")
        d = pf.to_dict()
        pf2 = Portfolio.from_dict(d)
        assert pf == pf2

    def test_total_value(self):
        pf = sample_portfolio()
        tv = pf.total_value()
        expected = Decimal("1000") + Decimal("100") * Decimal("160") + Decimal("50") * Decimal("2100")
        assert tv == expected

    def test_total_unrealized_pnl(self):
        pf = sample_portfolio()
        pnl = pf.total_unrealized_pnl()
        expected = (Decimal("160") - Decimal("150")) * Decimal("100") + (Decimal("2100") - Decimal("2000")) * Decimal("50")
        assert pnl == expected

    def test_position_count(self):
        pf = sample_portfolio()
        assert pf.position_count() == 2

    def test_has_position(self):
        pf = sample_portfolio()
        assert pf.has_position("AAPL") is True
        assert pf.has_position("TSLA") is False

    def test_get_position(self):
        pf = sample_portfolio()
        pos = pf.get_position("AAPL")
        assert pos is not None
        assert pos.symbol == "AAPL"
        assert pf.get_position("TSLA") is None

    def test_exposure_by_symbol(self):
        pf = sample_portfolio()
        exp = pf.exposure_by_symbol()
        assert "AAPL" in exp
        assert "GOOG" in exp
        assert exp["AAPL"] == Decimal("16000")

    def test_net_exposure(self):
        pf = sample_portfolio()
        net = pf.net_exposure()
        expected = Decimal("100") * Decimal("160") + Decimal("50") * Decimal("2100")
        assert net == expected

    def test_gross_exposure(self):
        pf = sample_portfolio()
        gross = pf.gross_exposure()
        expected = abs(Decimal("100") * Decimal("160")) + abs(Decimal("50") * Decimal("2100"))
        assert gross == expected

    def test_cash_only_portfolio(self):
        pf = Portfolio(positions=[], cash=Decimal("5000"), name="CashOnly")
        assert pf.total_value() == Decimal("5000")
        assert pf.total_unrealized_pnl() == Decimal("0")
        assert pf.position_count() == 0

    def test_portfolio_with_short_positions(self):
        pos = Position(symbol="TSLA", quantity=-10, cost_basis=Decimal("200"), current_price=Decimal("180"))
        pf = Portfolio(positions=[pos], cash=Decimal("1000"))
        assert pf.net_exposure() == Decimal("-1800")

    def test_portfolio_equality(self):
        pf1 = sample_portfolio()
        pf2 = sample_portfolio()
        pf3 = Portfolio(positions=[], cash=Decimal("0"))
        assert pf1 == pf2
        assert pf1 != pf3

    def test_portfolio_hash(self):
        pf1 = sample_portfolio()
        pf2 = sample_portfolio()
        assert hash(pf1) == hash(pf2)

    def test_portfolio_repr(self):
        pf = sample_portfolio()
        r = repr(pf)
        assert "Portfolio" in r
        assert "TestPortfolio" in r

    def test_portfolio_invalid_cash(self):
        with pytest.raises(ValueError):
            Portfolio(positions=[], cash=Decimal("-1"))

    def test_portfolio_no_name(self):
        pf = Portfolio(positions=[], cash=Decimal("0"))
        assert pf.name == ""

    def test_portfolio_no_current_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        pf = Portfolio(positions=[pos], cash=Decimal("0"))
        assert pos.market_value() is None
        assert pf.total_value() == Decimal("0")


class TestPositionSchema:
    def test_roundtrip(self):
        pos = sample_position()
        data = pos.to_dict()
        pos2 = Position.from_dict(data)
        assert pos == pos2

    def test_to_dict(self):
        pos = sample_position()
        d = pos.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["quantity"] == 100
        assert d["cost_basis"] == "150"
        assert d["current_price"] == "160"

    def test_from_dict_without_current_price(self):
        data = {"symbol": "AAPL", "quantity": 100, "cost_basis": "150"}
        pos = Position.from_dict(data)
        assert pos.current_price is None

    def test_market_value(self):
        pos = sample_position()
        assert pos.market_value() == Decimal("16000")

    def test_market_value_no_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.market_value() is None

    def test_unrealized_pnl(self):
        pos = sample_position()
        assert pos.unrealized_pnl() == Decimal("1000")

    def test_unrealized_pnl_no_price(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert pos.unrealized_pnl() is None

    def test_is_long(self):
        assert sample_position().is_long() is True
        assert Position(symbol="A", quantity=-10, cost_basis=Decimal("100")).is_long() is False

    def test_is_short(self):
        assert Position(symbol="A", quantity=-10, cost_basis=Decimal("100")).is_short() is True
        assert sample_position().is_short() is False

    def test_is_closed(self):
        assert Position(symbol="A", quantity=0, cost_basis=Decimal("0")).is_closed() is True
        assert sample_position().is_closed() is False

    def test_weighted_cost_basis(self):
        pos = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        new_cost = pos.weighted_cost_basis(Decimal("170"), Decimal("50"))
        expected = (Decimal("150") * Decimal("100") + Decimal("170") * Decimal("50")) / Decimal("150")
        assert new_cost == expected

    def test_invalid_symbol(self):
        with pytest.raises(ValueError):
            Position(symbol="", quantity=100, cost_basis=Decimal("100"))

    def test_invalid_cost_basis(self):
        with pytest.raises(ValueError):
            Position(symbol="AAPL", quantity=100, cost_basis=Decimal("-1"))

    def test_invalid_current_price(self):
        with pytest.raises(ValueError):
            Position(symbol="AAPL", quantity=100, cost_basis=Decimal("100"), current_price=Decimal("-1"))

    def test_position_hash(self):
        p1 = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        p2 = Position(symbol="AAPL", quantity=100, cost_basis=Decimal("150"))
        assert hash(p1) == hash(p2)

    def test_position_repr(self):
        pos = sample_position()
        r = repr(pos)
        assert "Position" in r
        assert "AAPL" in r


@given(
    st.sampled_from(["AAPL", "GOOG", "TSLA", "MSFT"]),
    st.integers(min_value=1, max_value=1000),
    st.decimals(min_value=10, max_value=500),
    st.decimals(min_value=10, max_value=500),
)
def test_position_roundtrip_hypothesis(symbol, qty, cost, price):
    assume(cost > 0 and price > 0)
    pos = Position(symbol=symbol, quantity=qty, cost_basis=cost, current_price=price)
    data = pos.to_dict()
    pos2 = Position.from_dict(data)
    assert pos == pos2


@given(
    st.lists(
        st.fixed_dictionaries({
            "symbol": st.sampled_from(["AAPL", "GOOG", "MSFT"]),
            "quantity": st.integers(min_value=1, max_value=100),
            "cost_basis": st.decimals(min_value=10, max_value=500),
            "current_price": st.decimals(min_value=10, max_value=500),
        }),
        min_size=1, max_size=5,
    ),
    st.decimals(min_value=0, max_value=10000),
    st.text(max_size=20),
)
def test_portfolio_roundtrip_hypothesis(pos_data, cash, name):
    positions = [Position(**p) for p in pos_data]
    pf = Portfolio(positions=positions, cash=cash, name=name)
    data = pf.to_dict()
    pf2 = Portfolio.from_dict(data)
    assert pf == pf2

import pytest
from finpy.core.errors import FinPyError, InvalidCashflowError, InvalidInstrumentError, NoSolutionFoundError
from finpy.core.errors import UnknownCurrencyError, RateNotAvailableError, SchemaValidationError, MigrationError
from finpy.core.errors import InvalidTradeError, InsufficientDataError, InvalidParameterError
from finpy.core.errors import InvalidPortfolioError, InvalidPositionError, ConvergenceError
from finpy.core.errors import ValuationError, MarketDataError, CurveConstructionError
from finpy.core.errors import InterpolationError, DateMismatchError, NotImplementedInModeError
from finpy.core.errors import NegativeRateError, DivisionByZeroError, CalculationError, DataNotFoundError
from finpy.core.errors import UnsupportedModeError, PeriodMismatchError, ValidationAggregateError
from finpy.core.errors import CashflowStructureError, PriceOutOfRangeError, TimeSeriesError
from finpy.core.errors import OverlappingDataError, InvalidDateError, BenchmarkMismatchError
from finpy.core.errors import InsufficientObservationsError, OptimizationError, ConfigurationError
from finpy.core.errors import FileFormatError, ImportError


ERROR_CLASSES = [
    InvalidCashflowError, InvalidInstrumentError, NoSolutionFoundError,
    UnknownCurrencyError, RateNotAvailableError, SchemaValidationError, MigrationError,
    InvalidTradeError, InsufficientDataError, InvalidParameterError,
    InvalidPortfolioError, InvalidPositionError, ConvergenceError,
    ValuationError, MarketDataError, CurveConstructionError,
    InterpolationError, DateMismatchError, NotImplementedInModeError,
    NegativeRateError, DivisionByZeroError, CalculationError, DataNotFoundError,
    UnsupportedModeError, PeriodMismatchError, ValidationAggregateError,
    CashflowStructureError, PriceOutOfRangeError, TimeSeriesError,
    OverlappingDataError, InvalidDateError, BenchmarkMismatchError,
    InsufficientObservationsError, OptimizationError, ConfigurationError,
    FileFormatError, ImportError,
]


class TestFinPyError:
    def test_base_class(self):
        e = FinPyError("test error")
        assert str(e) == "test error"
        assert isinstance(e, Exception)

    def test_all_subclass_finpy_error(self):
        for e in ERROR_CLASSES:
            assert issubclass(e, FinPyError)

    def test_instantiation(self):
        e = InvalidCashflowError("bad cashflow")
        assert str(e) == "bad cashflow"

    def test_catch_all_as_finpy_error(self):
        for cls in ERROR_CLASSES:
            try:
                raise cls("test")
            except FinPyError:
                pass


class TestInvalidTradeError:
    def test_default_message(self):
        e = InvalidTradeError()
        assert str(e) == ""

    def test_with_trade_id(self):
        e = InvalidTradeError("bad trade", trade_id="T123")
        assert str(e) == "bad trade"
        assert e.trade_id == "T123"


class TestInsufficientDataError:
    def test_default_message(self):
        e = InsufficientDataError()
        assert str(e) == ""

    def test_with_points(self):
        e = InsufficientDataError("too few", required_points=10, available=3)
        assert e.required_points == 10
        assert e.available == 3


class TestInvalidParameterError:
    def test_default_message(self):
        e = InvalidParameterError()
        assert str(e) == ""

    def test_with_parameter_name(self):
        e = InvalidParameterError("bad param", parameter_name="rate")
        assert e.parameter_name == "rate"


class TestInvalidPortfolioError:
    def test_instantiation(self):
        e = InvalidPortfolioError("bad portfolio")
        assert str(e) == "bad portfolio"


class TestInvalidPositionError:
    def test_instantiation(self):
        e = InvalidPositionError("bad position")
        assert str(e) == "bad position"


class TestConvergenceError:
    def test_default_message(self):
        e = ConvergenceError()
        assert str(e) == ""

    def test_with_iterations(self):
        e = ConvergenceError("did not converge", iterations=100, tolerance=1e-10)
        assert e.iterations == 100
        assert e.tolerance == 1e-10


class TestValuationError:
    def test_instantiation(self):
        e = ValuationError("valuation failed")
        assert str(e) == "valuation failed"


class TestMarketDataError:
    def test_default_message(self):
        e = MarketDataError()
        assert str(e) == ""

    def test_with_symbol(self):
        e = MarketDataError("no data", symbol="AAPL")
        assert e.symbol == "AAPL"


class TestCurveConstructionError:
    def test_instantiation(self):
        e = CurveConstructionError("bad curve")
        assert str(e) == "bad curve"


class TestInterpolationError:
    def test_instantiation(self):
        e = InterpolationError("interp failed")
        assert str(e) == "interp failed"


class TestDateMismatchError:
    def test_default_message(self):
        e = DateMismatchError()
        assert str(e) == ""

    def test_with_dates(self):
        e = DateMismatchError("mismatch", expected="2024-01-01", actual="2024-01-02")
        assert e.expected == "2024-01-01"
        assert e.actual == "2024-01-02"


class TestNotImplementedInModeError:
    def test_default_message(self):
        e = NotImplementedInModeError()
        assert str(e) == ""

    def test_with_mode(self):
        e = NotImplementedInModeError("not supported", mode="monthly")
        assert e.mode == "monthly"


class TestNegativeRateError:
    def test_instantiation(self):
        e = NegativeRateError("negative rate")
        assert str(e) == "negative rate"


class TestDivisionByZeroError:
    def test_instantiation(self):
        e = DivisionByZeroError("div by zero")
        assert str(e) == "div by zero"


class TestCalculationError:
    def test_instantiation(self):
        e = CalculationError("calc error")
        assert str(e) == "calc error"


class TestDataNotFoundError:
    def test_default_message(self):
        e = DataNotFoundError()
        assert str(e) == ""

    def test_with_key(self):
        e = DataNotFoundError("not found", key="AAPL")
        assert e.key == "AAPL"


class TestUnsupportedModeError:
    def test_default_message(self):
        e = UnsupportedModeError()
        assert str(e) == ""

    def test_with_mode(self):
        e = UnsupportedModeError("unsupported", mode="weekly")
        assert e.mode == "weekly"


class TestPeriodMismatchError:
    def test_default_message(self):
        e = PeriodMismatchError()
        assert str(e) == ""

    def test_with_periods(self):
        e = PeriodMismatchError("mismatch", expected=12, actual=10)
        assert e.expected == 12
        assert e.actual == 10


class TestValidationAggregateError:
    def test_default_message(self):
        e = ValidationAggregateError()
        assert str(e) == ""
        assert e.errors == []

    def test_with_errors(self):
        inner = [ValueError("e1"), TypeError("e2")]
        e = ValidationAggregateError("validation failed", errors=inner)
        assert len(e.errors) == 2
        assert isinstance(e.errors[0], ValueError)


class TestCashflowStructureError:
    def test_instantiation(self):
        e = CashflowStructureError("bad structure")
        assert str(e) == "bad structure"


class TestPriceOutOfRangeError:
    def test_instantiation(self):
        e = PriceOutOfRangeError("price out of range")
        assert str(e) == "price out of range"


class TestTimeSeriesError:
    def test_instantiation(self):
        e = TimeSeriesError("ts error")
        assert str(e) == "ts error"


class TestOverlappingDataError:
    def test_instantiation(self):
        e = OverlappingDataError("overlap")
        assert str(e) == "overlap"


class TestInvalidDateError:
    def test_default_message(self):
        e = InvalidDateError()
        assert str(e) == ""

    def test_with_date_str(self):
        e = InvalidDateError("bad date", date_str="2024-13-01")
        assert e.date_str == "2024-13-01"


class TestBenchmarkMismatchError:
    def test_instantiation(self):
        e = BenchmarkMismatchError("mismatch")
        assert str(e) == "mismatch"


class TestInsufficientObservationsError:
    def test_default_message(self):
        e = InsufficientObservationsError()
        assert str(e) == ""

    def test_with_counts(self):
        e = InsufficientObservationsError("too few", required=100, available=10)
        assert e.required == 100
        assert e.available == 10


class TestOptimizationError:
    def test_instantiation(self):
        e = OptimizationError("opt failed")
        assert str(e) == "opt failed"


class TestConfigurationError:
    def test_instantiation(self):
        e = ConfigurationError("bad config")
        assert str(e) == "bad config"


class TestFileFormatError:
    def test_instantiation(self):
        e = FileFormatError("bad format")
        assert str(e) == "bad format"


class TestImportError:
    def test_instantiation(self):
        e = ImportError("import failed")
        assert str(e) == "import failed"

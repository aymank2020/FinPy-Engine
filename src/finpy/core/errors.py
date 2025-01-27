"""FinPy domain-specific exception hierarchy.

All custom exceptions in finpy subclass :class:`FinPyError`, which itself is a
subclass of :class:`Exception`. The richer error classes accept optional
keyword-only context attributes that callers (and tests) can introspect.
"""

from __future__ import annotations


class FinPyError(Exception):
    """Base exception for all finpy errors."""


class InvalidCashflowError(FinPyError):
    pass


class InvalidInstrumentError(FinPyError):
    pass


class NoSolutionFoundError(FinPyError):
    pass


class UnknownCurrencyError(FinPyError):
    pass


class RateNotAvailableError(FinPyError):
    pass


class SchemaValidationError(FinPyError):
    pass


class MigrationError(FinPyError):
    pass


class InvalidTradeError(FinPyError):
    def __init__(self, message: str = "", *, trade_id: str | None = None) -> None:
        super().__init__(message)
        self.trade_id = trade_id


class InsufficientDataError(FinPyError):
    def __init__(
        self,
        message: str = "",
        *,
        required_points: int | None = None,
        available: int | None = None,
    ) -> None:
        super().__init__(message)
        self.required_points = required_points
        self.available = available


class InvalidParameterError(FinPyError):
    def __init__(self, message: str = "", *, parameter_name: str | None = None) -> None:
        super().__init__(message)
        self.parameter_name = parameter_name


class InvalidPortfolioError(FinPyError):
    pass


class InvalidPositionError(FinPyError):
    pass


class ConvergenceError(FinPyError):
    def __init__(
        self,
        message: str = "",
        *,
        iterations: int | None = None,
        tolerance: float | None = None,
    ) -> None:
        super().__init__(message)
        self.iterations = iterations
        self.tolerance = tolerance


class ValuationError(FinPyError):
    pass


class MarketDataError(FinPyError):
    def __init__(self, message: str = "", *, symbol: str | None = None) -> None:
        super().__init__(message)
        self.symbol = symbol


class CurveConstructionError(FinPyError):
    pass


class InterpolationError(FinPyError):
    pass


class DateMismatchError(FinPyError):
    def __init__(
        self,
        message: str = "",
        *,
        expected: str | None = None,
        actual: str | None = None,
    ) -> None:
        super().__init__(message)
        self.expected = expected
        self.actual = actual


class NotImplementedInModeError(FinPyError):
    def __init__(self, message: str = "", *, mode: str | None = None) -> None:
        super().__init__(message)
        self.mode = mode


class NegativeRateError(FinPyError):
    pass


class DivisionByZeroError(FinPyError):
    pass


class CalculationError(FinPyError):
    pass


class DataNotFoundError(FinPyError):
    def __init__(self, message: str = "", *, key: str | None = None) -> None:
        super().__init__(message)
        self.key = key


class UnsupportedModeError(FinPyError):
    def __init__(self, message: str = "", *, mode: str | None = None) -> None:
        super().__init__(message)
        self.mode = mode


class PeriodMismatchError(FinPyError):
    def __init__(
        self,
        message: str = "",
        *,
        expected: int | None = None,
        actual: int | None = None,
    ) -> None:
        super().__init__(message)
        self.expected = expected
        self.actual = actual


class ValidationAggregateError(FinPyError):
    def __init__(
        self,
        message: str = "",
        *,
        errors: list[BaseException] | None = None,
    ) -> None:
        super().__init__(message)
        self.errors: list[BaseException] = list(errors) if errors else []


class CashflowStructureError(FinPyError):
    pass


class PriceOutOfRangeError(FinPyError):
    pass


class TimeSeriesError(FinPyError):
    pass


class OverlappingDataError(FinPyError):
    pass


class InvalidDateError(FinPyError):
    def __init__(self, message: str = "", *, date_str: str | None = None) -> None:
        super().__init__(message)
        self.date_str = date_str


class BenchmarkMismatchError(FinPyError):
    pass


class InsufficientObservationsError(FinPyError):
    def __init__(
        self,
        message: str = "",
        *,
        required: int | None = None,
        available: int | None = None,
    ) -> None:
        super().__init__(message)
        self.required = required
        self.available = available


class OptimizationError(FinPyError):
    pass


class ConfigurationError(FinPyError):
    pass


class FileFormatError(FinPyError):
    pass


class ImportError(FinPyError):  # noqa: A001
    pass


__all__ = [
    "FinPyError",
    "InvalidCashflowError",
    "InvalidInstrumentError",
    "NoSolutionFoundError",
    "UnknownCurrencyError",
    "RateNotAvailableError",
    "SchemaValidationError",
    "MigrationError",
    "InvalidTradeError",
    "InsufficientDataError",
    "InvalidParameterError",
    "InvalidPortfolioError",
    "InvalidPositionError",
    "ConvergenceError",
    "ValuationError",
    "MarketDataError",
    "CurveConstructionError",
    "InterpolationError",
    "DateMismatchError",
    "NotImplementedInModeError",
    "NegativeRateError",
    "DivisionByZeroError",
    "CalculationError",
    "DataNotFoundError",
    "UnsupportedModeError",
    "PeriodMismatchError",
    "ValidationAggregateError",
    "CashflowStructureError",
    "PriceOutOfRangeError",
    "TimeSeriesError",
    "OverlappingDataError",
    "InvalidDateError",
    "BenchmarkMismatchError",
    "InsufficientObservationsError",
    "OptimizationError",
    "ConfigurationError",
    "FileFormatError",
    "ImportError",
]

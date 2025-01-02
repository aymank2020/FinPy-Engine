"""ISO 4217 currency code helpers.

The module exposes a small in-memory registry of currency codes, names, and
symbols. The internal mappings ``_VALID_CURRENCIES``, ``_CURRENCY_NAMES`` and
``_CURRENCY_SYMBOLS`` are mutated by :func:`add_currency` so tests can grow the
registry; the test suite snapshots them per-test via the autouse fixture in
``tests/conftest.py``.
"""

from __future__ import annotations


_VALID_CURRENCIES: set[str] = {
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
    "SEK", "NOK", "DKK", "CNY", "INR", "BRL", "MXN", "SGD",
    "HKD", "KRW", "ZAR", "TRY", "SAR", "AED", "EGP",
}

_CURRENCY_NAMES: dict[str, str] = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "CHF": "Swiss Franc",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "DKK": "Danish Krone",
    "CNY": "Chinese Yuan",
    "INR": "Indian Rupee",
    "BRL": "Brazilian Real",
    "MXN": "Mexican Peso",
    "SGD": "Singapore Dollar",
    "HKD": "Hong Kong Dollar",
    "KRW": "South Korean Won",
    "ZAR": "South African Rand",
    "TRY": "Turkish Lira",
    "SAR": "Saudi Riyal",
    "AED": "UAE Dirham",
    "EGP": "Egyptian Pound",
}

_CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "\u20ac",
    "GBP": "\u00a3",
    "JPY": "\u00a5",
    "CHF": "Fr",
    "CAD": "C$",
    "AUD": "A$",
    "NZD": "NZ$",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
    "CNY": "\u00a5",
    "INR": "\u20b9",
    "BRL": "R$",
    "MXN": "Mex$",
    "SGD": "S$",
    "HKD": "HK$",
    "KRW": "\u20a9",
    "ZAR": "R",
    "TRY": "\u20ba",
    "SAR": "SR",
    "AED": "AED",
    "EGP": "E\u00a3",
}


def is_valid_currency(code: str) -> bool:
    """Return ``True`` when ``code`` is a registered ISO 4217 currency."""
    if not isinstance(code, str) or len(code) != 3:
        return False
    return code.upper() in _VALID_CURRENCIES


def list_currencies() -> list[str]:
    """Return the registered currency codes sorted alphabetically."""
    return sorted(_VALID_CURRENCIES)


def currency_name(code: str) -> str:
    """Return the human-readable name for ``code``."""
    if not isinstance(code, str) or not code:
        raise ValueError("currency code must be a non-empty string")
    upper = code.upper()
    if upper not in _CURRENCY_NAMES or not _CURRENCY_NAMES[upper]:
        raise ValueError(f"unknown currency code: {code}")
    return _CURRENCY_NAMES[upper]


def currency_symbol(code: str) -> str:
    """Return the conventional display symbol for ``code``."""
    if not isinstance(code, str) or not code:
        raise ValueError("currency code must be a non-empty string")
    upper = code.upper()
    if upper not in _CURRENCY_SYMBOLS or not _CURRENCY_SYMBOLS[upper]:
        raise ValueError(f"unknown currency symbol for: {code}")
    return _CURRENCY_SYMBOLS[upper]


def add_currency(code: str, name: str, symbol: str | None = None) -> None:
    """Register a currency in the in-memory tables.

    A blank ``name`` registers the code as valid but causes :func:`currency_name`
    to raise. A missing ``symbol`` causes :func:`currency_symbol` to raise.
    Existing entries are overwritten.
    """
    if not isinstance(code, str) or len(code) != 3:
        raise ValueError("currency code must be a 3-letter string")
    upper = code.upper()
    _VALID_CURRENCIES.add(upper)
    _CURRENCY_NAMES[upper] = name
    if symbol is not None:
        _CURRENCY_SYMBOLS[upper] = symbol
    else:
        # remove any stale symbol so currency_symbol raises predictably
        _CURRENCY_SYMBOLS.pop(upper, None)


__all__ = [
    "is_valid_currency",
    "list_currencies",
    "currency_name",
    "currency_symbol",
    "add_currency",
]

import copy
import pytest
from hypothesis import settings, Phase


settings.register_profile("ci", max_examples=200, phases=[Phase.reuse, Phase.generate, Phase.shrink])
settings.load_profile("ci")


@pytest.fixture(autouse=True)
def _isolate_iso4217_state():
    from finpy.fx import iso4217
    saved_valid = copy.copy(iso4217._VALID_CURRENCIES)
    saved_names = copy.copy(iso4217._CURRENCY_NAMES)
    saved_symbols = copy.copy(iso4217._CURRENCY_SYMBOLS)
    yield
    iso4217._VALID_CURRENCIES.clear()
    iso4217._VALID_CURRENCIES.update(saved_valid)
    iso4217._CURRENCY_NAMES.clear()
    iso4217._CURRENCY_NAMES.update(saved_names)
    iso4217._CURRENCY_SYMBOLS.clear()
    iso4217._CURRENCY_SYMBOLS.update(saved_symbols)

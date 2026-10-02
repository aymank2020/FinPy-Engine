"""References for the legacy score contract, not the 2014 DSR probability.

Score constants were calculated independently from sample moments, the
documented legacy sampling-variance heuristic, and normal quantiles. Quantile
constants are standard normal percentiles; CDF checks use erf independently.
"""

from decimal import Decimal
import math

import pytest

from finpy.risk.sharpe import _inverse_norm, deflated_sharpe_ratio


RETURNS = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]


@pytest.mark.parametrize("risk_free,periods,expected", [
    (0.0, None, [0.46770717334674256, 0.2648236042929234, -0.14692839840534672, -0.52009940234381169]),
    (0.005, None, [0.1559023911155808, -0.033587277202325683, -0.41815637160657371, -0.76669149493833066]),
    (0.0, 252, [7.4246212024587477, 6.7189737979492934, 5.2868630885377819, 3.9889405825633717]),
    (0.005, 252, [2.474873734152915, 2.1489236314382971, 1.4874082204152947, 0.88787654009674966]),
])
@pytest.mark.parametrize("index,trials", list(enumerate([1, 2, 10, 100])))
def test_legacy_score_reference(risk_free, periods, expected, index, trials):
    score = deflated_sharpe_ratio(RETURNS, risk_free, trials, periods)
    assert isinstance(score, Decimal)
    assert score.is_finite()
    assert float(score) == pytest.approx(expected[index], rel=0, abs=1e-12)


@pytest.mark.parametrize("probability,expected", [
    (1e-6, -4.753424308822899),
    (0.01, -2.326347874040841),
    (0.05, -1.6448536269514722),
    (0.25, -0.6744897501960817),
    (0.5, 0.0),
    (0.75, 0.6744897501960817),
    (0.95, 1.6448536269514722),
    (0.99, 2.326347874040841),
    (1 - 1e-6, 4.753424308817087),
])
def test_normal_quantile_reference_and_independent_cdf(probability, expected):
    quantile = _inverse_norm(probability)
    assert quantile == pytest.approx(expected, rel=0, abs=1e-12)
    cdf = 0.5 * (1 + math.erf(quantile / math.sqrt(2)))
    assert abs(cdf - probability) <= 1e-10


@pytest.mark.parametrize("probability", [0, 1, -0.1, 1.1, math.nan, math.inf, -math.inf])
def test_normal_quantile_rejects_invalid_probability(probability):
    with pytest.raises(ValueError, match="probability"):
        _inverse_norm(probability)


def test_default_preserves_score_units_and_large_trial_count_is_finite():
    assert deflated_sharpe_ratio(RETURNS, periods_per_year=252) > 1
    large = deflated_sharpe_ratio(RETURNS, num_trials=10**20)
    assert large.is_finite()
    assert large < deflated_sharpe_ratio(RETURNS, num_trials=100)


@pytest.mark.parametrize("trials", [0, -1, 1.5, 2.0, True, "2", Decimal(2), math.nan, math.inf])
def test_trial_count_requires_positive_integer(trials):
    with pytest.raises(ValueError, match="num_trials.*positive integer"):
        deflated_sharpe_ratio(RETURNS, num_trials=trials)


def test_trial_count_outside_float_range_is_explicit_error():
    with pytest.raises(ValueError, match="num_trials.*floating-point range"):
        deflated_sharpe_ratio(RETURNS, num_trials=10**400)


@pytest.mark.parametrize("periods", [0, -1, 1.5, 252.0, True, "252", Decimal(252), math.nan, math.inf])
def test_period_frequency_requires_positive_integer(periods):
    with pytest.raises(ValueError, match="periods_per_year.*positive integer"):
        deflated_sharpe_ratio(RETURNS, periods_per_year=periods)


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, True, "0.01", 10**400])
def test_nonfinite_or_nonnumeric_return_is_explicit_error(invalid):
    with pytest.raises(ValueError, match="returns and risk_free_rate must be finite numbers"):
        deflated_sharpe_ratio([*RETURNS[:-1], invalid])


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, True, "0.01", 10**400])
def test_nonfinite_or_nonnumeric_risk_free_is_explicit_error(invalid):
    with pytest.raises(ValueError, match="returns and risk_free_rate must be finite numbers"):
        deflated_sharpe_ratio(RETURNS, risk_free_rate=invalid)


@pytest.mark.parametrize("digits", [1.5, True, "4", math.nan, math.inf])
def test_rounding_digits_require_integer(digits):
    with pytest.raises(ValueError, match="ndigits must be an integer"):
        deflated_sharpe_ratio(RETURNS, ndigits=digits)


def test_undefined_legacy_variance_is_rejected_without_clamp():
    with pytest.raises(ValueError, match="Legacy Sharpe variance estimate"):
        deflated_sharpe_ratio([0.099, 0.101, 0.099, 0.101], num_trials=10)


@pytest.mark.parametrize("returns,expected", [
    ([0.099, 0.101, 0.099, 0.101], 86.60254037844378),
    ([1e100, -1e100, 1e100, -1e100], 0.0),
])
def test_single_trial_needs_observed_score_without_unused_variance(returns, expected):
    score = deflated_sharpe_ratio(returns)
    assert score.is_finite()
    assert float(score) == pytest.approx(expected, rel=0, abs=1e-12)


@pytest.mark.parametrize("returns,periods", [
    ([1e308, -1e308, 1e308, -1e308], None),
    ([1e-100, -1e-100, 1e-100, -1e-100], None),
    (RETURNS, 10**400),
])
def test_finite_input_outside_estimator_range_is_explicit_error(returns, periods):
    with pytest.raises(ValueError, match="Legacy Sharpe (score|variance estimate)"):
        deflated_sharpe_ratio(returns, periods_per_year=periods, num_trials=2)


def test_single_trial_zero_variance_preserves_existing_zero_score():
    assert deflated_sharpe_ratio([0.01] * 4) == Decimal(0)


@pytest.mark.parametrize("trials,expected", [(2, -0.18376126424937828), (10, -0.5567045682631994), (100, -0.8947032331366038)])
def test_multiple_trials_retain_legacy_constant_series_penalty(trials, expected):
    score = deflated_sharpe_ratio([0.01] * 8, num_trials=trials)
    assert float(score) == pytest.approx(expected, rel=0, abs=1e-12)


@pytest.mark.parametrize("trials,expected", [(1, "0.4677"), (2, "0.2648"), (10, "-0.1469"), (100, "-0.5201")])
def test_legacy_score_decimal_rounding(trials, expected):
    assert deflated_sharpe_ratio(RETURNS, num_trials=trials, ndigits=4) == Decimal(expected)

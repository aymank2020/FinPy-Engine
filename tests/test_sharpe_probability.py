"""Primary-paper probability references; legacy score has separate tests."""

from decimal import Decimal
import inspect
import math

import pytest

from finpy.risk import deflated_sharpe_probability_from_stats, probabilistic_sharpe
from finpy.risk.sharpe import deflated_sharpe_ratio


RETURNS = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
BASE_STATS = dict(
    n_observations=1250, skewness=-3, raw_kurtosis=10,
    trial_sharpe_variance=0.5 / 250, num_independent_trials=100,
)


@pytest.mark.parametrize("trials,skew,kurtosis,expected,published", [
    (100, -3, 10, 0.9003968344493904, 0.9004),
    (46, -3, 10, 0.9505017068755786, 0.9505),
    (88, 0, 3, 0.9504908166760138, 0.9505),
])
def test_2014_author_probability_examples(trials, skew, kurtosis, expected, published):
    stats = {**BASE_STATS, "num_independent_trials": trials, "skewness": skew, "raw_kurtosis": kurtosis}
    probability = deflated_sharpe_probability_from_stats(2.5 / math.sqrt(250), **stats)
    assert isinstance(probability, Decimal)
    assert probability.is_finite()
    assert 0 <= probability <= 1
    assert float(probability) == pytest.approx(expected, rel=0, abs=1e-12)
    assert abs(float(probability) - published) <= 5e-5


@pytest.mark.parametrize("trial_variance", [0, 0.002, 1e100])
def test_single_trial_is_psr_at_zero_threshold(trial_variance):
    stats = {**BASE_STATS, "num_independent_trials": 1, "trial_sharpe_variance": trial_variance}
    probability = deflated_sharpe_probability_from_stats(2.5 / math.sqrt(250), **stats)
    assert float(probability) == pytest.approx(0.9999968595078976, rel=0, abs=1e-15)


def test_zero_trial_variance_has_zero_search_threshold():
    stats = {**BASE_STATS, "trial_sharpe_variance": 0}
    single = deflated_sharpe_probability_from_stats(0.15, **{**stats, "num_independent_trials": 1})
    multiple = deflated_sharpe_probability_from_stats(0.15, **stats)
    assert multiple == single


def test_more_independent_trials_lower_probability_including_large_count():
    probabilities = [
        deflated_sharpe_probability_from_stats(2.5 / math.sqrt(250), **{**BASE_STATS, "num_independent_trials": n})
        for n in [1, 2, 10, 46, 100, 10**20]
    ]
    assert all(p.is_finite() for p in probabilities)
    assert all(a > b for a, b in zip(probabilities, probabilities[1:]))


def test_more_trial_variance_lowers_probability():
    probabilities = [
        deflated_sharpe_probability_from_stats(0.15, **{**BASE_STATS, "trial_sharpe_variance": variance})
        for variance in [0, 0.001, 0.002, 0.01]
    ]
    assert all(a > b for a, b in zip(probabilities, probabilities[1:]))


def test_stats_api_matches_sample_psr_without_inferring_trial_variance():
    # S uses sample SD; g3/g4 use population-standardized central moments.
    probability = deflated_sharpe_probability_from_stats(
        0.46770717334674267, n_observations=8, skewness=-11 / 24,
        raw_kurtosis=2.3449074074074074, trial_sharpe_variance=0.1,
        num_independent_trials=1,
    )
    assert float(probability) == pytest.approx(float(probabilistic_sharpe(RETURNS)), rel=0, abs=1e-12)
    assert float(probability) == pytest.approx(0.8622279371626578, rel=0, abs=1e-12)
    assert deflated_sharpe_ratio(RETURNS, ndigits=4) == Decimal("0.4677")
    assert probability != deflated_sharpe_ratio(RETURNS)


def test_stats_variance_and_other_statistics_are_required_keyword_arguments():
    signature = inspect.signature(deflated_sharpe_probability_from_stats)
    for name in BASE_STATS:
        parameter = signature.parameters[name]
        assert parameter.kind == inspect.Parameter.KEYWORD_ONLY
        assert parameter.default == inspect.Parameter.empty
    incomplete = {k: v for k, v in BASE_STATS.items() if k != "trial_sharpe_variance"}
    with pytest.raises(TypeError, match="trial_sharpe_variance"):
        deflated_sharpe_probability_from_stats(0.15, **incomplete)


@pytest.mark.parametrize("target,expected", [
    (0.0, 0.8622279371626578),
    (0.1, 0.8043466098857269),
    (0.5, 0.4699937740537978),
])
def test_psr_independent_population_moment_references(target, expected):
    probability = probabilistic_sharpe(RETURNS, target_sharpe=target)
    assert isinstance(probability, Decimal)
    assert float(probability) == pytest.approx(expected, rel=0, abs=1e-12)


def test_psr_risk_free_is_per_observation():
    assert float(probabilistic_sharpe(RETURNS, 0.005)) == pytest.approx(0.6543076184595922, rel=0, abs=1e-12)


@pytest.mark.parametrize("periods", [1, 12, 252, 365])
def test_annual_target_converts_to_native_units(periods):
    native = probabilistic_sharpe(RETURNS, target_sharpe=0.1)
    annual = probabilistic_sharpe(RETURNS, target_sharpe=0.1 * math.sqrt(periods), periods_per_year=periods)
    zero_native = probabilistic_sharpe(RETURNS)
    zero_annual = probabilistic_sharpe(RETURNS, periods_per_year=periods)
    assert float(annual) == pytest.approx(float(native), rel=0, abs=1e-12)
    assert zero_annual == zero_native


@pytest.mark.parametrize("scale", [1e-200, 1e-100, 100, 1e100, 1e200])
def test_return_and_risk_free_units_do_not_change_probability(scale):
    actual = probabilistic_sharpe([r * scale for r in RETURNS], risk_free_rate=0.005 * scale)
    assert float(actual) == pytest.approx(0.6543076184595922, rel=0, abs=1e-12)


@pytest.mark.parametrize("sign,expected", [(1, Decimal(1)), (-1, Decimal(0))])
def test_symmetric_near_constant_population_moments_have_valid_variance(sign, expected):
    assert probabilistic_sharpe([sign * x for x in [0.099, 0.101, 0.099, 0.101]]) == expected


def test_symmetric_sample_at_observed_target_is_half():
    probability = probabilistic_sharpe([0.099, 0.101, 0.099, 0.101], target_sharpe=86.60254037844386)
    assert float(probability) == pytest.approx(0.5, rel=0, abs=1e-12)


def test_psr_rounding_keeps_existing_decimal_quantization_contract():
    assert probabilistic_sharpe(RETURNS, ndigits=4) == Decimal("0.8622")
    # The existing Decimal(10)**(-ndigits) quantum has exponent 0 for -1.
    assert probabilistic_sharpe(RETURNS, ndigits=-1) == Decimal(1)


def test_lower_tail_probability_does_not_cancel_to_zero():
    probability = deflated_sharpe_probability_from_stats(
        -10, n_observations=2, skewness=0, raw_kurtosis=1,
        trial_sharpe_variance=0, num_independent_trials=1,
    )
    assert probability > 0
    assert float(probability) == pytest.approx(7.619853024160593e-24, rel=1e-14, abs=0)


@pytest.mark.parametrize("field", ["observed_sharpe", "skewness", "raw_kurtosis", "trial_sharpe_variance"])
@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, True, "0.1", Decimal("sNaN"), Decimal("1e-400"), 10**400])
def test_stats_reject_nonfinite_nonnumeric_and_unrepresentable_values(field, invalid):
    stats = {**BASE_STATS, "observed_sharpe": 0.15, field: invalid}
    with pytest.raises(ValueError, match=field):
        deflated_sharpe_probability_from_stats(**stats)


@pytest.mark.parametrize("field", ["n_observations", "num_independent_trials"])
@pytest.mark.parametrize("invalid", [0, -1, 2.0, 2.5, True, "2", Decimal(2), math.nan, math.inf, 10**400])
def test_stats_require_actual_integer_counts(field, invalid):
    with pytest.raises(ValueError, match=field):
        deflated_sharpe_probability_from_stats(0.15, **{**BASE_STATS, field: invalid})


def test_at_least_two_observations_are_required():
    with pytest.raises(ValueError, match="n_observations"):
        deflated_sharpe_probability_from_stats(0.15, **{**BASE_STATS, "n_observations": 1})


def test_negative_trial_variance_is_not_clamped():
    with pytest.raises(ValueError, match="trial_sharpe_variance must be nonnegative"):
        deflated_sharpe_probability_from_stats(0.15, **{**BASE_STATS, "trial_sharpe_variance": -0.001})


@pytest.mark.parametrize("skew,kurtosis", [(0, 0.9), (2, 4.9), (1e200, 1e300)])
def test_incoherent_raw_moments_are_rejected(skew, kurtosis):
    with pytest.raises(ValueError, match="raw_kurtosis.*skewness"):
        deflated_sharpe_probability_from_stats(0.15, **{**BASE_STATS, "skewness": skew, "raw_kurtosis": kurtosis})


def test_four_ulp_pearson_boundary_allowance_does_not_relax_model_variance():
    floor = 2.0
    rounded = floor
    for _ in range(4):
        rounded -= math.ulp(floor)
    stats = {**BASE_STATS, "skewness": 1, "raw_kurtosis": rounded}
    assert deflated_sharpe_probability_from_stats(0.15, **stats).is_finite()
    with pytest.raises(ValueError, match="raw_kurtosis"):
        deflated_sharpe_probability_from_stats(0.15, **{**stats, "raw_kurtosis": rounded - math.ulp(floor)})
    with pytest.raises(ValueError, match="sampling variance must be positive"):
        deflated_sharpe_probability_from_stats(2, **stats)


def test_zero_sampling_variance_is_explicit_model_error():
    with pytest.raises(ValueError, match="sampling variance must be positive"):
        deflated_sharpe_probability_from_stats(2, **{**BASE_STATS, "skewness": 1, "raw_kurtosis": 2})


def test_decimal_and_integer_statistics_are_supported_at_float_precision():
    values = {k: Decimal(str(v)) if k in ["skewness", "raw_kurtosis", "trial_sharpe_variance"] else v for k, v in BASE_STATS.items()}
    probability = deflated_sharpe_probability_from_stats(Decimal(str(2.5 / math.sqrt(250))), **values)
    assert float(probability) == pytest.approx(0.9003968344493904, rel=0, abs=1e-12)
    assert deflated_sharpe_probability_from_stats(0, **{**BASE_STATS, "num_independent_trials": 1}) == Decimal("0.5")


@pytest.mark.parametrize("field", ["return", "risk_free_rate", "target_sharpe"])
@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, True, "0.1", Decimal("sNaN"), Decimal("1e-400"), 10**400])
def test_psr_rejects_invalid_numeric_inputs(field, invalid):
    values = [*RETURNS]
    kwargs = {}
    if field == "return":
        values[0] = invalid
    else:
        kwargs[field] = invalid
    with pytest.raises(ValueError, match="returns" if field == "return" else field):
        probabilistic_sharpe(values, **kwargs)


@pytest.mark.parametrize("periods", [0, -1, 252.0, 1.5, True, "252", Decimal(252), math.nan, math.inf, 10**400])
def test_psr_requires_positive_integer_frequency(periods):
    with pytest.raises(ValueError, match="periods_per_year"):
        probabilistic_sharpe(RETURNS, periods_per_year=periods)


@pytest.mark.parametrize("digits", [1.5, True, "4", math.nan, math.inf, 100])
def test_psr_invalid_precision_is_explicit_error(digits):
    with pytest.raises(ValueError, match="ndigits"):
        probabilistic_sharpe(RETURNS, ndigits=digits)


@pytest.mark.parametrize("returns", [[0.0] * 4, [0.01] * 4, [Decimal(".01")] * 4])
def test_psr_rejects_undefined_constant_return_model(returns):
    with pytest.raises(ValueError, match="undefined for constant returns"):
        probabilistic_sharpe(returns)


def test_psr_rejects_nonfinite_observed_sharpe_from_finite_inputs():
    with pytest.raises(ValueError, match="Observed Sharpe"):
        probabilistic_sharpe(RETURNS, risk_free_rate=1e308)


def test_sampling_variance_range_error_is_not_a_fake_probability():
    with pytest.raises(ValueError, match="sampling variance"):
        deflated_sharpe_probability_from_stats(1e308, **{**BASE_STATS, "skewness": 1e10, "raw_kurtosis": 1e20})


def test_two_point_empirical_moments_at_rounded_pearson_equality_are_valid():
    probability = deflated_sharpe_probability_from_stats(
        1 / math.sqrt(3), n_observations=3, skewness=0.7071067811865478,
        raw_kurtosis=1.5000000000000002, trial_sharpe_variance=0,
        num_independent_trials=1,
    )
    assert probability.is_finite()
    assert float(probability) == pytest.approx(float(probabilistic_sharpe([0, 0, 1])), rel=0, abs=1e-12)


@pytest.mark.parametrize("risk_free,target,expected", [
    (1e308, 1e308, 6.220960574271784e-16),
    (-1e308, -1e308, 0.9999999999999993),
])
def test_opposing_large_native_sharpe_and_target_do_not_overflow_z(risk_free, target, expected):
    # Sample SD=1, population kurtosis=1.5, SE approximately 2.5e307.
    # The true z is +/-8, rather than an infinite subtraction result.
    probability = probabilistic_sharpe([-1, 0, 1], risk_free_rate=risk_free, target_sharpe=target)
    assert Decimal(0) < probability < Decimal(1)
    assert float(probability) == pytest.approx(expected, rel=2e-13, abs=0)


def test_large_same_sign_native_target_preserves_cancellation():
    assert probabilistic_sharpe([-1, 0, 1], risk_free_rate=-1e308, target_sharpe=1e308) == Decimal("0.5")


def test_dsr_large_coherent_stats_keep_finite_dispersion_and_probability():
    probability = deflated_sharpe_probability_from_stats(
        -1e308, n_observations=3, skewness=0, raw_kurtosis=3,
        trial_sharpe_variance=1e308, num_independent_trials=100,
    )
    assert float(probability) == pytest.approx(0.02275013194817921, rel=0, abs=1e-15)

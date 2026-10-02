from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional
import math
from statistics import NormalDist


_EULER_MASCHERONI = 0.5772156649015329


def sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    std_dev = math.sqrt(variance)
    if std_dev == 0:
        return Decimal(0)
    excess = mean_ret - risk_free_rate
    result = Decimal(str(excess)) / Decimal(str(std_dev))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def adjusted_sharpe(returns: list[float], risk_free_rate: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 3:
        raise ValueError("Need at least 3 returns for adjusted Sharpe")
    n = len(returns)
    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return Decimal(0)
    std_dev = math.sqrt(variance)
    excess = mean_ret - risk_free_rate
    sr = excess / std_dev
    skewness = sum((r - mean_ret) ** 3 for r in returns) / n
    skewness = skewness / (std_dev ** 3)
    excess_kurtosis = sum((r - mean_ret) ** 4 for r in returns) / n
    excess_kurtosis = excess_kurtosis / (std_dev ** 4) - 3.0
    adj = sr * (1 + skewness / 6 - excess_kurtosis / 24)
    result = Decimal(str(adj))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _sharpe_ratio_value(returns: list[float], risk_free_rate: float) -> float:
    n = len(returns)
    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std_dev = math.sqrt(variance)
    return (mean_ret - risk_free_rate) / std_dev


def probabilistic_sharpe(returns: list[float], risk_free_rate: float = 0.0, target_sharpe: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    """Estimate PSR with native-frequency Sharpe and population moments.

    The risk-free rate is per observation. With periods_per_year supplied,
    target_sharpe is annualized and is converted back to observation units.
    Constant returns have undefined Sharpe/moments and raise ValueError.
    The probability model uses T-1 and differs from the old implementation.
    """
    if len(returns) < 3:
        raise ValueError("Need at least 3 returns for probabilistic Sharpe")
    values = [_finite_statistic(r, "returns") for r in returns]
    risk_free = _finite_statistic(risk_free_rate, "risk_free_rate")
    target = _finite_statistic(target_sharpe, "target_sharpe")
    if periods_per_year is not None:
        _integer_count(periods_per_year, "periods_per_year", minimum=1)
        target /= math.sqrt(periods_per_year)
    n = len(returns)
    scale = max(abs(r) for r in values)
    if scale == 0:
        raise ValueError("Sharpe and moments are undefined for constant returns")
    scaled = [r / scale for r in values]
    mean = math.fsum(scaled) / n
    centered = [r - mean for r in scaled]
    population_variance = math.fsum(r * r for r in centered) / n
    if population_variance == 0:
        raise ValueError("Sharpe and moments are undefined for constant returns")
    population_std = math.sqrt(population_variance)
    sample_std = math.sqrt(population_variance * n / (n - 1))
    sr = (mean - risk_free / scale) / sample_std
    if not math.isfinite(sr):
        raise ValueError("Observed Sharpe exceeds the supported floating-point range")
    standardized = [r / population_std for r in centered]
    # With population-standardized Z, E[(Z-SR*(Z²-1)/2)²] equals
    # 1-skew*SR+(raw_kurtosis-1)*SR²/4. Evaluating the squares directly
    # preserves this nonnegative empirical variance without clamping.
    influences = [(z - 0.5 * sr * (z * z - 1)) / math.sqrt(n) for z in standardized]
    dispersion = math.hypot(*influences)
    result = _sharpe_probability(sr, target, n, dispersion)
    if ndigits is not None:
        if isinstance(ndigits, bool) or not isinstance(ndigits, int):
            raise ValueError("ndigits must be an integer")
        try:
            result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError("ndigits exceeds the current Decimal precision") from exc
    return result


def deflated_sharpe_probability_from_stats(
    observed_sharpe: float,
    *,
    n_observations: int,
    skewness: float,
    raw_kurtosis: float,
    trial_sharpe_variance: float,
    num_independent_trials: int,
) -> Decimal:
    """Return the 2014 DSR probability from explicit native-frequency stats.

    trial_sharpe_variance is variance across trials, never an estimate from
    the selected strategy's returns. Raw kurtosis must satisfy the Pearson
    moment bound, raw_kurtosis >= 1 + skewness**2. Counts are actual integers.
    N=1 uses the zero expected maximum of a zero-mean null. The finite-N
    maximum approximation for N>1 and trial independence are caller assumptions.
    """
    sr = _finite_statistic(observed_sharpe, "observed_sharpe")
    skew = _finite_statistic(skewness, "skewness")
    kurtosis = _finite_statistic(raw_kurtosis, "raw_kurtosis")
    trial_variance = _finite_statistic(trial_sharpe_variance, "trial_sharpe_variance")
    _integer_count(n_observations, "n_observations", minimum=2)
    _integer_count(num_independent_trials, "num_independent_trials", minimum=1)
    if trial_variance < 0:
        raise ValueError("trial_sharpe_variance must be nonnegative")
    moment_floor = 1 + skew * skew
    if not math.isfinite(moment_floor):
        raise ValueError("raw_kurtosis must be at least 1 + skewness**2")
    moment_slack = kurtosis - moment_floor
    if moment_slack < 0:
        # Empirical moments at Pearson equality can differ by a few rounding
        # steps. Only this four-ULP boundary allowance is normalized to zero.
        if -moment_slack > 4 * math.ulp(moment_floor):
            raise ValueError("raw_kurtosis must be at least 1 + skewness**2")
        moment_slack = 0.0
    # Completing the square gives exactly the paper's variance numerator.
    dispersion = math.hypot(1 - 0.5 * skew * sr, 0.5 * sr * math.sqrt(moment_slack))
    threshold = 0.0
    if num_independent_trials > 1 and trial_variance > 0:
        tail = 1.0 / num_independent_trials
        expected_max = -(1 - _EULER_MASCHERONI) * _inverse_norm(tail)
        expected_max -= _EULER_MASCHERONI * _inverse_norm(tail / math.e)
        threshold = math.sqrt(trial_variance) * expected_max
    if not math.isfinite(threshold):
        raise ValueError("Search threshold exceeds the supported floating-point range")
    return _sharpe_probability(sr, threshold, n_observations, dispersion)


def _finite_statistic(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{name} must be a finite number")
    try:
        numeric = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number within floating-point range") from exc
    if not math.isfinite(numeric) or (numeric == 0 and value != 0):
        raise ValueError(f"{name} must be a finite number within floating-point range")
    return numeric


def _integer_count(value: int, name: str, *, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer at least {minimum}")
    try:
        finite = math.isfinite(value)
    except OverflowError as exc:
        raise ValueError(f"{name} exceeds the supported floating-point range") from exc
    if not finite:
        raise ValueError(f"{name} exceeds the supported floating-point range")


def _sharpe_probability(sr: float, threshold: float, n: int, dispersion: float) -> Decimal:
    if not math.isfinite(dispersion) or dispersion <= 0:
        raise ValueError("Sharpe sampling variance must be positive and finite")
    standard_error = dispersion / math.sqrt(n - 1)
    if standard_error == 0:
        raise ValueError("Sharpe standard error is outside the supported floating-point range")
    difference = sr - threshold
    if math.isfinite(difference):
        z_stat = difference / standard_error
    else:
        # Finite opposing inputs can overflow their difference even when z
        # is moderate. Divide first here; preserve direct subtraction when
        # finite so close same-sign inputs do not become inf-inf.
        z_stat = sr / standard_error - threshold / standard_error
    # erfc retains small lower-tail probabilities lost by 1+erf(z).
    return Decimal(str(0.5 * math.erfc(-z_stat / math.sqrt(2))))


def _compute_skewness_stat(returns: list[float]) -> float:
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    return sum((r - mean) ** 3 for r in returns) / (n * std ** 3)


def _compute_kurtosis_stat(returns: list[float]) -> float:
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    return sum((r - mean) ** 4 for r in returns) / (n * std ** 4)


def deflated_sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0, num_trials: int = 1, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    """Return the legacy Sharpe score minus an estimated search penalty.

    The result has Sharpe units, not probability units. The penalty retains
    this API's sampling-variance heuristic for the supplied returns; it does
    not estimate variance across trials or implement the 2014 DSR probability.
    With one trial, the expected maximum under a zero-mean null is zero.
    Annualization and moment estimates retain their existing conventions.
    """
    if len(returns) < 4:
        raise ValueError("Need at least 4 returns for deflated Sharpe")
    if isinstance(num_trials, bool) or not isinstance(num_trials, int) or num_trials < 1:
        raise ValueError("num_trials must be a positive integer")
    if periods_per_year is not None and (
        isinstance(periods_per_year, bool)
        or not isinstance(periods_per_year, int)
        or periods_per_year < 1
    ):
        raise ValueError("periods_per_year must be a positive integer")
    if ndigits is not None and (isinstance(ndigits, bool) or not isinstance(ndigits, int)):
        raise ValueError("ndigits must be an integer")
    try:
        finite_inputs = all(not isinstance(r, bool) and math.isfinite(r) for r in returns)
        finite_inputs = finite_inputs and not isinstance(risk_free_rate, bool) and math.isfinite(risk_free_rate)
    except (TypeError, OverflowError) as exc:
        raise ValueError("returns and risk_free_rate must be finite numbers") from exc
    if not finite_inputs:
        raise ValueError("returns and risk_free_rate must be finite numbers")
    n = len(returns)
    try:
        sr_obs = _sharpe_ratio_value(returns, risk_free_rate)
        if periods_per_year is not None:
            sr_obs *= math.sqrt(periods_per_year)
    except (TypeError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError("Legacy Sharpe score is undefined for these inputs") from exc
    if not math.isfinite(sr_obs):
        raise ValueError("Legacy Sharpe score must be finite")
    e_max_sr = 0.0
    if num_trials > 1:
        try:
            skewness = _compute_skewness_stat(returns)
            excess_kurtosis = _compute_kurtosis_stat(returns)
            var_sr = 1 + 0.5 * sr_obs * sr_obs
            var_sr += -skewness * sr_obs + (excess_kurtosis - 3) * sr_obs * sr_obs / 4
        except (TypeError, OverflowError, ZeroDivisionError) as exc:
            raise ValueError("Legacy Sharpe variance estimate is undefined for these inputs") from exc
        if not math.isfinite(var_sr) or var_sr < 0:
            raise ValueError("Legacy Sharpe variance estimate must be finite and nonnegative")
        try:
            tail_probability = 1.0 / num_trials
        except OverflowError as exc:
            raise ValueError("num_trials exceeds the supported floating-point range") from exc
        # Q(1-p) = -Q(p) avoids rounding a small tail probability away to 1.
        e_max_sr = -(1 - _EULER_MASCHERONI) * _inverse_norm(tail_probability)
        e_max_sr -= _EULER_MASCHERONI * _inverse_norm(tail_probability / math.e)
        e_max_sr *= math.sqrt(var_sr / n)
    sr_deflated = sr_obs - e_max_sr
    result = Decimal(str(sr_deflated))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _inverse_norm(p: float) -> float:
    if not math.isfinite(p) or not 0 < p < 1:
        raise ValueError("Normal quantile probability must be finite and between 0 and 1")
    return NormalDist().inv_cdf(p)

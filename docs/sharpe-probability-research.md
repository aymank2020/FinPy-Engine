# Sharpe probability models: research and compatibility decisions

This note records the model implemented in phase B. The legacy
`deflated_sharpe_ratio` remains a Decimal **score in Sharpe units**. The new
`deflated_sharpe_probability_from_stats` is a separate probability API.

## Primary sources

[Bailey and López de Prado, 2014, author PDF](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf),
Eq. 2 on page 8, defines DSR as PSR evaluated at a search threshold. Its variance
input is variance **across trial Sharpe estimates**, and N counts independent
trials. Page 10 gives the numerical examples below. The expected maximum is an
approximation for multiple trials, under a zero-mean null; this implementation
does not estimate trial independence or variance from the winning returns.

[Bailey and López de Prado, 2012, author PDF](https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf),
Eq. 7 on page 7 defines standardized central moments; Eq. 11 on page 9 and
Appendix 3 on page 20 use native-frequency statistics and T-1. The appendix
accepts mean, standard deviation, skewness and raw kurtosis externally; it does
not prescribe a finite-sample SD estimator. All Sharpe quantities in the
probability formula have the original observation frequency.

[Python NormalDist](https://docs.python.org/3.12/library/statistics.html#statistics.NormalDist.inv_cdf)
provides the normal quantile. The implementation uses erfc for the normal CDF
so very small lower-tail probabilities are not lost in `1+erf(z)`.
The local Euler–Mascheroni value agrees with
[NIST DLMF 5.2.3](https://dlmf.nist.gov/5.2#E3).

## Formula and input contract

Write S for observed Sharpe, g3 for skewness, g4 for **raw**, not excess,
kurtosis, V for variance across trial Sharpe estimates, and T for observations:

```
A  = 1 - g3*S + (g4-1)*S*S/4
S0 = sqrt(V) * [(1-gamma)*Q(1-1/N) + gamma*Q(1-1/(N*e))]
P  = Phi((S-S0)*sqrt(T-1)/sqrt(A))
```

All supplied statistics are at the native observation frequency. V is mandatory
and nonnegative. T is an actual int at least 2; N is an actual int at least 1.
Floats, Decimal counts and booleans are rejected as counts. No annualization or
trial-variance inference is performed by the new API. N=1 uses S0=0: under a
zero-mean null the maximum of one draw has expected value zero. This boundary
is a documented inference, not an evaluation of the asymptotic formula at Q(0).
V=0 also gives S0=0. Tail symmetry Q(1-p)=-Q(p) avoids rounding 1-p to 1.

Coherent standardized moments obey g4 >= 1+g3². This follows from
E[(Z²-g3*Z-1)²] >= 0 when E[Z]=0 and E[Z²]=1. A is evaluated as
`(1-g3*S/2)² + (g4-1-g3²)*S²/4`, using hypot for its square root. A=0 is an
undefined sampling-variance model and raises ValueError; it is not clamped.

Rounded moments at Pearson equality can differ by a few representable values:
a sweep of two-point empirical samples with T=3..100 found deficits up to four
ULPs of `1+g3²`. Only a deficit no greater than four ULPs is treated as equality.
Larger violations are rejected. This explicit roundoff allowance does not
relax the A>0 requirement or repair genuinely inconsistent moments.

Finite int, float and Decimal statistics are converted to binary floats.
Nonfinite values, booleans, strings, overflow and nonzero values that underflow
to zero are rejected. Counts outside the floating-point range are rejected.
Returned Decimal wraps a binary-float probability, not arbitrary-precision
statistical arithmetic. Extreme tails can round to 0 or 1. The count remains
an integer even above 2**53; continuous normal calculations use floating-point
approximations. No epsilon accepts fractional counts or hides model errors.

The standardized difference is subtracted before division when that difference
is finite, preserving cancellation of close same-sign inputs. With finite
opposing inputs whose difference overflows, each is divided by the standard
error first. For returns [-1,0,1], risk-free 1e308 and target 1e308, the true
z is -8 and probability is approximately 6.220960574271784e-16; direct
subtraction would incorrectly turn it into zero. A regression covers both
signs, same-sign cancellation and large coherent DSR inputs.

## PSR estimator and compatibility correction

`probabilistic_sharpe` retains its signature and Decimal probability result.
Its observed S uses Bessel sample SD, preserving the existing point-estimate
convention and ordinary Sharpe. This is an explicit compatibility choice, not
an author requirement. Skewness and raw kurtosis use the empirical population
standardization: Z=(r-mean)/sqrt(mean((r-mean)²)). This avoids the old mixture of
sample SD and population central moments. These are consistent plug-in
estimators, not unbiased finite-sample skew/kurtosis estimators.

For empirical PSR, the identity
`A = mean((Z - S*(Z²-1)/2)²)` evaluates the same population-moment formula as
nonnegative squares. It does not replace negative variance with zero.
Scaling the returns before centering avoids unnecessary overflow/underflow;
positive rescaling of returns and risk-free rate leaves the probability unchanged.

`risk_free_rate` remains per observation. Without periods_per_year,
target_sharpe is also per observation. With that parameter, target_sharpe is
annualized and is divided by sqrt(periods_per_year). S, moments and T remain in
native units. Thus a zero target gives the same probability with and without
an annual display frequency; the old implementation changed it by annualizing
S alone inside its variance estimate. T-1 replaces the old T denominator.

Constant returns now raise ValueError because SD and standardized moments are
undefined. The old PSR silently used the ordinary-Sharpe zero sentinel and
returned .5 at target zero. This is an intentional correction to the probability
contract, documented here and in tests. Ordinary Sharpe and the legacy deflated
score keep their existing constant-return behavior. No existing CLI command
uses either probability API; risk CLI continues to use ordinary Sharpe.

## Reference acceptance

For the author 2014 example use S=2.5/sqrt(250), T=1250, V=.5/250:

| N | g3 | g4 | probability with full Euler constant | Published rounding |
| --- | --- | --- | --- | --- |
| 100 | -3 | 10 | .9003968344493904 | .9004 |
| 46 | -3 | 10 | .9505017068755786 | .9505 |
| 88 | 0 | 3 | .9504908166760138 | .9505 |
| 1 | -3 | 10 | .9999968595078976 | boundary PSR0 |

The paper's shorter constant 0.5772156649 produces probabilities differing
by about 1e-13. Tests allow 1e-12 against the independent full-constant values
and 5e-5 against published four-digit examples. No financial tolerance was
widened to fix an implementation failure.

Independent 60-digit central-moment calculations for
`[.01,.02,-.01,.015,.005,-.02,.03,.01]` give S=.46770717334674267,
g3=-.4583333333333333 and g4=2.3449074074074074. PSR at target zero is
.8622279371626578; target .1 gives .8043466098857269; target .5 gives
.4699937740537978. The old probability .8845787007702588 used different moment
normalization and T instead of T-1. With risk_free_rate=.005 the corrected
probability is .6543076184595922.

Acceptance includes these constants; N=1 equals PSR0; increasing N or V cannot
increase DSR for fixed data; annual target conversion and positive return-unit
rescaling preserve PSR; coherent symmetric near-constant samples no longer
produce a negative moment variance; invalid counts/moments/nonfinite inputs
fail explicitly. Tests exercise module and package exports from an installed
wheel, and ci_smoke checks the author DSR example and corrected PSR before the
existing six CLI commands. The legacy score regression suite remains active.

These models assume supplied moments and the independent-trial count are
appropriate for the data. This change supplies no serial-dependence correction,
effective-trial estimator, investment decision, or certification of model fit.

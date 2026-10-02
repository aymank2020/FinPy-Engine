# Numerical conventions and compatibility

Inputs are fractional rates, positive elapsed years, and `Decimal` amounts.
`ndigits` rounds the returned value; schedules calculate unrounded balances
before rounding displayed rows. Rounded rows can have a small reconciliation
difference. These are constant-rate mathematical models without fees, taxes,
penalties, business calendars, or changing rates unless explicitly supplied.

## Discounting and rate conversion

For nominal annual rate `r`, frequency `m` and years `t`, the accumulation
factor is `(1+r/m) ** (m*t)`. Continuous accumulation is `exp(r*t)`.
Discounting takes the reciprocal; an implied spot rate inverts this same
formula. Positive discount factors above one imply negative yields and are
valid. A periodic accumulation base at or below zero is rejected.

`money-market` uses simple accumulation `1+r*t` with time in years.
`bond-basis` accepts time in days and uses `1+r*days/365`. This historical mode
name does **not** implement a 30/360 calendar convention; accrued-interest
functions supply separate day-count APIs. Quarterly, monthly, weekly and
daily compounding use 4, 12, 52 and 365 periods per year.

`continuous_equiv(nominal, m)` returns `m*ln(1+nominal/m)`.
`discrete_equiv(continuous, m)` now returns its inverse,
`m*(exp(continuous/m)-1)`. This corrects the old inconsistent calculation;
callers needing effective annual yield should use `effective_annual_rate`.
The names `apr_from_apy` and `apy_from_apr` describe nominal/effective rate
conversion here. They do not calculate a disclosed consumer APR including
loan fees. Mathematically valid negative rates remain supported.

Macaulay duration takes `(amount, years)` cashflows and nominal annual yield.
Modified duration divides it by `1+yield/m`. Both accept `periods_per_year`,
defaulting to 1; a lone duration number without a yield is not this API.

## Loans and savings

Loan payments are positive amounts paid by the borrower. An extra principal
payment shortens the term while retaining the regular payment; recasting
reduces the payment while retaining the remaining term. Interest savings
compare actual balance-based interest, including the smaller final payment.
`apply_lump_sum` accepts a whole payment count as int, integral float, or
integral Decimal, including the `period` returned by `amortization_schedule`.
Fractional, negative and nonfinite payment counts raise `ValueError` instead of
being truncated or failing later during interest iteration.
`extra_payment_schedule` retains its list of payment rows. The new
`extra_payment_summary` supplies payment, term, interest and savings totals.
`amortization_summary` retains `total_payments` / `n_periods` and adds the
consumer aliases `total_paid` / `num_payments` plus `first_year_interest`.

Terms retain the existing whole-period truncation for fractional periods.
Values within `1e-12` of a whole period are restored to that integer to avoid
losing a payment after dividing an integer term by the frequency. Nonpositive
terms and payment frequencies are rejected. Zero-rate loans still owe their
unpaid principal before maturity; a zero-rate balloon is not automatically 0.

Refinance IRR uses costs at time 0 and savings at period ends. It returns a
nominal annual rate (`periodic IRR * payments_per_year`). The solver expands
its bracket and verifies convergence instead of returning 0 for an out-of-
bracket root. Positive savings with zero initial cost have no finite IRR and
raise `ValueError`. The existing sentinel 0 for nonpositive savings remains.
A lower rate can still have negative IRR after closing costs. One/five-year
savings in `rate_comparison` are undiscounted savings minus upfront costs;
negative savings are reported, not hidden by a clamp.

## Returns and backtests

`returns.log_returns.annualized_return` preserves sequence annualization with
observations per year and adds scalar total-return annualization over years.
Do not compound log returns with `total_return`, which accepts simple returns.
Standard deviation uses Decimal square root so tiny decimal variance is not
lost in conversion to a binary float. `semivariance` is a lower partial moment
averaged over all observations; one observation is valid. A gains/losses ratio
with gains and no losses remains positive infinity.

`var_backtest` retains its diagnostic dict: breaches, observation count,
breach rate and expected count. A breach requires actual loss strictly above
the estimate. `cvar_backtest` retains tail-breach count and average excess.
Neither is a regulatory model validation or an ES statistical test. Existing
historical VaR/CVaR absolute-tail conventions are unchanged in this patch.

## Research and regression evidence

The financial equations were checked against primary implementations and
definitions: [QuantLib interest rates](https://github.com/lballabio/QuantLib/blob/master/ql/interestrate.cpp),
[QuantLib duration](https://github.com/lballabio/QuantLib/blob/master/ql/cashflows/cashflows.cpp),
[NumPy Financial payment equation](https://github.com/numpy/numpy-financial/blob/main/numpy_financial/_financial.py),
[TreasuryDirect bill pricing](https://www.treasurydirect.gov/marketable-securities/understanding-pricing/),
[CFPB principal prepayments](https://www.consumerfinance.gov/ask-cfpb/whats-the-difference-between-a-simple-interest-rate-and-precomputed-interest-on-an-auto-loan-en-841/),
and [BIS VaR exceptions](https://www.bis.org/committees/bcbs/basel-framework/standard/mar/32/inforce/2023-01-01/published/2020-03-27).
These references support the equations and assumptions; they do not certify
this library. Regression checks cover inverse rates, price sensitivity,
principal/payment conservation, summaries and IRR NPV residuals.

Several pre-existing assertions were corrected with explicit numerical
evidence rather than changing working APIs: annual coupon 50 accrued over
150/360 of a year is 20.83 (not 41.67); duration needs a yield; negative yield
is valid; scalar comparisons are invalid for a backtest dict; and loan
savings must account for closing costs. Summary tests now call the new summary
function while separate regressions exercise the original schedule list.

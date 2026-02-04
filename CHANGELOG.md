# Changelog

All notable changes to FinPy-Engine are documented in this file.

The format follows Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.4.2] - 2024-12-01

### Added
- Core module with Cashflow, Instrument, YieldCurve, ReturnSeries, FXRate, ScheduleRow, Result dataclasses.
- TVM subpackage: present_value, future_value, NPV, IRR, MIRR, payback periods.
- Bonds subpackage: clean/dirty pricing, YTM, Macaulay/modified duration, convexity.
- Loans subpackage: amortization schedule, refinance breakeven, prepayment.
- Risk subpackage: historical/parametric VaR, CVaR, Sharpe, Sortino, max drawdown, beta.
- FX subpackage: ISO 4217 validation, spot conversion, historical lookup.
- Returns subpackage: simple/log returns, cumulative return, annualized volatility, rolling stats, autocorrelation.
- Schemas for JSON serialization of Cashflow, Instrument, Result.
- Migrations for schema versioning (0001, 0002, 0003).
- CLI with npv, irr, bond-price, bond-yield, duration, amortize, var, sharpe, drawdown, fx-convert commands.
- Dockerfile, CI workflow, Makefile, preflight checks.

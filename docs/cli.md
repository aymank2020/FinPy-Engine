# CLI Reference

After installation, use `finpy <command> [options]`, or run
`python -m finpy <command> [options]` from a checkout with `src` on PYTHONPATH.

| Command | Required arguments | Result |
| --- | --- | --- |
| `pv` | `--amount --rate --periods` | Present value |
| `fv` | `--pv --rate --periods` | Future value; optional `--mode` |
| `bond` | `--face --coupon --ytm --maturity` | Bond price, duration, convexity; optional `--freq` |
| `loan` | `--principal --rate --years` | Amortization schedule; optional `--freq` |
| `risk` | `--returns <values...>` | Sharpe, Sortino, maximum drawdown, historical VaR |
| `fx` | `--amount --from --to --rate` | Spot currency conversion |

Rates are decimal fractions. Monetary values and rates are parsed directly as
Decimal; NaN and infinity are rejected. The CLI prints the calculation result
to stdout, errors to stderr, and returns 0 on success, 1 for a calculation
error, or 2 for malformed command arguments.

```bash
finpy pv --amount 100 --rate 0.05 --periods 1
finpy fx --amount 100 --from USD --to EUR --rate 0.9
finpy risk --returns 0.02 -0.01 0.03
```

Run `finpy --help` and `finpy <command> --help` for current argument details.

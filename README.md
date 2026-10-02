# FinPy-Engine

Python financial-calculations library and CLI using Decimal monetary inputs.

## Install and run

```bash
python -m pip install -e ".[dev]"
finpy pv --amount 100 --rate 0.05 --periods 1
python -m finpy fv --pv 100 --rate 0.05 --periods 2
```

Rates are fractional values: `0.05` means 5 percent. See [the CLI guide](docs/cli.md)
for all six commands. Invalid arguments return status 2; calculation errors
return status 1 and a message on stderr.

## Library usage

```python
from decimal import Decimal
from finpy.core.discount import present_value

flows = [(Decimal("100.00"), 1), (Decimal("200.00"), 2)]
print(present_value(flows, Decimal("0.05")))
```

The existing single-flow call `present_value(amount, time, rate)` is supported.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m pip wheel . --no-deps
```

See [numerical conventions](docs/numerical-conventions.md) for rate, cashflow,
schedule and backtest contracts, including compatibility decisions and primary
sources used in the numerical review.

CI builds and installs a regular wheel with the declared `dev` extra on Python
3.11 and 3.12. It compiles source, scripts and tests, verifies the installed wheel
and all six CLI commands, runs the 50 numerical regression cases explicitly,
then runs the full suite with the existing 95 percent coverage requirement.
Warnings and test failures remain visible. A separate Docker job tests the same
wheel installation and full suite in the container.

`scripts/preflight.py` belongs to the historical repository-generation workflow;
its local `dir()` discovery currently invokes none of its 18 advertised checks.
CI uses the explicit checks above instead of treating that message as validation.

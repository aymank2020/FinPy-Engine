"""Verify the installed wheel and both application entry points in CI."""

from decimal import Decimal
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
from urllib.parse import urlsplit

import finpy


def run(command: list[str], expected_status: int = 0) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    print(f"{command!r}: exit {result.returncode}", flush=True)
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    if result.returncode != expected_status:
        raise RuntimeError(f"Expected exit {expected_status}, received {result.returncode}")
    return result


def main() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src"
    module = Path(finpy.__file__).resolve()
    if source_root in module.parents:
        raise RuntimeError(f"Imported checkout source instead of installed wheel: {module}")
    installed = distribution("finpy")
    provenance = json.loads(installed.read_text("direct_url.json") or "{}")
    if "archive_info" not in provenance or not urlsplit(provenance.get("url", "")).path.endswith(".whl"):
        raise RuntimeError(f"FinPy must be installed from the built wheel: {provenance}")
    print(f"Installed finpy {installed.version}: {module}; wheel: {provenance['url']}", flush=True)
    from finpy.risk.sharpe import deflated_sharpe_ratio

    returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
    for trials, expected in [(1, Decimal("0.4677")), (10, Decimal("-0.1469"))]:
        score = deflated_sharpe_ratio(returns, num_trials=trials, ndigits=4)
        if not isinstance(score, Decimal) or not score.is_finite() or score != expected:
            raise RuntimeError(f"Installed public legacy Sharpe score failed: {score}")
    print("PASS: installed public Sharpe module returns finite legacy scores", flush=True)
    console = Path(sysconfig.get_path("scripts")) / ("finpy.exe" if os.name == "nt" else "finpy")

    version = run([str(console), "--version"])
    if version.stdout.strip() != f"finpy {installed.version}":
        raise RuntimeError("Installed console entry point has an inconsistent version")
    pv = run([str(console), "pv", "--amount", "9007199254740993.01", "--rate", "0", "--periods", "1"])
    if Decimal(pv.stdout.strip()) != Decimal("9007199254740993.01"):
        raise RuntimeError("CLI lost Decimal monetary input precision")
    fv = run([str(console), "fv", "--pv", "100", "--rate", "0.05", "--periods", "2"])
    if Decimal(fv.stdout.strip()) != Decimal("110.25"):
        raise RuntimeError("Unexpected future-value CLI result")
    bond = run([str(console), "bond", "--face", "1000", "--coupon", "0.05", "--ytm", "0.04", "--maturity", "5"])
    if "clean_price" not in bond.stdout or "modified_duration" not in bond.stdout:
        raise RuntimeError("Bond CLI did not dispatch to its calculation")
    loan = run([str(console), "loan", "--principal", "1000", "--rate", "0.05", "--years", "1"])
    if not loan.stdout.startswith("[") or "balance" not in loan.stdout:
        raise RuntimeError("Loan CLI did not return its schedule")
    risk = run([str(console), "risk", "--returns", "0.02", "-0.01", "0.03"])
    if "var_95" not in risk.stdout or "max_drawdown" not in risk.stdout:
        raise RuntimeError("Risk CLI did not return its metrics")
    fx = run([str(console), "fx", "--amount", "100", "--from", "USD", "--to", "EUR", "--rate", "0.9"])
    if Decimal(fx.stdout.strip()) != Decimal("90"):
        raise RuntimeError("Unexpected FX CLI result")
    module_pv = run([sys.executable, "-m", "finpy", "pv", "--amount", "100", "--rate", "0", "--periods", "1"])
    if Decimal(module_pv.stdout.strip()) != Decimal("100"):
        raise RuntimeError("Module entry point did not run the calculation")
    invalid = run([str(console), "pv", "--amount=nan", "--rate", "0", "--periods", "1"], 2)
    if "finite decimal" not in invalid.stderr:
        raise RuntimeError("Argument failure did not explain the invalid input")
    failure = run([str(console), "pv", "--amount", "100", "--rate", "-1", "--periods", "1"], 1)
    if "Error:" not in failure.stderr or "Traceback" in failure.stderr:
        raise RuntimeError("Calculation failure did not preserve the CLI error contract")
    print("PASS: installed wheel, six CLI commands, module entry point and failure statuses", flush=True)


if __name__ == "__main__":
    main()

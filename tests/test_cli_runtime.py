"""Exercise command dispatch and process status without replacing calculations."""
import subprocess
import sys
from decimal import Decimal

import pytest

from finpy.cli.main import main
from finpy.core.discount import present_value


def test_pv_cli_keeps_decimal_input_precision(capsys):
    assert main(["pv", "--amount", "9007199254740993.01", "--rate", "0", "--periods", "1"]) == 0
    assert Decimal(capsys.readouterr().out.strip()) == Decimal("9007199254740993.01")


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nonfinite_amount_rejected(value, capsys):
    assert main(["pv", "--amount=" + value, "--rate", "0", "--periods", "1"]) == 2
    assert "finite decimal" in capsys.readouterr().err


def test_calculation_failure_returns_status_without_traceback(capsys):
    assert main(["pv", "--amount", "100", "--rate", "-1", "--periods", "1"]) == 1
    assert "Error:" in capsys.readouterr().err


def test_module_command_runs_the_registered_application():
    result = subprocess.run([sys.executable, "-m", "finpy", "pv", "--amount", "100", "--rate", "0", "--periods", "1"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert Decimal(result.stdout.strip()) == Decimal(100)


def test_single_flow_compatibility():
    assert present_value(100, 1, Decimal("0.05")) == present_value([(100, 1)], Decimal("0.05"))

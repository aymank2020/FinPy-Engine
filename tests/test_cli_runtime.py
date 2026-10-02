"""Exercise command dispatch and process status without replacing calculations."""
import subprocess
import sys
import re
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


@pytest.mark.parametrize("arguments, expected", [
    (["fv", "--pv", "100", "--rate", "0.05", "--periods", "2"], Decimal("110.25")),
    (["fx", "--amount", "100", "--from", "USD", "--to", "EUR", "--rate", "0.9"], Decimal("90")),
])
def test_registered_scalar_commands_calculate(arguments, expected, capsys):
    assert main(arguments) == 0
    assert Decimal(capsys.readouterr().out.strip()) == expected


def _decimal_fields(output):
    return {key: Decimal(value) for key, value in re.findall(r"'([a-z_][a-z0-9_]*?)': Decimal\('([^']+)'\)", output)}


def test_registered_bond_command_prices_zero_coupon_cashflow(capsys):
    assert main(["bond", "--face", "1000", "--coupon", "0", "--ytm", "0.05", "--maturity", "2", "--freq", "1"]) == 0
    fields = _decimal_fields(capsys.readouterr().out)
    assert fields["clean_price"] == pytest.approx(Decimal(1000) / Decimal("1.05") ** 2, abs=Decimal("1e-20"))
    assert fields["dirty_price"] == fields["clean_price"]
    assert fields["macaulay_duration"] == Decimal(2)
    assert fields["modified_duration"] == pytest.approx(Decimal(2) / Decimal("1.05"), abs=Decimal("1e-20"))


def test_registered_loan_command_returns_cash_conserving_schedule(capsys):
    assert main(["loan", "--principal", "1000", "--rate", "0.05", "--years", "1"]) == 0
    rows = [_decimal_fields(row) for row in re.findall(r"\{([^}]+)\}", capsys.readouterr().out)]
    assert len(rows) == 12
    assert rows[-1]["balance"] == 0
    assert sum(row["principal"] for row in rows) == pytest.approx(Decimal(1000), abs=Decimal("1e-20"))
    assert all(row["payment"] == row["principal"] + row["interest"] for row in rows)


def test_registered_risk_command_returns_loss_and_drawdown(capsys):
    assert main(["risk", "--returns", "0.02", "-0.01", "0.03"]) == 0
    fields = _decimal_fields(capsys.readouterr().out)
    assert fields["var_95"] == Decimal("0.01")
    assert fields["max_drawdown"] == pytest.approx(Decimal("0.01"), abs=Decimal("1e-15"))


@pytest.mark.parametrize("value", ["nan", "inf", "invalid"])
def test_registered_risk_command_rejects_invalid_returns(value, capsys):
    assert main(["risk", "--returns=" + value]) == 2
    assert "expected a" in capsys.readouterr().err

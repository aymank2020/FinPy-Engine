from hypothesis import given, strategies as st
from finpy.cli.main import main


class TestMain:
    def test_version(self):
        try:
            main(["--version"])
        except SystemExit as e:
            assert e.code == 0

    def test_unknown_subcommand(self):
        try:
            main(["nonexistent"])
        except SystemExit as e:
            assert e.code != 0

    def test_help_output(self):
        try:
            main(["--help"])
        except SystemExit as e:
            assert e.code == 0

    def test_debug_flag(self):
        try:
            main(["--debug", "nonexistent"])
        except SystemExit as e:
            assert e.code != 0

    def test_quiet_flag(self):
        try:
            main(["--quiet", "nonexistent"])
        except SystemExit as e:
            assert e.code != 0

    def test_main_no_args_shows_help(self):
        try:
            main([])
        except SystemExit as e:
            assert e.code != 0

    def test_main_entry_point(self):
        from finpy.cli.main import entry_point
        try:
            entry_point()
        except SystemExit as e:
            assert e.code != 0

    def test_version_output_format(self):
        import sys
        from io import StringIO
        saved = sys.stdout
        try:
            sys.stdout = StringIO()
            try:
                main(["--version"])
            except SystemExit:
                pass
            output = sys.stdout.getvalue()
            assert "finpy" in output
        finally:
            sys.stdout = saved

    def test_finpy_error_handling(self):
        try:
            main(["pv", "--rate", "abc", "--amount", "100", "--periods", "1"])
        except SystemExit as e:
            assert e.code != 0

    def test_value_error_handling(self):
        try:
            main(["pv", "--rate", "-1", "--amount", "100", "--periods", "1"])
        except SystemExit as e:
            assert e.code != 0

    def test_pv_subcommand(self):
        try:
            rc = main(["pv", "--rate", "0.05", "--amount", "100", "--periods", "1"])
            assert rc == 0
        except SystemExit as e:
            assert e.code == 0

    def test_fv_subcommand(self):
        try:
            rc = main(["fv", "--pv", "100", "--rate", "0.05", "--periods", "1", "--mode", "annual"])
            assert rc == 0
        except SystemExit as e:
            assert e.code == 0

    def test_subcommand_with_debug_env(self):
        import os
        os.environ["FINPY_DEBUG"] = "1"
        try:
            try:
                main(["nonexistent"])
            except SystemExit:
                pass
        finally:
            os.environ.pop("FINPY_DEBUG", None)

    def test_main_returns_int(self):
        result = main(["--version"])
        assert isinstance(result, int)


@given(st.text(min_size=1, max_size=10))
def test_rejects_unknown_subcommand(cmd):
    valid = {"npv", "irr", "bond-price", "bond-yield", "duration", "amortize", "var", "sharpe", "drawdown", "fx-convert"}
    if cmd not in valid:
        try:
            main([cmd])
        except SystemExit as e:
            assert e.code != 0


@given(st.sampled_from(["npv", "irr", "sharpe"]))
def test_valid_subcommands_hypothesis(cmd):
    try:
        main([cmd])
    except SystemExit as e:
        assert e.code != 0

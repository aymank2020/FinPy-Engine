import os, sys, argparse
from finpy import __version__
from finpy.cli.commands import register_subparsers
from finpy.core.errors import FinPyError

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="finpy", description="FinPy-Engine financial calculations")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_subparsers(subparsers)
    try:
        args = parser.parse_args(argv)
        if hasattr(args, "func"):
            result = args.func(args)
            if result is not None:
                print(result)
            return 0
        parser.print_help()
        return 2
    except FinPyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SystemExit as e:
        return e.code

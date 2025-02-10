from decimal import Decimal
from typing import Optional


def format_decimal(value: Decimal, ndigits: int = 4) -> str:
    return f"{value:.{ndigits}f}"


def format_percent(value: Decimal, ndigits: int = 2) -> str:
    return f"{value * 100:.{ndigits}f}%"


def format_currency(value: Decimal, symbol: str = "$", ndigits: int = 2) -> str:
    return f"{symbol}{value:.{ndigits}f}"


def format_with_commas(value: Decimal, ndigits: int = 2) -> str:
    formatted = f"{value:.{ndigits}f}"
    parts = formatted.split(".")
    int_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else ""
    reversed_int = int_part[::-1]
    grouped = ",".join(reversed_int[i:i + 3] for i in range(0, len(reversed_int), 3))
    int_part_commas = grouped[::-1]
    if decimal_part:
        return f"{int_part_commas}.{decimal_part}"
    return int_part_commas


def format_table(headers: list[str], rows: list[list[str]], padding: int = 2) -> str:
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))
    pad = " " * padding
    header_line = pad.join(h.ljust(w) for h, w in zip(headers, col_widths))
    separator = pad.join("-" * w for w in col_widths)
    lines = [header_line, separator]
    for row in rows:
        line = pad.join(cell.ljust(w) for cell, w in zip(row, col_widths))
        lines.append(line)
    return "\n".join(lines)


def format_bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def format_green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


def format_red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def format_yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def format_header(text: str, width: int = 60) -> str:
    line = "=" * width
    return f"{line}\n{text.center(width)}\n{line}"

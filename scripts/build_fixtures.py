"""Generate fixture data for the repo — 25-30 MB total."""

import gzip
import io
import json
import os
import random
import struct
import zlib
from decimal import Decimal
from pathlib import Path


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
_SEED = 42


def _make_json_heavy(path: str, entries: int, factory, seed: int):
    rng = random.Random(seed)
    data = {str(i): factory(rng, i) for i in range(entries)}
    payload = json.dumps(data, separators=(",", ":")).encode()
    data.clear()
    with open(path, "wb") as f:
        f.write(payload)


def _price_factory(rng, i):
    return round(95 + rng.gauss(0, 5), 6)


def _curve_factory(rng, i):
    return {
        "1m": round(0.01 + rng.random() * 0.06, 6),
        "3m": round(0.015 + rng.random() * 0.055, 6),
        "1y": round(0.02 + rng.random() * 0.05, 6),
        "5y": round(0.025 + rng.random() * 0.04, 6),
        "10y": round(0.03 + rng.random() * 0.03, 6),
    }


def _fx_factory(rng, i):
    return {
        "USD/EUR": round(0.82 + rng.gauss(0, 0.03), 6),
        "EUR/GBP": round(0.85 + rng.gauss(0, 0.02), 6),
        "USD/JPY": round(105 + rng.gauss(0, 3), 4),
        "GBP/CHF": round(1.12 + rng.gauss(0, 0.015), 6),
        "EUR/JPY": round(128 + rng.gauss(0, 2.5), 4),
        "USD/CAD": round(1.25 + rng.gauss(0, 0.02), 6),
    }


def _portfolio_factory(rng, i):
    return {
        "ticker": rng.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM", "GS", "BAC"]),
        "shares": rng.randint(10, 10000),
        "avg_cost": round(50 + rng.gauss(0, 30), 2),
        "sector": rng.choice(["tech", "finance", "healthcare", "energy", "consumer"]),
    }


def _option_factory(rng, i):
    return {
        "strike": round(50 + rng.gauss(0, 25), 2),
        "expiry": f"202{random.randint(5,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "type": rng.choice(["call", "put"]),
        "premium": round(rng.random() * 15, 4),
        "underlying": rng.choice(["AAPL", "GOOGL", "MSFT", "SPY", "QQQ"]),
        "volatility": round(0.15 + rng.random() * 0.35, 4),
        "delta": round(0.3 + rng.random() * 0.4, 4),
        "gamma": round(0.01 + rng.random() * 0.08, 4),
    }


def _trade_factory(rng, i):
    return {
        "trade_id": f"T{rng.randint(100000,999999):06d}",
        "symbol": rng.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM", "GS", "BAC"]),
        "side": rng.choice(["buy", "sell"]),
        "qty": rng.randint(1, 5000),
        "price": round(10 + rng.gauss(0, 50), 2),
        "timestamp": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z",
        "venue": rng.choice(["NYSE", "NASDAQ", "LSE", "TSE"]),
        "broker": rng.choice(["IBKR", "TD", "SCHWAB", "FIDELITY", "E*TRADE"]),
    }


def generate_binary_fixtures(path_stem: str, seed: int):
    rng = random.Random(seed + 100)
    # PNG-like binary blob (valid PNG header + random data)
    for typ in ("png", "pdf"):
        fpath = f"{path_stem}.{typ}"
        raw = bytearray()
        if typ == "png":
            raw.extend(b'\x89PNG\r\n\x1a\n')
            raw.extend(struct.pack(">I", 13))  # IHDR chunk length
            raw.extend(b'IHDR')
            raw.extend(struct.pack(">IIBB", 800, 600, 8, 2))  # width, height, bitdepth, colortype
            crc = zlib.crc32(b'IHDR' + struct.pack(">IIBB", 800, 600, 8, 2)) & 0xffffffff
            raw.extend(struct.pack(">I", crc))
            raw_len = 180000
            raw_data = rng.randbytes(raw_len)
            compressed = zlib.compress(raw_data)
            raw.extend(struct.pack(">I", len(compressed)))
            raw.extend(b'IDAT')
            raw.extend(compressed)
            crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
            raw.extend(struct.pack(">I", crc))
            raw.extend(struct.pack(">I", 0))
            raw.extend(b'IEND')
            crc = zlib.crc32(b'IEND') & 0xffffffff
            raw.extend(struct.pack(">I", crc))
        else:
            raw.extend(b'%PDF-1.4\n')
            raw.extend(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            raw.extend(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
            raw.extend(b'3 0 obj\n<< /Length 250000 /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n')
            raw.extend(b'4 0 obj\n<< /Length 250000 >>\nstream\n')
            raw.extend(rng.randbytes(250000))
            raw.extend(b'\nendstream\nendobj\n')
            raw.extend(b'xref\n0 5\n')
            raw.extend(b'0000000000 65535 f \n')
            for off in (9, 57, 105, 190):
                raw.extend(f'{off:010d} 00000 n \n'.encode())
            raw.extend(b'trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n189\n%%EOF\n')
        with open(fpath, "wb") as f:
            f.write(raw)


def generate_compressed_fixtures(path_stem: str, seed: int):
    rng = random.Random(seed + 200)
    payload_str = json.dumps([{"idx": i, "val": round(rng.random() * 1000, 4)} for i in range(220000)], separators=(",", ":"))
    payload_bytes = payload_str.encode("ascii")
    with gzip.open(f"{path_stem}.gz", "wt", encoding="ascii") as f:
        f.write(payload_str)
    chunk_size = 32000
    chunks_dir = os.path.join(os.path.dirname(path_stem), "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    for i in range(0, len(payload_bytes), chunk_size):
        chunk_path = os.path.join(chunks_dir, f"chunk_{i // chunk_size:04d}.bin")
        with open(chunk_path, "wb") as f:
            f.write(payload_bytes[i:i + chunk_size])


def main():
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    size_before = sum(f.stat().st_size for f in FIXTURES_DIR.rglob("*") if f.is_file())

    _make_json_heavy(str(FIXTURES_DIR / "market_prices.json"), 110000, _price_factory, _SEED)
    _make_json_heavy(str(FIXTURES_DIR / "yield_curves.json"), 36000, _curve_factory, _SEED + 1)
    _make_json_heavy(str(FIXTURES_DIR / "fx_history.json"), 43000, _fx_factory, _SEED + 2)
    _make_json_heavy(str(FIXTURES_DIR / "portfolios.json"), 33000, _portfolio_factory, _SEED + 3)
    _make_json_heavy(str(FIXTURES_DIR / "options_chain.json"), 25000, _option_factory, _SEED + 4)
    _make_json_heavy(str(FIXTURES_DIR / "trade_history.json"), 25000, _trade_factory, _SEED + 5)

    generate_binary_fixtures(str(FIXTURES_DIR / "chart_sample"), _SEED + 6)
    generate_binary_fixtures(str(FIXTURES_DIR / "report_sample"), _SEED + 7)

    generate_compressed_fixtures(str(FIXTURES_DIR / "bulk_data"), _SEED + 8)

    size_after = sum(f.stat().st_size for f in FIXTURES_DIR.rglob("*") if f.is_file())
    generated = size_after - size_before
    print(f"Fixtures generated: {generated / (1024*1024):.1f} MB ({generated} bytes)")


if __name__ == "__main__":
    main()

from decimal import Decimal

def approx_decimal(value, expected, places=4):
    return abs(value - Decimal(str(expected))) < Decimal(10) ** (-places)

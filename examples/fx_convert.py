from finpy.fx import convert_spot, is_valid_currency

result = convert_spot(1000, "USD", "EUR", 0.85)
print(f"1000 USD = {result} EUR")
print(f"Is XYZ valid? {is_valid_currency('XYZ')}")

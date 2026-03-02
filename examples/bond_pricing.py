from finpy.bonds import clean_price, dirty_price, ytm, modified_duration, convexity

cp = clean_price(1000, 0.05, 0.04, 10)
dp = dirty_price(1000, 0.05, 0.04, 10, days_since_last_coupon=60)
y = ytm(1000, 0.05, 950, 10)
d = modified_duration(1000, 0.05, 0.04, 10)
c = convexity(1000, 0.05, 0.04, 10)
print(f"Clean: {cp}, Dirty: {dp}, YTM: {y}, Duration: {d}, Convexity: {c}")

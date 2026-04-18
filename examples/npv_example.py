from finpy.tvm import npv, irr

cfs = [-1000, 300, 400, 500, 200]
n = npv(0.1, cfs)
r = irr(cfs)
print(f"NPV at 10%: {n}")
print(f"IRR: {r}")

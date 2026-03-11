from finpy.risk import historical_var, sharpe_ratio, max_drawdown, beta

rets = [0.01, -0.02, 0.03, -0.01, 0.02, 0.005, -0.015, 0.025, -0.005, 0.015]
v = historical_var(rets)
s = sharpe_ratio(rets)
m = max_drawdown(rets)
print(f"VaR: {v}, Sharpe: {s}, Max DD: {m}")

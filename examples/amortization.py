from finpy.loans import amortization_schedule

schedule = amortization_schedule(250000, 0.06, 30)
print(f"First payment: {schedule[0]}")
print(f"Last payment: {schedule[-1]}")

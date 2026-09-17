"""Pure-statistics adaptive-variance martingale oracle."""
import numpy as np
mu = 3.0
rng = np.random.default_rng(20260905)
means = []
for _ in range(20000):
    previous = mu
    samples = []
    for _k in range(8):
        sigma = 2.0 if previous > mu else 0.3
        x = mu + sigma * rng.normal()
        samples.append(x)
        previous = np.mean(samples)
    means.append(np.mean(samples))
means = np.asarray(means)
se = means.std(ddof=1) / np.sqrt(len(means))
z = (means.mean() - mu) / se
print(f"trials={len(means)} mean={means.mean():.8f} expected={mu:.8f} SE={se:.8f} z={z:.6f}")
print("PASS" if abs(z) <= 3.0 else "FAIL")

"""
bench.py — Phase 2 starter: serving-layer latency baseline.

Measures end-to-end latency of GET /predict in-process (no network noise):
p50 / p95 / p99 over N requests. This is the "before" number that Phase 2
inference work gets measured against.

Run:  python bench.py
"""
import time
import statistics

from fastapi.testclient import TestClient

import main

N_WARMUP = 50
N = 2000

client = TestClient(main.app)

# Warm up (imports, first-call overhead) so we measure steady state.
for _ in range(N_WARMUP):
    client.get("/predict")

lat_ms = []
for _ in range(N):
    t0 = time.perf_counter()
    r = client.get("/predict")
    lat_ms.append((time.perf_counter() - t0) * 1000)
    assert r.status_code == 200

lat_ms.sort()
q = lambda p: lat_ms[int(p * N) - 1]
print(f"requests: {N} (after {N_WARMUP} warmup)")
print(f"p50 latency: {statistics.median(lat_ms):8.3f} ms")
print(f"p95 latency: {q(0.95):8.3f} ms")
print(f"p99 latency: {q(0.99):8.3f} ms")
print(f"max latency: {lat_ms[-1]:8.3f} ms")
print("\nBaseline = stub model + framework overhead. Phase 2's job: swap in")
print("the real model and keep p95 within budget; profile what moves.")

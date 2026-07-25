# Kalshi BTC Settlement Pipeline — Phase 1: Serving

A containerized FastAPI service that authenticates against the Kalshi demo
API with RSA-PSS request signing and exposes a stable prediction endpoint.
Phase 1 of a four-phase ML systems build (Serving → Inference → Data → MLOps)
around a quantitative strategy for Kalshi's 15-minute BTC price markets.

## The strategy behind it (validation summary)

- Backtested across **5,000 markets** with full fee modeling
- **Calibration analysis** of predicted vs. realized probabilities at
  2 minutes to settlement
- **Kelly-criterion** position sizing
- Forward-validated live before containerization
- Honest caveat: forward results reflect a specific threshold regime and
  window; survival across regimes is the open research question, not a claim

## Quickstart (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your demo credentials
export $(grep -v '^#' .env | xargs)
uvicorn main:app --reload
```

Check: `curl localhost:8000/` (health) · `curl localhost:8000/predict`
(stub model) · `curl localhost:8000/balance` (real signed demo call).

## Quickstart (Docker)

```bash
docker build -t kalshi-phase1 .
docker run --rm -p 8000:8000 \
  -e KALSHI_KEY_ID="your-demo-key-id" \
  -e KALSHI_BASE_URL="https://external-api.demo.kalshi.co" \
  -e KALSHI_PRIVATE_KEY_PATH="/run/secrets/kalshi_key.pem" \
  -v "$(pwd)/kalshi_private_key.pem:/run/secrets/kalshi_key.pem:ro" \
  kalshi-phase1
```

The private key is mounted read-only at runtime — never baked into the image.

## Auth note (the part that costs people an hour)

Kalshi signs requests with RSA-PSS, not an API key header. The signed string
is `timestamp_ms + METHOD + path`, where the path includes `/trade-api/v2`
and excludes any query string. SHA-256 everywhere, salt length = digest size.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1 | Serving: FastAPI + signed Kalshi client, Dockerized | ✅ this repo |
| 2 | Inference: real model behind `/predict`; latency + throughput profiling | started — baseline measured (`bench.py`): p50 1.9 ms / p95 2.5 ms / p99 2.9 ms for the stub path over 2,000 in-process requests | 
| 3 | Data: capture pipeline for order books & settlements; backtest store | partial — historical capture + backtest store implemented (5,000 markets, used for the validation above); streaming capture and retraining feed not yet built |
| 4 | MLOps: monitoring, drift checks, scheduled retraining | planned |

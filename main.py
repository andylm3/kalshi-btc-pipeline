"""
Kalshi Demo Pipeline — Phase 1: Serving Layer
=============================================

A minimal FastAPI service that:
  1. exposes a health check              GET /
  2. returns a MOCK prediction           GET /predict   (placeholder for Phase 2 model)
  3. proves the sandbox connection works GET /balance   (real signed call to Kalshi demo)

Auth model (read once, save an hour):
Kalshi does NOT use a simple API-key header. Every authenticated request is
RSA-PSS signed. You sign the string:

        timestamp_ms + METHOD + path

where `path` includes the "/trade-api/v2" prefix and EXCLUDES any query
string. Three headers carry the result: KALSHI-ACCESS-KEY,
KALSHI-ACCESS-TIMESTAMP, KALSHI-ACCESS-SIGNATURE.
"""

import os
import time
import base64
import functools

import requests
from fastapi import FastAPI, HTTPException
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# --- Config from environment. Never hard-code secrets. ---
KALSHI_BASE_URL = os.getenv("KALSHI_BASE_URL", "https://external-api.demo.kalshi.co")
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID", "")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_private_key.pem")

BALANCE_PATH = "/trade-api/v2/portfolio/balance"

app = FastAPI(title="Kalshi Pipeline — Phase 1 (Serving)")


@functools.lru_cache(maxsize=1)
def load_private_key() -> rsa.RSAPrivateKey:
    """Load and cache the RSA private key once (not on every request)."""
    with open(KALSHI_PRIVATE_KEY_PATH, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def sign_pss(message: str) -> str:
    """
    RSA-PSS sign a message. SHA-256 for both the hash and MGF1, salt length
    equal to the digest length — matches Kalshi's official Python example.
    Returns a base64 string.
    """
    signature = load_private_key().sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=hashes.SHA256.digest_size,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def auth_headers(method: str, path: str) -> dict:
    """Build the three signed headers Kalshi requires for `method path`."""
    ts_ms = str(int(time.time() * 1000))
    return {
        "KALSHI-ACCESS-KEY": KALSHI_KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": ts_ms,
        "KALSHI-ACCESS-SIGNATURE": sign_pss(ts_ms + method.upper() + path),
    }


@app.get("/")
def health() -> dict:
    """Liveness probe: is the service up and configured?"""
    return {
        "status": "ok",
        "phase": 1,
        "kalshi_base": KALSHI_BASE_URL,
        "key_configured": bool(KALSHI_KEY_ID),
    }


@app.get("/predict")
def predict() -> dict:
    """
    Placeholder inference endpoint. Phase 2 replaces this stub with the real
    BTC settlement-window model. Shape is stable so clients don't change.
    """
    return {
        "market": "BTC-15MIN-DEMO",
        "p_yes": 0.5,          # mock probability
        "model": "stub-0.0",
        "note": "Phase 2 swaps in the real model behind this same route.",
    }


@app.get("/balance")
def balance() -> dict:
    """Real signed call to the Kalshi demo API — proves auth end to end."""
    if not KALSHI_KEY_ID:
        raise HTTPException(500, "KALSHI_KEY_ID not set")
    try:
        resp = requests.get(
            KALSHI_BASE_URL + BALANCE_PATH,
            headers=auth_headers("GET", BALANCE_PATH),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise HTTPException(502, f"Kalshi call failed: {exc}") from exc

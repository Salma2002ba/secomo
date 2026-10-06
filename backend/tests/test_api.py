"""Tests d'intégration de l'API SECOMO.

Ils s'exécutent contre une API qui tourne réellement (docker compose, Kubernetes…), avec sa base
PostgreSQL : c'est le même contrôle que celui du pipeline avant chaque déploiement.

    API_URL=http://localhost:8000 pytest backend/tests -v

Le compte de démonstration doit exister (SEED_DEMO_ACCOUNT=true).
"""

import os
import uuid

import httpx
import pytest

API_URL = os.environ.get("API_URL", "http://localhost:8000")
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "test@secomo.io")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Test1234!")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=API_URL, timeout=10) as c:
        yield c


def login(client: httpx.Client, email: str, password: str) -> dict:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="session")
def demo_headers(client):
    return login(client, DEMO_EMAIL, DEMO_PASSWORD)


# --- Santé ------------------------------------------------------------------------------------

def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# --- Comptes et authentification --------------------------------------------------------------

def test_register_then_login(client):
    email = f"ci-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/register", json={"email": email, "password": "Secret123!"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["email"] == email

    headers = login(client, email, "Secret123!")
    assert headers["Authorization"].startswith("Bearer ")


def test_register_twice_is_rejected(client):
    email = f"ci-{uuid.uuid4().hex[:8]}@example.com"
    body = {"email": email, "password": "Secret123!"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409


def test_wrong_password_is_rejected(client):
    resp = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "mauvais-mot-de-passe"})
    assert resp.status_code == 401


def test_protected_routes_require_a_token(client):
    # FastAPI répond 403 quand l'en-tête Authorization est absent
    assert client.get("/api/devices/").status_code in (401, 403)


# --- Appareils et mesures ---------------------------------------------------------------------

def test_demo_account_has_devices(client, demo_headers):
    resp = client.get("/api/devices/", headers=demo_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_esp_reading_requires_a_valid_api_key(client):
    resp = client.post("/api/esp/readings", json={"temp_air": 22.0}, headers={"X-API-Key": "cle-invalide"})
    assert resp.status_code == 401


def test_esp_reading_is_stored(client, demo_headers):
    device = client.get("/api/devices/", headers=demo_headers).json()[0]
    reading = {"temp_air": 23.4, "humidity_air": 61.0, "humidity_soil": 48.0, "light": 9000}

    resp = client.post("/api/esp/readings", json=reading, headers={"X-API-Key": device["api_key"]})
    assert resp.status_code == 201, resp.text

    readings = client.get(f"/api/devices/{device['id']}/readings", headers=demo_headers).json()
    assert any(r["temp_air"] == 23.4 for r in readings)


def test_dry_soil_raises_an_alert(client, demo_headers):
    device = client.get("/api/devices/", headers=demo_headers).json()[0]

    resp = client.post("/api/esp/readings", json={"humidity_soil": 5.0}, headers={"X-API-Key": device["api_key"]})
    assert resp.status_code == 201

    alerts = client.get("/api/alerts/", params={"device_id": device["id"]}, headers=demo_headers).json()
    assert any("humid" in a["category"].lower() for a in alerts), alerts

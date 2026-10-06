"""Métriques Prometheus de l'API SECOMO, exposées sur /metrics.

- Métriques techniques : nombre de requêtes HTTP et temps de réponse, par route et par code.
- Métriques métier : mesures reçues des ESP32 et alertes générées.
"""

import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "secomo_http_requests_total", "Requêtes HTTP reçues", ["method", "route", "status"]
)
HTTP_LATENCY = Histogram(
    "secomo_http_request_duration_seconds", "Temps de réponse des requêtes HTTP", ["method", "route"]
)
READINGS_RECEIVED = Counter("secomo_readings_received_total", "Mesures reçues des ESP32")
ALERTS_CREATED = Counter("secomo_alerts_created_total", "Alertes générées", ["type", "category"])


def setup_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def record_request(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        # Le modèle de route (/api/devices/{device_id}) évite une série par identifiant
        route = request.scope.get("route")
        path = getattr(route, "path", "inconnue")
        if path != "/metrics":
            HTTP_REQUESTS.labels(request.method, path, response.status_code).inc()
            HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
        return response

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

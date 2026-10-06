from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, engine, async_session
from app.metrics import setup_metrics
from app.models.station import Station  # noqa: F401 — ensures table is registered
from app.routers import auth, users, plants, devices, sensors, commands, alerts, watering, catalog, ws, stations
from app.services.seed import seed_default_plants, seed_test_account

settings = get_settings()

# Identifiant arbitraire du verrou PostgreSQL pris au démarrage
STARTUP_LOCK_KEY = 424242


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup : créer les tables et insérer les données par défaut.
    # Un verrou PostgreSQL (advisory lock) sérialise cette étape quand plusieurs répliques
    # de l'API démarrent en même temps (Kubernetes) : une seule initialise la base à la fois.
    async with engine.connect() as lock_conn:
        await lock_conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": STARTUP_LOCK_KEY})
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with async_session() as db:
                await seed_default_plants(db)
                if settings.SEED_DEMO_ACCOUNT:
                    await seed_test_account(db)
        finally:
            await lock_conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": STARTUP_LOCK_KEY})

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="SECOMO API",
    description="Backend de la Serre Connectée Modulaire",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_metrics(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plants.router)
app.include_router(devices.router)
app.include_router(sensors.router)
app.include_router(commands.router)
app.include_router(alerts.router)
app.include_router(watering.router)
app.include_router(catalog.router)
app.include_router(ws.router)
app.include_router(stations.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "secomo-backend"}

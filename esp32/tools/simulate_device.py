"""Simule un ESP32 SECOMO : envoie des mesures réalistes à l'API, sans matériel.

Utile pour faire une démonstration, tester le dashboard ou générer de la charge.

Usage :
    python simulate_device.py --api-key <CLE_DU_BAC> [--url http://localhost:8000]
                              [--count 60] [--interval 5]

La clé API d'un bac s'obtient depuis le dashboard (Appareils) ou dans la table devices.
Seule la bibliothèque standard de Python est utilisée.
"""

import argparse
import json
import math
import random
import time
import urllib.request


def reading(step: int) -> dict:
    """Mesures plausibles qui varient doucement au fil du temps."""
    t = step / 10
    return {
        "temp_air": round(24 + 3 * math.sin(t) + random.uniform(-0.3, 0.3), 1),
        "humidity_air": round(62 + 8 * math.cos(t / 2) + random.uniform(-1, 1), 1),
        "humidity_soil": round(max(20.0, 55 - (step % 40) * 0.6 + random.uniform(-1, 1)), 1),
        "light": round(max(0.0, 9000 + 4000 * math.sin(t / 3) + random.uniform(-300, 300)), 0),
        "soil_ph": round(6.5 + 0.2 * math.sin(t / 4), 2),
        "water_tank_level": round(max(5.0, 85 - step * 0.3), 1),
        "battery_level": round(max(10.0, 95 - step * 0.1), 1),
    }


def send(url: str, api_key: str, payload: dict) -> int:
    req = urllib.request.Request(
        f"{url}/api/esp/readings",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-key", required=True, help="clé API du bac (en-tête X-API-Key)")
    parser.add_argument("--url", default="http://localhost:8000", help="adresse du backend")
    parser.add_argument("--count", type=int, default=60, help="nombre de mesures à envoyer")
    parser.add_argument("--interval", type=float, default=5.0, help="secondes entre deux envois")
    args = parser.parse_args()

    for step in range(args.count):
        payload = reading(step)
        status = send(args.url, args.api_key, payload)
        print(f"[{step + 1}/{args.count}] HTTP {status} {payload}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

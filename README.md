<p align="center">
  <img src="docs/banner.svg" alt="SECOMO – Serre connectée modulaire" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ESP32-PlatformIO-E7352C?logo=espressif&logoColor=white" alt="ESP32">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/SQLAlchemy-async-D71F00?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/React-19-20232A?logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=white" alt="Docker Compose">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/CI%2FCD-Jenkins-D24939?logo=jenkins&logoColor=white" alt="Jenkins">
  <img src="https://img.shields.io/badge/Kubernetes-k3s-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes">
  <img src="https://img.shields.io/badge/Ansible-EE0000?logo=ansible&logoColor=white" alt="Ansible">
  <img src="https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white" alt="Prometheus">
  <img src="https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white" alt="Grafana">
  <img src="https://img.shields.io/badge/Loki-logs-F46800?logo=grafana&logoColor=white" alt="Loki">
  <img src="https://img.shields.io/badge/Trivy-1904DA?logo=aqua&logoColor=white" alt="Trivy">
  <img src="https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white" alt="pytest">
</p>

# SECOMO — Serre Connectée Modulaire

Un système complet pour **surveiller et piloter une serre** : un ESP32 lit les capteurs et
commande les actionneurs, une **API FastAPI** centralise les mesures et décide des alertes et de
l'arrosage, un **dashboard React** affiche tout en temps réel par WebSocket.

| | |
|---|---|
| **7** grandeurs mesurées (air, sol, lumière, pH, eau, batterie) | **6** actionneurs pilotés à distance (pompes, vannes, ventilateur, LED) |
| **37** routes d'API REST + 1 WebSocket temps réel | **5 515** plantes dans le catalogue intégré |
| Alertes et arrosage **automatiques** selon chaque plante | Plateforme complète en **une commande** Docker |
| Déploiement continu **Jenkins → Kubernetes** | **Observabilité** : métriques Prometheus, logs Loki, Grafana |

## Sommaire

- [Aperçu](#aperçu)
- [Architecture](#architecture)
- [Ce que fait le système](#ce-que-fait-le-système)
- [Lancer le projet](#lancer-le-projet)
- [Tester sans matériel](#tester-sans-matériel)
- [Le firmware ESP32](#le-firmware-esp32)
- [Structure du dépôt](#structure-du-dépôt)
- [Documentation](#documentation)
- [Chaîne DevOps : Ansible, Jenkins, Kubernetes, monitoring](#chaîne-devops--ansible-jenkins-kubernetes-monitoring)

---

## Aperçu

<p align="center">
  <img src="docs/screenshots/02-dashboard.jpg" alt="Dashboard temps réel" width="95%"><br>
  <b>Dashboard</b> : mesures en direct de chaque bac, comparées aux seuils de la plante cultivée
</p>

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/03-alertes.jpg" alt="Alertes"></td>
    <td width="50%"><img src="docs/screenshots/04-plantes.jpg" alt="Profils de plantes"></td>
  </tr>
  <tr>
    <td align="center"><b>Alertes</b> générées automatiquement, par bac et par gravité</td>
    <td align="center"><b>Profils de plantes</b> et leurs seuils de culture</td>
  </tr>
</table>

<p align="center">
  <img src="docs/screenshots/01-accueil.jpg" alt="Page d'accueil" width="70%">
</p>

> Captures prises sur la plateforme lancée avec Docker Compose, alimentée par le
> [simulateur d'ESP32](#tester-sans-matériel).

## Architecture

```mermaid
flowchart LR
    subgraph serre["Serre"]
        direction TB
        sensors["Capteurs<br/>BME280 · BH1750 · sol<br/>HC-SR04 · pH · batterie"]:::hw
        esp["ESP32<br/>firmware C++ PlatformIO"]:::hw
        relays["Module relais<br/>pompes · vannes<br/>ventilateur · LED"]:::hw
        sensors --> esp --> relays
    end

    subgraph plateforme["Plateforme"]
        direction TB
        api["API FastAPI<br/>REST + WebSocket"]:::api
        engines["Moteurs<br/>alertes · arrosage"]:::api
        db[("PostgreSQL 16<br/>migrations Alembic")]:::data
        api <--> engines
        api <--> db
    end

    ui["Dashboard React<br/>temps réel · FR / EN"]:::ui

    esp -- "mesures (clé API)<br/>commandes toutes les 30 s" <--> api
    api -- "REST (JWT)<br/>+ WebSocket" <--> ui

    classDef hw fill:#fde7f0,stroke:#e8397d,color:#1a1a1c
    classDef api fill:#e3f1fc,stroke:#3d9fe8,color:#1a1a1c
    classDef data fill:#efe7fb,stroke:#7B42BC,color:#1a1a1c
    classDef ui fill:#e2f7ee,stroke:#29c282,color:#1a1a1c
```

**Le trajet d'une mesure**

```mermaid
sequenceDiagram
    participant E as ESP32
    participant A as API FastAPI
    participant M as Moteurs
    participant D as PostgreSQL
    participant U as Dashboard

    E->>A: POST /api/esp/readings (X-API-Key)
    A->>D: enregistre la mesure
    A->>M: compare aux seuils de la plante
    M->>D: crée une alerte si un seuil est dépassé
    M->>D: planifie un arrosage si le sol est trop sec
    A-->>U: diffusion WebSocket : nouvelle mesure, nouvelle alerte
    E->>A: GET /api/esp/commands (toutes les 30 s)
    A-->>E: commandes à exécuter (pompe, ventilateur…)
    E->>A: POST /api/esp/commands/{id}/ack
```

## Ce que fait le système

**Mesure et suivi**
- Température et humidité de l'air, humidité du sol, luminosité, pH, niveau du réservoir,
  batterie.
- Historique en graphiques, par bac et par plage de temps.

**Décisions automatiques**
- **Moteur d'alertes** : chaque mesure est comparée aux seuils de la plante du bac et produit des
  alertes info, warning ou critical, en tenant compte de la nuit.
- **Moteur d'arrosage** : calcule la durée de pompage nécessaire pour remonter l'humidité du sol
  jusqu'à la cible, selon la taille du bac, avec un délai minimum entre deux arrosages.
- **Sécurité côté ESP32** : durée maximale par actionneur, pompe bloquée si le réservoir est trop
  bas, mode dégradé si le backend ne répond plus.

**Organisation**
- Plusieurs serres (stations) organisées en grilles de bacs, chaque bac relié à un ESP32.
- Profils de plantes personnalisables et catalogue de 5 515 plantes.
- Ajout d'un ESP32 par QR code et adresse MAC (*provisioning*).

**Interface** : bilingue français / anglais, thème clair ou sombre, adaptée au mobile.

**Sécurité**
- Comptes utilisateurs, mots de passe hachés (bcrypt), jetons JWT.
- Chaque ESP32 s'authentifie avec sa propre clé API.
- Aucun secret dans le code : variables d'environnement côté serveur, fichier `secrets.h` ignoré
  par Git côté firmware.

## Lancer le projet

Prérequis : Docker avec Docker Compose.

```bash
cp .env.example .env
docker compose up -d --build --wait
```

| Service | Adresse |
|---|---|
| Dashboard | http://localhost:8080 |
| API | http://localhost:8000 |
| Documentation de l'API (Swagger) | http://localhost:8000/docs |
| Santé de l'API | http://localhost:8000/api/health |

Avec `SEED_DEMO_ACCOUNT=true` (valeur du fichier d'exemple), un compte de démonstration est créé
avec une serre et 3 bacs : `test@secomo.io` / `Test1234!`. L'option est désactivée par défaut et
ne doit jamais être activée en production.

<details>
<summary>Lancer sans Docker (développement)</summary>

```bash
# API : Python 3.11+ et une base PostgreSQL accessible
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Dashboard : Node.js 18+
cd frontend
npm install
npm run dev
```

</details>

## Tester sans matériel

Le script [`esp32/tools/simulate_device.py`](esp32/tools/simulate_device.py) se fait passer pour
un ESP32 et envoie des mesures réalistes à l'API. Il n'utilise que la bibliothèque standard de
Python.

```bash
# Clés API des bacs du compte de démonstration
docker compose exec db psql -U secomo -d secomo -c "select name, api_key from devices"

# Envoyer 60 mesures, une toutes les 5 secondes
python esp32/tools/simulate_device.py --api-key <CLE_DU_BAC> --count 60 --interval 5
```

## Le firmware ESP32

Code C++ pour ESP32 DevKit v1, compilé avec PlatformIO, découpé en modules : `sensors`,
`actuators`, `network`, `automation`, `provisioning`.

```bash
cd esp32
cp src/secrets.example.h src/secrets.h   # WiFi et adresse du backend (fichier ignoré par Git)
pio run --target upload
pio device monitor                       # 115200 bauds
```

<details>
<summary>Branchements des capteurs et des actionneurs</summary>

| Capteur | Mesure | Interface | Broche(s) |
|---|---|---|---|
| BME280 | Température, humidité de l'air, pression | I2C | SDA 21, SCL 22 |
| BH1750 | Luminosité (lux) | I2C | SDA 21, SCL 22 |
| Capteur capacitif | Humidité du sol | Analogique | GPIO 32 |
| HC-SR04 | Niveau du réservoir | Trig / Echo | GPIO 5 / 18 |
| PH4502C | pH | Analogique | GPIO 33 |
| Pont diviseur | Batterie | Analogique | GPIO 36 |

| Broche | Actionneur (module relais) |
|---|---|
| GPIO 26 | Pompe principale |
| GPIO 27 | Pompe péristaltique |
| GPIO 14 | Ventilateur |
| GPIO 12 | Électrovanne A |
| GPIO 13 | LED horticole |
| GPIO 25 | Électrovanne B |

</details>

## Structure du dépôt

```text
.
├── backend/                 API FastAPI
│   ├── app/routers/         12 routeurs : auth, plantes, appareils, capteurs, alertes, arrosage, WebSocket…
│   ├── app/services/        Moteurs d'alertes et d'arrosage, données initiales
│   ├── app/models/          Modèles SQLAlchemy (async)
│   └── alembic/             Migrations de la base
├── frontend/                Dashboard React + Vite (servi par Nginx en conteneur)
├── esp32/
│   ├── src/                 Firmware C++ (PlatformIO)
│   └── tools/               Simulateur d'ESP32, moniteur série, générateur de QR codes
├── k8s/                     Manifestes Kubernetes : PostgreSQL, API, dashboard, Ingress
│   └── monitoring/          Prometheus (règles d'alerte), Loki + Alloy (logs), Grafana (tableau de bord provisionné)
├── ops/
│   ├── ansible/             Playbook qui prépare la plateforme (k3d, secrets, Jenkins)
│   ├── jenkins/             Image Jenkins configurée en code (plugins, compte, job)
│   └── deploy.sh            Déploiement sur le cluster
├── Jenkinsfile              Pipeline CI/CD
├── docs/                    Notice utilisateur, cahier des charges embarqué, déploiement
├── docker-compose.yml       Base + API + dashboard en local
└── .env.example             Variables à copier dans .env
```

## Documentation

- [Notice utilisateur](docs/notice-utilisateur.md) : prise en main du dashboard.
- [Cahier des charges embarqué](docs/cahier-des-charges-embarque.md) : capteurs, actionneurs,
  protocole, modes dégradés.
- [Déploiement du backend](docs/deploiement-backend.md) : variables d'environnement et hébergement.

## Chaîne DevOps : Ansible, Jenkins, Kubernetes, monitoring

Toute la chaîne tourne sur un poste Linux ou WSL : une fois Docker et Ansible installés, aucun droit
administrateur n'est nécessaire.

```mermaid
flowchart LR
    dev(["git push"]):::trigger

    subgraph prep["① Ansible prépare la plateforme"]
        direction TB
        a1["kubectl + k3d"]:::ops
        a2["cluster Kubernetes k3s"]:::ops
        a3["secrets générés"]:::ops
        a4["Jenkins configuré en code"]:::ops
    end

    subgraph ci["② Pipeline Jenkins"]
        direction TB
        j1["build des images"]:::ci
        j2["scan Trivy"]:::ci
        j3["déploiement"]:::ci
        j4["tests d'intégration<br/>contre le cluster"]:::ci
        j1 --> j2 --> j3 --> j4
    end

    subgraph k8s["③ Kubernetes · namespace secomo"]
        direction TB
        ing["Ingress Traefik<br/>localhost:8081"]:::k8s
        api["API × 2 répliques<br/>sondes + /metrics"]:::k8s
        front["Dashboard"]:::k8s
        pg[("PostgreSQL<br/>volume persistant")]:::k8s
        ing --> api & front
        api --> pg
    end

    subgraph mon["④ Monitoring"]
        direction TB
        prom["Prometheus<br/>métriques · alertes"]:::mon
        loki["Loki ← Alloy<br/>logs des pods"]:::mon
        graf["Grafana<br/>tableau de bord"]:::mon
        prom --> graf
        loki --> graf
    end

    prep -.-> ci
    dev --> j1
    j3 --> ing
    prom -- "collecte /metrics" --> api

    classDef trigger fill:#1a1a1c,stroke:#8b8b94,color:#f0ede8
    classDef ops fill:#fde7f0,stroke:#e8397d,color:#1a1a1c
    classDef ci fill:#fff3e0,stroke:#D24939,color:#1a1a1c
    classDef k8s fill:#e3f1fc,stroke:#326CE5,color:#1a1a1c
    classDef mon fill:#e2f7ee,stroke:#29c282,color:#1a1a1c
```

### ① Ansible : préparer la plateforme

```bash
ansible-playbook -i ops/ansible/inventory.ini ops/ansible/playbook.yml
```

Le [playbook](ops/ansible/playbook.yml) installe `kubectl` et `k3d`, crée le cluster Kubernetes,
génère les secrets de l'application (stockés dans `~/.secomo`, hors du dépôt) et démarre Jenkins.
Il est **idempotent** : relancé, il ne change rien de ce qui est déjà en place.

### ② Jenkins : intégration et déploiement continus

Jenkins est entièrement **configuré en code** ([`ops/jenkins/`](ops/jenkins/)) : plugins,
compte administrateur et job du pipeline sont créés au démarrage (Configuration as Code + Job DSL).
Il surveille la branche `main` et lance le [`Jenkinsfile`](Jenkinsfile) à chaque nouveau commit :

| Étape | Ce qu'elle fait |
|---|---|
| Build | Images Docker de l'API et du dashboard, taguées `<build>-<commit>` |
| Scan Trivy | Vulnérabilités hautes et critiques, rapport archivé avec le build |
| Déploiement | Import des images dans le cluster, application des manifestes, attente du rollout |
| Tests | Les 9 tests d'intégration ([`backend/tests`](backend/tests)) tournent contre l'application déployée ; résultats JUnit publiés dans Jenkins |

Jenkins : http://localhost:8090 (compte `admin`, mot de passe dans `~/.secomo/jenkins_admin_password`).

### ③ Kubernetes

| Composant | Objet | Points clés |
|---|---|---|
| API | Deployment × 2 | Sondes `readiness` et `liveness` sur `/api/health`, limites CPU et mémoire, attente de la base au démarrage, verrou PostgreSQL pour que deux répliques n'initialisent pas la base en même temps |
| Dashboard | Deployment | Nginx, fichiers statiques |
| PostgreSQL | Deployment + PersistentVolumeClaim | Données conservées entre les redéploiements |
| Configuration | ConfigMap + Secret | Aucun mot de passe dans les manifestes |
| Accès | Ingress (Traefik) | `/api` vers l'API, `/` vers le dashboard, `/grafana` vers Grafana |

Application : http://localhost:8081 · Swagger : http://localhost:8081/docs

### ④ Monitoring

L'API expose ses métriques sur `/metrics` ([`app/metrics.py`](backend/app/metrics.py)) :

- **techniques** : requêtes par route et par code HTTP, temps de réponse ;
- **métier** : mesures reçues des ESP32, alertes générées par catégorie.

Prometheus découvre automatiquement les pods annotés et évalue 3 règles d'alerte :

| Alerte | Condition |
|---|---|
| `ApiIndisponible` | Un pod de l'API ne répond plus depuis 1 minute |
| `TauxErreursEleve` | Plus de 5 % d'erreurs 5xx sur 5 minutes |
| `AucuneMesureRecue` | Aucune mesure des ESP32 depuis 15 minutes |

Les **logs** de tous les pods sont collectés par **Grafana Alloy** (via l'API Kubernetes) et
stockés dans **Loki**, avec les étiquettes `app`, `pod` et `container` pour filtrer.

Grafana (http://localhost:8081/grafana) est livré avec ses deux sources de données (Prometheus et
Loki) et son tableau de bord, sans aucune configuration manuelle : métriques et logs côte à côte.

<p align="center">
  <img src="docs/screenshots/05-grafana.jpg" alt="Tableau de bord Grafana : métriques" width="95%"><br>
  <b>Métriques</b> : trafic par route, temps de réponse, mesures reçues, alertes par catégorie
</p>

<p align="center">
  <img src="docs/screenshots/06-grafana-logs.jpg" alt="Logs de l'API dans Grafana" width="95%"><br>
  <b>Logs</b> de l'API dans Loki : chaque mesure reçue d'un ESP32, chaque requête
</p>

---

<p align="center">
  <b>Salma Baba</b> · Ingénieure DevOps & DevSecOps ·
  <a href="https://salmababa.com">salmababa.com</a>
</p>

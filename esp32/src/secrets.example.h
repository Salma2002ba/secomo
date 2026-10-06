#ifndef SECRETS_H
#define SECRETS_H

// Copier ce fichier en secrets.h (ignoré par Git) et renseigner les valeurs locales.

// Réseau WiFi 2,4 GHz (l'ESP32 ne gère pas le 5 GHz)
#define WIFI_SSID     "NOM_DU_RESEAU"
#define WIFI_PASSWORD "MOT_DE_PASSE"

// Adresse IP de la machine qui fait tourner le backend (pas localhost)
#define BACKEND_URL   "http://192.168.1.100:8000"

#endif

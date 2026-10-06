"""Affiche en direct les mesures envoyées par l'ESP32 sur le port série pendant une minute.

Usage : python serial_monitor.py [PORT]   (par défaut COM3 sous Windows, ex. /dev/ttyUSB0 sous Linux)
"""
import re
import sys
import time

import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else 'COM3'
ser = serial.Serial(PORT, 115200, timeout=6)
time.sleep(3)
print('=== SECOMO - Temps reel (1 min) ===')
print(f'{"Heure":<10} {"Luminosite":<14} {"Sol":<10} {"Temp":<10} {"Humidite":<10}')
print('-' * 55)

start = time.time()
while time.time() - start < 60:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
    if 'Lux=' not in clean:
        continue
    lux  = re.search(r'Lux=([\d\-\.]+)', clean)
    sol  = re.search(r'Sol1=([\d\-\.]+)', clean)
    temp = re.search(r'T=([\d\-\.]+)', clean)
    hum  = re.search(r'H=([\d\-\.]+)', clean)
    ts = time.strftime('%H:%M:%S')
    lv = (lux.group(1)  + ' lux') if lux  else '?'
    sv = (sol.group(1)  + ' %')   if sol  else '?'
    tv = (temp.group(1) + ' C')   if temp else '?'
    hv = (hum.group(1)  + ' %')   if hum  else '?'
    print(f'{ts:<10} {lv:<14} {sv:<10} {tv:<10} {hv:<10}')

ser.close()
print('\n--- Fin (1 min ecoulee) ---')

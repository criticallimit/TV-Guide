#!/usr/bin/with-contenv bashio
set -e

mkdir -p /homeassistant/www/tv-guide-logos
cp /app/lovelace/tv-guide-card.js /homeassistant/www/tv-guide-card.js
cp /app/www/logos/*.png /homeassistant/www/tv-guide-logos/

exec python3 /app/app.py

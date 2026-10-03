#!/usr/bin/with-contenv bashio
set -e

mkdir -p /homeassistant/www/tv-guide-logos

cat /app/www/guide-core.js /app/lovelace/tv-guide-card.js > /homeassistant/www/tv-guide-card.js
cp /app/lovelace/tv-guide-card-loader.js /homeassistant/www/tv-guide-card-loader.js
cp /app/www/styles.css /homeassistant/www/tv-guide-styles.css
cp /app/www/logos/*.png /homeassistant/www/tv-guide-logos/

exec python3 /app/app.py

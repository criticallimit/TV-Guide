#!/usr/bin/with-contenv bashio
set -e

mkdir -p /homeassistant/www

loader_tmp="/homeassistant/www/.tv-guide-card-loader.js.tmp"
card_tmp="/homeassistant/www/.tv-guide-card.js.tmp"

cp /app/lovelace/tv-guide-card.js "$card_tmp"
cp /app/lovelace/tv-guide-card-loader.js "$loader_tmp"

mv "$card_tmp" /homeassistant/www/tv-guide-card.js
mv "$loader_tmp" /homeassistant/www/tv-guide-card-loader.js

exec python3 /app/app.py

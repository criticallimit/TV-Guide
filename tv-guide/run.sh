#!/usr/bin/with-contenv bashio
set -e

mkdir -p /homeassistant/www/tv-guide-logos

# Publish the generated Lovelace bundle atomically so Home Assistant can never
# read a half-written JavaScript file while the add-on is starting.
bundle_tmp="/homeassistant/www/.tv-guide-card.js.tmp"
loader_tmp="/homeassistant/www/.tv-guide-card-loader.js.tmp"
styles_tmp="/homeassistant/www/.tv-guide-styles.css.tmp"

cat /app/www/guide-core.js /app/lovelace/tv-guide-card.js > "$bundle_tmp"
cp /app/lovelace/tv-guide-card-loader.js "$loader_tmp"
cp /app/www/styles.css "$styles_tmp"

mv "$bundle_tmp" /homeassistant/www/tv-guide-card.js
mv "$loader_tmp" /homeassistant/www/tv-guide-card-loader.js
mv "$styles_tmp" /homeassistant/www/tv-guide-styles.css

cp /app/www/logos/*.png /homeassistant/www/tv-guide-logos/

exec python3 /app/app.py

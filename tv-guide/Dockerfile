ARG BUILD_ARCH
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base-python:3.13-alpine3.21

ARG BUILD_ARCH
ARG BUILD_VERSION

LABEL \
  io.hass.name="TV Guide" \
  io.hass.description="Multilingual TV guide for Home Assistant with channel lists, reminders and five optional sensors for automations" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}"

WORKDIR /app
COPY app.py /app/app.py
COPY tvguide /app/tvguide
COPY www /app/www
COPY data /app/data
COPY lovelace /app/lovelace
COPY run.sh /run.sh

RUN apk add --no-cache tzdata && chmod a+x /run.sh

CMD ["/run.sh"]

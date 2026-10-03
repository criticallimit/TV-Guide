ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.name="TV Guide" \
  io.hass.description="Fernsehzeitschrift für Home Assistant" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}"

WORKDIR /app
COPY app.py /app/app.py
COPY www /app/www
COPY data /app/data
COPY fetch_logos.py /app/fetch_logos.py
COPY run.sh /run.sh

RUN python3 /app/fetch_logos.py \
    && rm /app/fetch_logos.py \
    && chmod a+x /run.sh

CMD ["/run.sh"]

FROM debian:bookworm-slim

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    netcat-openbsd \
    opendkim \
    opendkim-tools \
    postfix \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --home-dir /var/mail/support --shell /usr/sbin/nologin support

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
 && mkdir -p /var/lib/opendkim/keys

ENTRYPOINT ["/entrypoint.sh"]

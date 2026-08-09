FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    POWERSHELL_TELEMETRY_OPTOUT=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates wget python3 openjdk-21-jdk-headless util-linux \
 && wget -q https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb -O /tmp/packages-microsoft-prod.deb \
 && dpkg -i /tmp/packages-microsoft-prod.deb \
 && rm /tmp/packages-microsoft-prod.deb \
 && apt-get update \
 && apt-get install -y --no-install-recommends powershell \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 10002 runner \
 && useradd --uid 10002 --gid 10002 --create-home --shell /usr/sbin/nologin runner \
 && mkdir -p /app /ipc /work

COPY app /app
WORKDIR /app
ENTRYPOINT ["python3", "/app/code_worker.py"]

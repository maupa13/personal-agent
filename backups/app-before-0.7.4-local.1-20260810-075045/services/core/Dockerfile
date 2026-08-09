FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip install --no-cache-dir -r /tmp/requirements.txt
COPY app /app
RUN mkdir -p /data \
 && useradd --uid 10001 --create-home --shell /usr/sbin/nologin rpa \
 && chown -R rpa:rpa /app /data
USER rpa
EXPOSE 8080
CMD ["python","/app/main.py"]

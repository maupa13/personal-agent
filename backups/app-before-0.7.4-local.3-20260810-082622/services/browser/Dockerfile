FROM mcr.microsoft.com/playwright/python:v1.61.0-noble
WORKDIR /app
RUN python -m pip install --no-cache-dir playwright==1.61.0
COPY app /app
USER pwuser
CMD ["python", "-u", "/app/browser_worker.py"]

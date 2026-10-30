FROM mcr.microsoft.com/playwright/python:v1.55.0-noble
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt
USER pwuser

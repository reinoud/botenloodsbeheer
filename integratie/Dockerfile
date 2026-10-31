# Integratiecontainer (ADR-012): eigen image zonder applicatiecode, alleen de standaardbibliotheek.
FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /integratie
COPY koppeling koppeling
RUN useradd --system --uid 10001 koppeling
USER 10001
CMD ["python", "-m", "koppeling"]

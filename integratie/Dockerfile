# Integratiecontainer (ADR-012): eigen image zonder applicatiecode, alleen de standaardbibliotheek.
FROM python:3.14-slim@sha256:cd89c30eda26ee911a4611b18680086e0ea42e6f5f8cbe653d07fa7958c9cec8
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /integratie
COPY koppeling koppeling
# Zonder pip: niet nodig en het brengt eigen kopieën van urllib3 en msgpack mee (#59).
RUN pip uninstall --yes --no-cache-dir pip && useradd --system --uid 10001 koppeling
USER 10001
CMD ["python", "-m", "koppeling"]

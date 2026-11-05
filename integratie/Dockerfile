# Integratiecontainer (ADR-012): eigen image zonder applicatiecode, alleen de standaardbibliotheek.
FROM python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /integratie
COPY koppeling koppeling
# Zonder pip: niet nodig en het brengt eigen kopieën van urllib3 en msgpack mee (#59).
RUN pip uninstall --yes --no-cache-dir pip && useradd --system --uid 10001 koppeling
USER 10001
CMD ["python", "-m", "koppeling"]

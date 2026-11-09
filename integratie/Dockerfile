# Integratiecontainer (ADR-012): eigen image zonder applicatiecode. De API-aanroepen gebruiken alleen
# de standaardbibliotheek; zeep (met zijn afhankelijkheden, vastgepind met hashes) is er alleen voor
# de bron e-boekhouden.
FROM python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d AS bouw
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes --only-binary :all: --target /pakketten -r requirements.txt

# Alleen voor tests (tests/integratie): voegt pytest toe, ook vastgepind met hashes.
FROM bouw AS test
COPY requirements-test.txt .
RUN pip install --no-cache-dir --require-hashes --only-binary :all: --target /pakketten -r requirements-test.txt
ENV PYTHONPATH=/pakketten:/integratie PYTHONDONTWRITEBYTECODE=1
WORKDIR /integratie
COPY koppeling koppeling
RUN useradd --system --uid 10001 koppeling
USER 10001
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider", "-q", "/tests"]

FROM python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/pakketten
WORKDIR /integratie
COPY --from=bouw /pakketten /pakketten
COPY koppeling koppeling
# shortcut: zlib1g uit Debian bijwerken (CVE-2026-85091), weg zodra het basisimage deb13u1 heeft.
RUN apt-get update && apt-get install --yes --no-install-recommends zlib1g \
    && rm -rf /var/lib/apt/lists/*
# Zonder pip: niet nodig en het brengt eigen kopieën van urllib3 en msgpack mee (#59).
RUN pip uninstall --yes --no-cache-dir pip && useradd --system --uid 10001 koppeling
USER 10001
CMD ["python", "-m", "koppeling"]

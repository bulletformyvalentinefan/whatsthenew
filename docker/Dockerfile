# Imagen del pipeline efímero: trae datos, los analiza con OpenCode y abre un PR
# con la propuesta. No deja procesos vivos: se ejecuta y muere.
FROM python:3.12-slim

# Versión de OpenCode fijada para que la imagen sea reproducible.
ARG OPENCODE_VERSION=2.0.23

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # OpenCode se instala en $HOME/.opencode/bin
    PATH="/root/.opencode/bin:${PATH}"

# git  -> para clonar el repo privado del plan y hacer la rama del PR.
# curl/tar/ca-certificates -> instalador de OpenCode y HTTPS.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl tar \
 && rm -rf /var/lib/apt/lists/*

# OpenCode (motor de análisis). El instalador descarga el binario nativo.
RUN curl -fsSL https://opencode.ai/v2/install | bash -s -- --version "${OPENCODE_VERSION}" --no-modify-path \
 && /root/.opencode/bin/opencode --version

WORKDIR /app

# Dependencias primero (mejor caché de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código, catálogos y el agente de OpenCode
COPY src/ ./src/
COPY config/ ./config/
COPY output/ ./output/
COPY opencode.jsonc ./
COPY .opencode/ ./.opencode/

ENV PYTHONPATH=/app/src

# Se ejecuta una vez y termina (contenedor efímero).
ENTRYPOINT ["python", "-m", "whatsthenew"]
CMD ["run"]

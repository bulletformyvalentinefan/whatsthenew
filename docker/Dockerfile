# Imagen liviana del pipeline efímero
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primero (mejor caché de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código y configuración
COPY src/ ./src/
COPY config/ ./config/
COPY output/ ./output/

ENV PYTHONPATH=/app/src

# Se ejecuta una vez y termina (contenedor efímero)
ENTRYPOINT ["python", "-m", "whatsthenew"]
CMD ["run"]

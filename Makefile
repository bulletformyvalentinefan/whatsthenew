.PHONY: help install run publish test lint secrets clean docker-build docker-run docker-server server-install

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Crea venv e instala dependencias
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run: ## Ejecuta el pipeline una vez (sin publicar)
	python -m whatsthenew run --no-publish

publish: ## Ejecuta el pipeline y abre el PR de propuesta
	python -m whatsthenew run --publish

test: ## Corre las pruebas
	python -m pytest -q

lint: ## Revisa el estilo (opcional, si tienes ruff)
	ruff check src tests || true

secrets: ## Verifica que no haya secretos versionados
	./scripts/check-secrets.sh

clean: ## Borra temporales y cachés
	rm -f /tmp/whatsthenew_raw.json
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

docker-build: ## Construye la imagen (local)
	docker build -f docker/Dockerfile -t whatsthenew:local .

docker-run: ## Ejecuta el contenedor efímero (build local)
	docker compose -f docker/docker-compose.yml run --rm whatsthenew

docker-server: ## Baja la imagen de GHCR y ejecuta (servidor)
	docker compose -f docker/docker-compose.server.yml run --rm whatsthenew

server-install: ## Prepara el servidor (imagen GHCR + timer semanal)
	./scripts/server-install.sh

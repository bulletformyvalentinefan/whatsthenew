.PHONY: help install run test lint clean docker-build docker-run

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Crea venv e instala dependencias
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run: ## Ejecuta el pipeline una vez
	python -m whatsthenew run

test: ## Corre las pruebas
	python -m pytest -q

lint: ## Revisa el estilo (opcional, si tienes ruff)
	ruff check src tests || true

clean: ## Borra temporales y cachés
	rm -f /tmp/whatsthenew_raw.json
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

docker-build: ## Construye la imagen
	docker build -f docker/Dockerfile -t whatsthenew:local .

docker-run: ## Ejecuta el contenedor efímero
	docker compose -f docker/docker-compose.yml run --rm whatsthenew

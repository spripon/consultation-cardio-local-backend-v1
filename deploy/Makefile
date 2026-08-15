# Cibles de déploiement. Aucune action destructive implicite :
# rien n'est supprimé, aucun volume n'est purgé, aucun processus n'est tué.
SHELL := /bin/bash
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))..)
COMPOSE := docker compose -f $(ROOT)/deploy/docker-compose.yml

.PHONY: help preflight prepare-config models models-speech build validate up down logs-api

help:
	@echo "Cibles disponibles :"
	@echo "  make prepare-config  Crée backend/.env et deploy/caddy.env (jamais écrasés)"
	@echo "  make models          Télécharge le modèle PII local (phase installation)"
	@echo "  make models-speech   Idem + modèle faster-whisper small"
	@echo "  make build           Construit les images Docker (web + api), sans npm hôte"
	@echo "  make preflight       Vérifications lecture seule avant démarrage"
	@echo "  make validate        no-egress + compose config + build images (sans démarrage)"
	@echo "  make up              preflight puis docker compose up -d"
	@echo "  make down            Arrête la pile (volumes conservés)"
	@echo "  make logs-api        Journaux de l'API (sans contenu patient)"

prepare-config:
	bash $(ROOT)/deploy/prepare-config.sh

models:
	bash $(ROOT)/deploy/download-models.sh

models-speech:
	bash $(ROOT)/deploy/download-models.sh --with-speech

build:
	$(COMPOSE) build

preflight:
	bash $(ROOT)/deploy/preflight-ubuntu.sh

validate:
	bash $(ROOT)/deploy/validate-install.sh

up: preflight
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs-api:
	$(COMPOSE) logs -f --tail=200 api

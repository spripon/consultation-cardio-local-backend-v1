# Cibles de deploiement. Aucune action destructive implicite.
SHELL := /bin/bash
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))..)
COMPOSE := docker compose -f $(ROOT)/deploy/docker-compose.yml

.PHONY: help preflight prepare-config models models-speech build validate up down logs-api logs-web cloudflare-check

help:
	@echo "Cibles disponibles :"
	@echo "  make prepare-config   Cree backend/.env et deploy/caddy.env"
	@echo "  make models           Telecharge le modele PII local"
	@echo "  make models-speech    Idem + faster-whisper small"
	@echo "  make build            Construit les images Docker web + api"
	@echo "  make preflight        Verifications locales lecture seule"
	@echo "  make validate         no-egress + compose config + build, sans demarrage"
	@echo "  make up               Preflight puis demarre api+web sur 127.0.0.1:8091"
	@echo "  make cloudflare-check Valide le chemin public via Cloudflare Tunnel"
	@echo "  make down             Arrete uniquement cette pile"
	@echo "  make logs-api         Journaux API"
	@echo "  make logs-web         Journaux Caddy/frontend"

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

cloudflare-check:
	bash $(ROOT)/deploy/validate-cloudflare-tunnel.sh

down:
	$(COMPOSE) down

logs-api:
	$(COMPOSE) logs -f --tail=200 api

logs-web:
	$(COMPOSE) logs -f --tail=200 web

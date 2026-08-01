# Ensure recipes run through Bash instead of the default sh
SHELL := /bin/bash
.SHELLFLAGS := -c

# Default target when running just 'make'
.DEFAULT_GOAL := help

.PHONY: help build start stop seed rebuild update api-logs

## Help menu displaying available commands
help:
	@echo "Available commands:"
	@sed -n 's/^##//p' $(MAKEFILE_LIST) | column -t -s ':' |  sed -e 's/^/  /'

## build: Build The Initial App and DataBase Containers
build:
	docker compose up -d --build api

## start: Start The Services after the Initial Build
start:
	docker compose up -d api

## stop: Stop the Services
stop:
	docker compose down

## seed: Seed the DataBase with fresh Data
seed:
	docker compose run --rm seeder

## rebuild: Rebuild the Images
rebuild:
	docker compose down
	docker compose up --build -d api

## update: Update The DataBase with Fresh Data
update:
	docker compose run --rm updater

## api-logs: Shows Logs from API
show-logs:
	docker logs -f api

## run the tests
test:
	uv run pytest -v
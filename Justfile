# Execution Through Bash
set shell := ["bash", "-c"]

@_default:
    just --list

[ doc( "Build The Initial App and DataBase Containers" ) ]
build:
    docker compose up -d --build api

[ doc( "Start The Services after the Initial Build" ) ]
start:
    docker compose up -d api

[ doc( "Stop the Services" ) ]
stop:
    docker compose down

[ doc( "Seed the DataBase with fresh Data" ) ]
seed:
    docker compose run --rm seeder

[ doc( "Rebuild the Images" ) ]
rebuild:
    docker compose down
    docker compose up --build -d api

[ doc( "Update The DataBase with Fresh Data" ) ]
update:
    docker compose run --rm updater

[doc( "Shows Logs from API" )]
api-logs:
    docker compose up api

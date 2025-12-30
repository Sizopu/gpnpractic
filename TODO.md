# TODO

## Исходные данные

Есть репозиторий с Sandbox проектом на ранней стадии готовности максимально приближенный к архитектуре реального проекта.

В репозитории есть исходный код, Dockerfile-ы нескольких сервисов и файл `.env`:

- Backend
- Java.Obs
- Minio
- Postgres
- Redis
- Dotnet
- Dockerfile
- Javascript.Obs
- Minio.Migration
- Postgres.Migration
- Frontend
- Keycloak
- PGAdmin
- RabbitMQ

## Задания

1. По имеющимся данным составить `docker-compose.yaml`, для каждого сервиса написать healthcheck, продемонстрировать запуск приложения.

2. Установить K3s или Minikube локально и на основе ранее подготовленного `docker-compose.yaml`:
    - написать YAML-манифесты для Kubernrtes,
    - продемостировать деплой приложения в локальный кластер K3s или Minikube.

3. На основе манифестов написать Helm-чарт, продемонстриовать деплой через Helm в локальный кластер.

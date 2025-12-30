# Quotation Book 

## Описание проекта
Данный проект представляет собой пример микросервисного приложения **"Quotation Book"** (Книга цитат), реализованного на базе фреймворка **devops-tools**.

## Назначение
**Quotation Book** — это веб-приложение (песочница), в рамках которого реализованы примеры использования:

### Функциональные возможности:
- **Выдача случайных цитат**
- **Генерация процедурных изображений**
- **Создание PDF-файлов со случайным содержанием**
- **Минимально-жизнеспособная сконфигурированная система мониторинга приложения**

### Интеграционные компоненты:
- **[Типовое решение devops-tools](https://git.devzone.local/devzone/NonProgram/u200004862/inner-source/devops-tools/devops-tools.git)**
- **Комплексный формат репозитория**
- **Кэш-сервер Redis**
- **Сервер аутентификации Keycloak**
- **Объектное хранилище Minio S3**
- **СУБД PostgreSQL**
- **NFS-хранилище**
- **Брокер сообщений RabbitMQ**
- **Фоновый обработчик задач RabbitMQ**
- **Инструмент администрирования PostgreSQL - pgAdmin**
- **Варианты миграции для PostgreSQL и Minio**
- **[Типовое решение для Nginx с необх. требованиями ИБ](https://git.devzone.local/devzone/NonProgram/u200004862/inner-source/docker/common-images/-/tree/fea/nginx)**
- **Сборка на основе базовых образов RedOS**
- **Health-check система на платформе .NET**
- **Java-приложения для сбора телеметрии**
- **реализация фронтенда на базе node.js, обслуживающий бекенды .NET и Java**

## Документация

### Основные разделы:

- [Быстрый старт](docs/quickstart.md) - локальная сборка и запуск через docker-compose
- [Архитектура приложения](docs/architecture.md) - схема взаимодействия компонентов
- [Используемые компоненты](docs/components.md) - список и краткое описание используемых сервисов
- [Аутентификация](docs/authentication.md) - Описание функционала Keycloak
- [Хранилища](docs/storage.md) - Описание функционала PostgreSQL, Redis, Minio S3, NFS
- [Очереди сообщений](docs/messaging.md) - Описание очереди сообщений RabbitMQ
- [API endpoints](docs/api.md) - описание всех маршрутов
- [Observability](docs/observability.md) - Описание конфигурации системы мониторинга приложения.


## Структура проекта

<pre>
├── ci/                          # Конфигурационные файлы CI/CD
│   ├── build-props.yaml         # Параметры для сборки Dockfiles под devzone/trust контур.
│   ├── services-model.yaml      # Конф. файл для сервисов и ландшафтов под деплой.
│   ├── secrets-model.yaml       # Конф. файл для описания секретов
│   ├── devops-tools/           # Фреймворк DevOpsTools
│   │   ├── docs/
│   │   ├── helm/
│   │   ├── jenkins/
│   │   └── ...
│   ├── helm/                    # Helm chart'ы для default/devzone/uat/preprod/prod окружений.
│   │   └── services/
│   └── local/                   # Конфигурация для локальной сборки проекта
│       └── docker-compose.yaml
├── docker/                      # Dockerfile'ы и конфигурации для всех сервисов
│   ├── bin/                     # Исполняемые файлы и скрипты
│   ├── certs/                   # Корневые Сертификаты
│   ├── config/                  # Конфигурационные файлы для сборки сервисов
│   │   ├── QB.Backend/
│   │   ├── QB.Frontend/
│   │   ├── QB.Keycloak/
│   │   └── QB.Postgres.Migration/
│   ├── ssl/                     # SSL конфигурации для сервера
│   ├── yum.repos.d/             # Репозитории RedOS
│   ├── QB.Backend.Dockerfile
│   ├── QB.Frontend.Dockerfile
│   ├── QB.Keycloak.Dockerfile
│   ├── QB.Postgres.Dockerfile
│   ├── QB.Redis.Dockerfile
│   ├── QB.RabbitMQ.Dockerfile
│   ├── QB.pgAdmin.Dockerfile
│   └── ...
├── src/                         # Исходный код приложений
│   └── QB.Backend/              # Бэкенд приложение
│       ├── app/
│       │   ├── __init__.py                 # Инициализация Flask-приложения (create_app)
│       │   ├── config.py                   # Конфигурация (переменные окружения)
│       │   ├── extensions.py               # Инициализация внешних сервисов (DB, Redis, S3)
│       │   ├── routes/                     # Маршруты Flask
│       │   │   ├── __init__.py             # Регистрация всех blueprint'ов
│       │   │   ├── main.py                 # Основные маршруты (/jason, /check, /)
│       │   │   ├── auth.py                 # Маршруты аутентификации (/auth/...)
│       │   │   ├── gallery.py              # Маршруты галереи (/gallery, /generate-images...)
│       │   │   └── library.py              # Маршруты библиотеки (/library/...)
│       │   ├── utils/                      # Вспомогательные функции
│       │   │   ├── __init__.py             
│       │   │   ├── content_generation.py   # Генерация контента (цитаты, PDF, изображения)
│       │   │   ├── static_files.py         # Работа со статикой (init_static_dir, generate_sample_files...)
│       │   │   └── task_helpers.py         # Функции для работы с задачами(Redis, RabbitMQ)
│       │   ├── services/                   # Логика взаимодействия с внешними сервисами
│       │   │   ├── __init__.py             
│       │   │   └── s3_service.py           # Логика работы с Minio/S3
│       │   └── worker_logic/               # Логика worker'а 
│       │       ├── __init__.py             
│       │       ├── connections.py          # Функции подключения 
│       │       ├── content_generation.py   # Функции генерации контента
│       │       ├── task_handlers.py        # Обработчики сообщений
│       │       └── worker_main.py          # Основной цикл worker'а
│       ├── tests/                         # Директория для тестов
│       │   ├── __init__.py                
│       │   ├── test_config.py             # Тесты для конфигурации
│       │   ├── test_routes_main.py        # Тесты для основных маршрутов
│       │   ├── test_routes_auth.py        # Тесты для маршрутов аутентификации
│       │   ├── test_utils_content.py      # Тесты для функций генерации контента
│       │   └── test_utils_task_helpers.py # Тесты для обработки userinfo из Redis
│       ├── backend.py                      # Точка входа для Flask-приложения
│       ├── worker.py                       # Точка входа для Worker'а
├── docs/                        # Документация проекта
└── README.md
</pre>
# Описание компонентов системы

## Общее описание

Quotation Book - это микросервисное приложение для генерации случайных цитат, изображений и PDF книг с аутентификацией через Keycloak OIDC.

## Компоненты системы

### Приложение состоит из следующих компонентов:

- **quotation-book-backend** - бэкенд на Python/Flask, реализующий REST API
- **quotation-book-frontend** - фронтенд(Nginx)
- **quotation-book-postgres** - база данных PostgreSQL
- **quotation-book-redis** - сервер Redis для кэширования.
- **quotation-book-rabbitmq** - брокер сообщений RabbitMQ
- **quotation-book-keycloak** - сервис аутентификации Keycloak
- **quotation-book-pgadmin** - инструмент администрирования PostgreSQL
- **quotation-book-backend-worker** - фоновый обработчик задач на Python(Worker)

##  Подробное описание компонентов

###  **quotation-book-backend (Flask API)**
- **Порт**: 5000
- **Язык**: Python 3.11
- **Функции**:
  - REST API endpoints
  - Аутентификация через Keycloak OIDC
  - Кэширование в Redis
  - Постановка задач в брокер RabbitMQ
  - Генерация HTML страниц
  - Работа с PostgreSQL и Minio S3
  - Использование Session management через Flask cookies 

### **quotation-book-frontend (Nginx)**
- **Порт**: 8443 (HTTPS)
- **Функции**:
  - Reverse proxy для backend
  - Отдача статики, расположенной на NFS
  - OIDC protection через обязательный `auth_request`

### **quotation-book-postgres (PostgreSQL)**
- **Порт**: 5432
- **Функции**:
  - Хранение цитат в таблице `quotes`
  - Хранение пользовательских данных (БД - Keycloak)

### **quotation-book-redis (Redis)**
- **Порт**: 6379
- **Функции**:
  - Кэширование userinfo от Keycloak (30 секунд)
  - Кэширование цитат из PostgreSQL (10 секунд)
  - Отслеживание статуса задач генерации PDF книг

### **quotation-book-rabbitmq (RabbitMQ)**
- **Порт AMQP**: 5672
- **Порт Management(UI)**: 15672
- **Функции**:
  - Message queuing для асинхронных задач 
  - Task distribution между worker'ами (если воркеро в > 1)
  - Persistent queues для надежности
  - Priority queues для важных задач (в нашем случае для генерации объёмных книг)

### **quotation-book-keycloak (Keycloak)**
- **Порт HTTP**: 8081
- **Порт HTTPS**: 1443
- **Функции**:
  - OpenID Connect провайдер
  - Управление пользователями

### **quotation-book-pgadmin (pgAdmin)**
- **Порт**: 5050
- **Функции**:
  - Администрирование PostgreSQL через UI

### **quotation-book-backend-worker (Background Worker)**
- **Язык**: Python 3.11
- **Функции**:
  - Асинхронная обработка задач из RabbitMQ
  - Генерация PDF книг и PNG изображений
  - Загрузка файлов в Minio S3 и NFS
  - Обновление статуса задач в Redis

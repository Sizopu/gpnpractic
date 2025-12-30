## Быстрый старт

### Локальная сборка через Docker Compose:
**При необходимости сверить переменные указанные в .env файле.**

### Требования:
- 2+ CPU
- 4GB+ RAM
- 2GB+ свободного места

### Выполнить:
```bash
# Клонирование репозитория
git clone <repository-url> . 
cd devops-tools-sandbox/ci/local

# Запуск всех сервисов
docker-compose up -d

# Проверка статуса сервисов
docker-compose ps

# Остановка сервисов
docker-compose down

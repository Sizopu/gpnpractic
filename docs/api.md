# API Endpoints

## Аутентификация

### `GET /auth/login`
**Описание**: Перенаправление на страницу аутентификации Keycloak

**Аутентификация**: Не ребуется

**Response**: 302 Redirect на Keycloak

### `GET /auth/callback`
**Описание**: Обработка callback от Keycloak после аутентификации

**Аутентификация**: Нет (обрабатывается на стороне Keycloak)

**Query Parameters**:
- `code` - authorization code от Keycloak
- `state` - состояние (опционально)

**Response**: 302 Redirect на защищенный маршрут

### `GET /auth/logout`
**Описание**: Выход из системы и завершение сессии Keycloak

**Аутентификация**: Требуется

**Response**: 302 Redirect на Keycloak logout


### `GET /auth/validate`
**Описание**: Валидация токена аутентификации (внутренний endpoint)

**Аутентификация**: Требуется

**Headers**:
- `Authorization: Bearer <token>`
**Response**: 
- 200 OK + `X-Forwarded-User` header
- 401 Unauthorized

## Цитаты

### `GET /jason`

**Описание**: Получение случайной цитаты с кнопками навигации

**Аутентификация**: Требуется

**Response**: HTML страница с цитатой

### `GET /`
**Описание**: Главная страница (редирект на /jason)

**Аутентификация**: Требуется

**Response**: 302 Redirect на /jason

## Галерея изображений

### `GET /gallery`

**Описание**: Отображение галереи сгенерированных изображений

**Аутентификация**: Требуется

**Response**: HTML страница галереи

### `GET /generate-images-asyncs`
**Описание**: Генерация новых случайных изображений через брокер RabbitMQ

**Аутентификация**: Требуется

**Response**: JSON статус генерации
```json
{
  "status": "queued",
  "message": "Поставлено в очередь 4 задачи генерации изображений",
  "tasks": ["task-id-1", "task-id-2", "task-id-3", "task-id-4"]
}
```

## Библиотека книг

### `GET /library`

**Описание**: Отображение библиотеки сгенерированных книг

**Аутентификация**: Требуется

**Response**: HTML страница библиотеки

### `GET /library/generate-async`

**Описание**: Генерация новых случайных книг через RabbitMQ

**Аутентификация**: Требуется

**Response**:  JSON статус постановки в очередь

```json
{
  "status": "queued",
  "message": "Поставлено в очередь 3 задачи генерации книг",
  "tasks": ["task-id-1", "task-id-2", "task-id-3"]
}
```

### `GET /library/generate-large-books`

**Описание**:  Генерация новых объёмных книг через RabbitMQ

**Аутентификация**: Требуется

**Response**:  JSON статус постановки в очередь

```json
{
  "status": "queued",
  "message": "Поставлено в очередь 5 задач генерации больших книг",
  "tasks": ["large-task-id-1", "large-task-id-2", "..."]
}
```

### `GET /library/view/<filename>`

**Описание**: Отображение библиотеки сгенерированных книг

**Аутентификация**: Требуется

**Response**: HTML страница с содержимым книги

### `GET /library/download/<filename>`

**Описание**: Скачивание книги

**Аутентификация**: Требуется

**Response**: PDF файл книги


### `GET /library/tasks/status`

**Описание**: Получение статуса задач генерации (для мониторинга прогресса)

**Аутентификация**: Требуется

**Response**: JSON статус задач

```json
{
  "status": "success",
  "active_tasks": [{"task_id": "task-1", "progress": 50}],
  "completed_tasks": [{"task_id": "task-2", "progress": 100}],
  "failed_tasks": [{"task_id": "task-3", "progress": 0}]
}
```

## Служебные endpoints

### `GET /check`

**Описание**: Проверка состояния сервиса (health check)

**Аутентификация**: Не требуется

**Response**:  JSON статус

### `GET /refresh-static`

**Описание**: Обновление статических файлов

**Аутентификация**: Требуется

**Response**:  JSON статус

```json
{"status": "success", "message": "Статические файлы обновлены"}
```

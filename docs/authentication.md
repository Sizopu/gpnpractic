# Аутентификация через Keycloak OIDC

## Обзор системы аутентификации

Quotation Book использует **OpenID Connect (OIDC)** аутентификацию через **Keycloak** для защиты всех маршрутов приложения.

## Конфигурация Keycloak для приложения Quotation-Book:
* При инициализации Keycloak импортирует файл `realm.json` с настройками для:
  * realm - `quotation-book`
  * client - `quotation-book-client`
  * user - `gpn-user`. Пароль предварительно захеширован с помощью PBKDF2-SHA256 + соль (указан в файле ci/local/.env)

## Поток аутентификации
**Взят пример локального развёртывания (localhost):**

### 1. **Первоначальный запрос пользователя:**
<pre>
Пользователь → https://localhost:8443/ 
     ↓
Nginx → auth_request /auth/check
     ↓
Flask Backend → проверяет session cookie
     ↓
В случае если в cookies браузра нет токена, то Flask Backend → 401 Unauthorized
     ↓
Nginx → редирект на /auth/login
     ↓
Flask Backend → редирект на Keycloak
</pre>

### 2. **Аутентификация через Keycloak:**
<pre>
Keycloak → форма логина для пользователя
     ↓
Пользователь → вводит учетные данные (логин/пароль)
     ↓
Keycloak → проверяет учетные данные в БД Keycloak, созданной в Postgres.
     ↓
Keycloak → валидирует пользователя
     ↓
Keycloak → если валидация успешна → генерирует временный код авторизации
     ↓
Keycloak → редирект на /auth/callback с кодом

</pre>

### 3. **Обработка callback:**
<pre>
Flask Backend → получает временный код из параметров URL
     ↓
Flask Backend → обменивает code на access_token и id_token
     ↓
Keycloak → проверяет код и выдает токены если код валиден
     ↓
Flask Backend → сохраняет токены в session cookies
     ↓
Flask Backend → редирект на защищенный маршрут (по умолч.: /jason)
</pre>

### 4. Последующие запросы с аутентификацией:
<pre>
Пользователь → любой защищенный маршрут (например /jason, /gallery, /library)
     ↓
Nginx → auth_request /auth/check (внутренний запрос)
     ↓
Flask Backend → /auth/validate → проверяет access_token
     ↓
Flask Backend → сначала проверяет кэш Redis на наличие ueserinfo
     ↓
Если нет в кэше → делает запрос к Keycloak /userinfo endpoint
     ↓
Keycloak → проверяет access_token (валидность, срок действия, подпись)
     ↓
Keycloak → если токен валиден → возвращает информацию о пользователе
     ↓
Flask Backend → кэширует userinfo в Redis (по умолчанию на 30 секунд для тестирования)
     ↓
Flask Backend → возвращает 200 OK с заголовком X-Forwarded-User
     ↓
Nginx → проксирует оригинальный запрос пользователя
</pre>

## Схема аутентификации пользователя:
<pre>
┌─────────────────┐    HTTPS   ┌──────────────┐    HTTP    ┌──────────────────┐
│   Пользователь  │───────────►│    Nginx     │───────────►│  Flask Backend   │
└─────────────────┘            └──────┬───────┘            └─────────┬────────┘
                                      │                              │
                               auth_request /auth/check       /auth/validate
                                      │                              │
                               ┌──────▼──────┐              ┌────────▼────────┐
                               │             │              │                 │
                               │   200/401   │◄─────────────┤  Проверка токена│
                               │             │              │                 │
                               └──────┬──────┘              └─────────────────┘
                                      │
                            Если 200: proxy_pass
                            Если 401: error_page 302
                                      │
                               ┌──────▼──────┐
                               │             │
                               │Пользователю │
                               │             │
                               └─────────────┘

</pre>

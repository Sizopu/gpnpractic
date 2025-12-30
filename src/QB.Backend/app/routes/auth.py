"""Маршруты для аутентификации через Keycloak."""
from flask import Blueprint, request, redirect, session, url_for, jsonify
import requests
from urllib.parse import urlencode
from ..config import Config
# Импортируем функции из extensions и utils
from ..extensions import get_redis_connection
from ..utils.task_helpers import cache_userinfo, get_cached_userinfo, invalidate_userinfo_cache
import logging

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Маршрут для перенаправления на страницу аутентификации Keycloak
@bp.route('/login')
def auth_login():
    """Перенаправление пользователя на страницу входа Keycloak."""
    # Очищаем сессию перед новым входом
    session.clear()
    # Формируем URL для аутентификации в Keycloak
    keycloak_auth_url = f"https://{Config.KEYCLOAK_EXTERNAL_HOST}:{Config.KEYCLOAK_EXTERNAL_PORT}/keycloak/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/auth"
    redirect_uri = Config.KEYCLOAK_REDIRECT_URI
    params = {
        'client_id': Config.KEYCLOAK_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'openid profile email'
    }
    auth_url = f"{keycloak_auth_url}?{urlencode(params)}"
    return redirect(auth_url)

# Маршрут для обработки callback от Keycloak
# отвечает за первичное получение пары токенов.
# Обменивает одноразовый authorization code на accesss_token и refresh_token
@bp.route('/callback')
def auth_callback():
    """Callback-эндпоинт для обработки ответа от Keycloak после аутентификации."""
    # Получаем код авторизации из параметров запроса
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        logging.getLogger(__name__).error(f"Keycloak вернул ошибку: {error}")
        return f"Аутентификация не удалась: {error}", 400

    if not code:
        logging.getLogger(__name__).error("В callback не передан код авторизации")
        return "Код авторизации не предоставлен", 400

    # Формируем URL для обмена кода на токен
    token_url = f"https://{Config.KEYCLOAK_HOST}:{Config.KEYCLOAK_PORT}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/token"

    # Настройка SSL-верификации для запроса к Keycloak
    verify_ssl = True
    if Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false" and Config.CA_CERTIFICATE != "False":
        verify_ssl = Config.CA_CERTIFICATE
    elif Config.CA_CERTIFICATE and (Config.CA_CERTIFICATE.lower() == "false" or Config.CA_CERTIFICATE == "False"):
        verify_ssl = False

    # Данные для запроса токена
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': Config.KEYCLOAK_CLIENT_ID,
        'client_secret': Config.KEYCLOAK_CLIENT_SECRET,
        'code': code,
        'redirect_uri': Config.KEYCLOAK_REDIRECT_URI
    }
    try:
        logging.getLogger(__name__).info(f"Попытка обмена кода на токен по адресу: {token_url}")
        response = requests.post(token_url, data=token_data, verify=verify_ssl)
        logging.getLogger(__name__).info(f"Статус ответа токена: {response.status_code}")

        if response.status_code != 200:
            logging.getLogger(__name__).error(f"Не удалось получить токен: {response.status_code}")
            return f"Не удалось получить токен доступа: {response.status_code}", response.status_code

        token_info = response.json()

        if 'access_token' in token_info:
            # Сохраняем access_token в сессии
            session['access_token'] = token_info['access_token']
            # Сохраняем refresh_token, если он предоставлен
            if 'refresh_token' in token_info:
                session['refresh_token'] = token_info['refresh_token']
                logging.getLogger(__name__).info("Refresh токен успешно получен и сохранен в сессии")
            else:
                logging.getLogger(__name__).warning("Refresh токен не предсоставился Keycloak.")
            # Делаем сессию постоянной
            session.permanent = True
            logging.getLogger(__name__).info("Токен доступа успешно получен и сохранен в сессии")
            # Перенаправляем на главную страницу
            return redirect(url_for('main.jason'))  # Используем url_for для blueprint'а
        else:
            logging.getLogger(__name__).error("В ответе отсутствует access_token")
            return "Не удалось получить токен доступа", 400

    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка обмена кода на токен: {e}")
        return "Ошибка во время аутентификации", 500

# Маршрут для валидации токена аутентификации и в случаего чего обновляет токен
# проверяет, авторизован ли текущий пользователь.
@bp.route('/validate')
def auth_validate():
    """Валидация токена доступа (используется Nginx auth_request)."""
    # Получаем токен из сессии
    access_token = session.get('access_token')
    refresh_token = session.get('refresh_token')

    if not access_token:
        logging.getLogger(__name__).warning("В сессии отсутствует токен доступа для валидации")
        return "Unauthorized", 401

    # Сначала проверяем кэш Redis
    cached_userinfo = get_cached_userinfo(access_token)
    if cached_userinfo:
        logging.getLogger(__name__).info("Userinfo получен из кэша")
        return "", 200, {
            'X-Forwarded-User': cached_userinfo.get('preferred_username', 'unknown')
        }

    # Если нет в кэше, проверяем токен через Keycloak
    userinfo_url = f"https://{Config.KEYCLOAK_HOST}:{Config.KEYCLOAK_PORT}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"

    # Настройка SSL-верификации
    verify_ssl = True
    if Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false" and Config.CA_CERTIFICATE != "False":
        verify_ssl = Config.CA_CERTIFICATE
    elif Config.CA_CERTIFICATE and (Config.CA_CERTIFICATE.lower() == "false" or Config.CA_CERTIFICATE == "False"):
        verify_ssl = False

    try:
        response = requests.get(
            userinfo_url,
            headers={'Authorization': f'Bearer {access_token}'},
            verify=verify_ssl
        )

        if response.status_code == 200:
            # Получаем информацию о пользователе
            user_info = response.json()
            # Кэшируем информацию о пользователе в Redis
            cache_userinfo(access_token, user_info)
            return "", 200, {
                'X-Forwarded-User': user_info.get('preferred_username', 'unknown')
            }

        elif response.status_code == 401:
            # Access token истёк, пробуем обновить его с помощью refresh_token
            logging.getLogger(__name__).info("Access token истёк, пробуем обновить...")
            if refresh_token:
                token_refresh_url = f"https://{Config.KEYCLOAK_HOST}:{Config.KEYCLOAK_PORT}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/token"
                payload = {
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': Config.KEYCLOAK_CLIENT_ID,
                }
                # Добавляем client_secret, если он задан
                if Config.KEYCLOAK_CLIENT_SECRET:
                    payload['client_secret'] = Config.KEYCLOAK_CLIENT_SECRET

                try:
                    refresh_response = requests.post(token_refresh_url, data=payload, verify=verify_ssl)
                    if refresh_response.status_code == 200:
                        tokens = refresh_response.json()
                        new_access_token = tokens.get('access_token')
                        new_refresh_token = tokens.get('refresh_token')
                        # Сохраняем новые токены в сессии
                        session['access_token'] = new_access_token
                        if new_refresh_token:
                            session['refresh_token'] = new_refresh_token
                        logging.getLogger(__name__).info("Токены успешно обновлены")
                        # Повторяем проверку userinfo с новым токеном
                        retry_response = requests.get(userinfo_url,
                                                      headers={'Authorization': f'Bearer {new_access_token}'},
                                                      verify=verify_ssl)
                        if retry_response.status_code == 200:
                            user_info = retry_response.json()
                            cache_userinfo(new_access_token, user_info)
                            return "", 200, {'X-Forwarded-User': user_info.get('preferred_username', 'unknown')}
                        else:
                            logging.getLogger(__name__).warning(
                                f"Проверка нового токена не удалась: {retry_response.status_code}")
                    else:
                        logging.getLogger(__name__).warning(
                            f"Не удалось обновить токен: {refresh_response.status_code}, {refresh_response.text}")
                except Exception as refresh_error:
                    logging.getLogger(__name__).error(f"Ошибка при попытке обновить токен: {refresh_error}")
            # Если refresh_token отсутствует или обновление не удалось, очищаем сессию
            logging.getLogger(__name__).warning(
                "Не удалось обновить токен или refresh_token отсутствует, очищаем сессию")
            session.pop('access_token', None)
            session.pop('refresh_token', None)
            return "Unauthorized", 401
        else:
            # Другая ошибка валидации токена
            logging.getLogger(__name__).warning(f"Валидация токена не удалась со статусом {response.status_code}")
            session.pop('access_token', None)
            return "Unauthorized", 401

    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка валидации токена: {e}")
        return "Unauthorized", 401
@bp.route('/logout')
def auth_logout():
    """Выход пользователя из системы."""
    # Получаем токен доступа из сессии
    access_token = session.get('access_token')
    # Очищаем сессию
    session.clear()
    # Удаляем информацию о пользователе из кэша Redis
    if access_token:
        invalidate_userinfo_cache(access_token)
    # Формируем URL для выхода из Keycloak
    keycloak_logout_url = f"https://{Config.KEYCLOAK_EXTERNAL_HOST}:{Config.KEYCLOAK_EXTERNAL_PORT}/keycloak/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    logout_redirect_url = f"{keycloak_logout_url}?client_id={Config.KEYCLOAK_CLIENT_ID}&post_logout_redirect_uri=https://{Config.KEYCLOAK_EXTERNAL_HOST}:{Config.KEYCLOAK_EXTERNAL_PORT}"
    logging.getLogger(__name__).info("Пользователь разлогинен, делаю редирект на кейклок")
    return redirect(logout_redirect_url)
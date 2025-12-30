"""Вспомогательные функции для работы с задачами (RabbitMQ, Redis)."""
import pika
import ssl
import json
import hashlib
import time
from ..config import Config
from ..extensions import get_redis_connection
import logging

logger = logging.getLogger(__name__)
def get_rabbitmq_connection():
    """Получение подключения к RabbitMQ"""
    try:
        # Создаем учетные данные для подключения
        credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)

        # Настраиваем SSL-подключение, если сертификат предоставлен
        if Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false":
            # Создаем SSL-контекст
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_verify_locations(Config.CA_CERTIFICATE)
            # Создаем SSL-опции для подключения
            ssl_options = pika.SSLOptions(ssl_context, Config.RABBITMQ_HOST)

            # Формируем параметры подключения с SSL
            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                virtual_host=Config.RABBITMQ_VHOST,
                credentials=credentials,
                ssl_options=ssl_options,
                heartbeat=600,  # Таймаут heartbeat в секундах
                blocked_connection_timeout=300,  # Таймаут заблокированного соединения
                socket_timeout=10  # Таймаут сокета
            )
        else:
            # Формируем параметры подключения без SSL
            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                virtual_host=Config.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                socket_timeout=10
            )

        # Устанавливаем соединение
        connection = pika.BlockingConnection(parameters)
        return connection
    except Exception as e:
        logger.error(f"Ошибка подключения к RabbitMQ: {e}")
        return None
def cache_userinfo(access_token, user_info, ttl=Config.USERINFO_CACHE_TTL):
    """Кэширует информацию о пользователе в Redis"""
    try:
        # Получаем подключение к Redis
        redis_conn = get_redis_connection()
        # Хешируем токен доступа для использования в качестве ключа кэша
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        cache_key = f"userinfo:{token_hash}"
        # Сохраняем информацию о пользователе в Redis с TTL
        redis_conn.setex(cache_key, ttl, json.dumps(user_info))
        logger.info(f"Userinfo закэширован в Redis с ключом {cache_key}")
        return True
    except Exception as e:
        logger.error(f"Ошибка кэширования userinfo в Redis: {e}")
        return False
def get_cached_userinfo(access_token):
    """Получает информацию о пользователе из Redis кэша"""
    try:
        redis_conn = get_redis_connection()
        # Создаем ключ на основе хэша токена
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        cache_key = f"userinfo:{token_hash}"

        # Получаем userinfo из Redis
        cached_data = redis_conn.get(cache_key)
        if cached_data:
            user_info = json.loads(cached_data)
            logger.info(f"Userinfo получен из Redis кэша по ключу {cache_key}")
            return user_info
        return None
    except Exception as e:
        logger.error(f"Ошибка получения userinfo из Redis кэша: {e}")
        return None
def invalidate_userinfo_cache(access_token):
    """Удаляет информацию о пользователе из Redis кэша"""
    try:
        # Получаем подключение к Redis
        redis_conn = get_redis_connection()
        # Хешируем токен доступа для поиска в кэше
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        cache_key = f"userinfo:{token_hash}"
        # Удаляем ключ из Redis
        redis_conn.delete(cache_key)
        logger.info(f"Userinfo удален из Redis кэша по ключу {cache_key}")
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления userinfo из Redis кэша: {e}")
        return False
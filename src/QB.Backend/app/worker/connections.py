"""Модуль для работы с подключениями к внешним сервисам."""
import redis
import boto3
import pika
import ssl
from botocore.exceptions import ClientError
from ..config import Config
import logging

logger = logging.getLogger(__name__)
def get_redis_connection():
    """Получение подключения к Redis для отслеживания статуса задач"""
    try:
        if Config.REDIS_SSL and Config.CA_CERTIFICATE != "false":
            # Подключение к Redis через SSL/TLS
            redis_conn = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                ssl_cert_reqs=None,
                ssl=True,
                ssl_ca_certs=Config.CA_CERTIFICATE
            )
        else:
            # Подключение без SSL
            redis_conn = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
        redis_conn.ping()
        return redis_conn
    except Exception as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        return None
def get_s3_client():
    """Получение клиента S3"""
    try:
        # Определяем, использовать ли SSL
        use_ssl = Config.MINIO_ENDPOINT.startswith('https')

        if use_ssl and Config.MINIO_SSL_VERIFY and Config.CA_CERTIFICATE != "false": # Исправлено: проверка на "false"
            # Используем стандартную проверку SSL с указанным CA
            client = boto3.client(
                's3',
                endpoint_url=Config.MINIO_ENDPOINT,
                aws_access_key_id=Config.MINIO_ACCESS_KEY,
                aws_secret_access_key=Config.MINIO_SECRET_KEY,
                verify=Config.CA_CERTIFICATE
            )
        else:
            # Стандартное подключение
            client = boto3.client(
                's3',
                endpoint_url=Config.MINIO_ENDPOINT,
                aws_access_key_id=Config.MINIO_ACCESS_KEY,
                aws_secret_access_key=Config.MINIO_SECRET_KEY,
            )

        return client
    except Exception as e:
        logger.error(f"Ошибка создания S3 клиента: {e}")
        return None
def get_rabbitmq_connection():
    """Получение подключения к RabbitMQ"""
    try:
        logger.info("[Worker] Попытка подключения к RabbitMQ...")
        credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)

        if Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false":
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_verify_locations(Config.CA_CERTIFICATE)
            ssl_options = pika.SSLOptions(ssl_context, Config.RABBITMQ_HOST)

            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                virtual_host=Config.RABBITMQ_VHOST,
                credentials=credentials,
                ssl_options=ssl_options,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=5,
                retry_delay=5
            )
        else:
             parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                virtual_host=Config.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=5,
                retry_delay=5
            )
        connection = pika.BlockingConnection(parameters)
        logger.info("[Worker] Подключение к RabbitMQ установлено.")
        return connection
    except Exception as e:
        logger.error(f"[Worker] Ошибка подключения к RabbitMQ: {e}")
        return None
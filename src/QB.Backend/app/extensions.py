"""Инициализация внешних сервисов (база данных, Redis, S3)."""
import psycopg2
import redis
import boto3
from botocore.exceptions import ClientError
from .config import Config
import logging

logger = logging.getLogger(__name__)

# Глобальные клиенты/пулы
db_pool = None
redis_client = None
s3_client = None

def get_db_connection():
    """Получение соединения с PostgreSQL."""
    conn_params = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'database': Config.DB_NAME,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD
    }
    if Config.POSTGRES_SSL:
        conn_params['sslmode'] = 'verify-full'
        if Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false":
            conn_params['sslrootcert'] = Config.CA_CERTIFICATE
        logger.info(f"Подключение к PostgreSQL с параметами SSL...")
    conn = psycopg2.connect(**conn_params)
    logger.info(f"Используется SSL: {conn.get_dsn_parameters().get('sslmode', 'none')}")
    return conn

def get_redis_connection():
    """Получение соединения с Redis."""
    try:
        # Проверка на использование SSL при подключение к Redis.
        if Config.REDIS_SSL and Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false":
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
        raise

def get_s3_client():
    """Получение клиента S3 (Minio)."""
    try:
        use_ssl = Config.MINIO_ENDPOINT.startswith('https')
        # Проверка на использование SSL при подключение к S3.
        if use_ssl and Config.MINIO_SSL_VERIFY and Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false":
            client = boto3.client(
                's3',
                endpoint_url=Config.MINIO_ENDPOINT,
                aws_access_key_id=Config.MINIO_ACCESS_KEY,
                aws_secret_access_key=Config.MINIO_SECRET_KEY,
                verify=Config.CA_CERTIFICATE
            )
        else:
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

def init_extensions(app):
    """Инициализация внешних сервисов."""
    global db_pool, redis_client, s3_client
    try:
        redis_client = get_redis_connection()
        s3_client = get_s3_client()
        # Проверка подключения к Redis
        if redis_client:
             redis_client.ping()
             logger.info("Подключение к Redis успешно установлено")
        # Проверка подключения к S3
        if s3_client:
             logger.info("Клиент S3 (Minio) успешно инициализирован.")
    except Exception as e:
         logger.error(f"Ошибка инициализации расширений: {e}")
         raise
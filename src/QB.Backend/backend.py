"""Точка входа для запуска Flask-приложения."""
import os
import sys
import ssl
import logging
import threading
import time
import redis # Импортируем redis для тестирования
# Импортируем функции и классы из других модулей
from app import create_app
from app.config import Config
# from app.extensions import redis_client # Не импортируем напрямую, так как он инициализируется позже
from app.utils.static_files import init_static_dir
from app.services.s3_service import init_minio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Функция для тестирования подключения к Redis при запуске
def test_redis_connection():
    """Функция для тестирования подключения к Redis в отдельном потоке"""
    time.sleep(5) # Небольшая задержка перед тестированием
    logger.info("=== Тестирование подключения к Redis ===")
    try:
        if Config.REDIS_SSL and Config.CA_CERTIFICATE and Config.CA_CERTIFICATE.lower() != "false":
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
        logger.info(f"Попытка подключения к Redis по адресу {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        response = redis_conn.ping()
        logger.info(f"Ответ Redis на ping: {response}")
        logger.info("Тестирование подключения к Redis успешно завершено")
    except Exception as e:
        logger.error(f"Ошибка тестирования подключения к Redis: {e}")
    logger.info("=== Завершение тестирования подключения к Redis ===")

def collect_static():
    """Функция для генерации статических файлов"""
    print("Запуск генерации статических файлов...")
    init_static_dir()
    print("Статические файлы успешно сгенерированы")

def main():
    """Главная функция для запуска приложения или выполнения команд."""
    # Обработка командной строки для генерации статики и иницализации Minio с созданием бакета и пролив контента.
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'collectstatic':
            collect_static()
            sys.exit(0)
        elif command == 'collectminio':
            print("Инициализация Minio...")
            init_minio()
            print("Minio инициализирован")
            sys.exit(0)

    # Запускаем тестирование Redis в отдельном потоке
    redis_test_thread = threading.Thread(target=test_redis_connection, daemon=True)
    redis_test_thread.start()

    # Создаем Flask-приложение
    app = create_app()

    # Запуск приложения
    if not Config.BACKEND_TLS:
        logger.info("Запуск Flask приложения на HTTP")
        app.run(host='0.0.0.0', port=Config.BACKEND_PORT, debug=True)
    else:
        # Проверяем наличие SSL-сертификатов
        if not os.path.exists(Config.BACKEND_SSL_CERT) or not os.path.exists(Config.BACKEND_SSL_KEY):
            logger.error(f"SSL certificate or key file not found: {Config.BACKEND_SSL_CERT}, {Config.BACKEND_SSL_KEY}")
            logger.info("Попытка запуска Flask-сервера с SSL mode. Отсутствуют сертификаты сервера")
            exit(1)
        else:
            # Создаем SSL-контекст и запускаем приложение
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(Config.BACKEND_SSL_CERT, Config.BACKEND_SSL_KEY)
            logger.info(f"Старт Flask-приложения на порту {Config.BACKEND_PORT} с SSL...")
            app.run(host='0.0.0.0', port=Config.BACKEND_PORT, ssl_context=context, debug=False)

if __name__ == '__main__':
    main()
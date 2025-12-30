import os

class Config:
    # Flask
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'quotation-book-secret-key')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'None')
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 5000))
    BACKEND_TLS = os.getenv("BACKEND_TLS", "True").lower() == "true"
    BACKEND_SSL_CERT = os.getenv("BACKEND_SSL_CERT", "/opt/app-root/etc/certificate.crt")
    BACKEND_SSL_KEY = os.getenv("BACKEND_SSL_KEY", "/opt/app-root/etc/private.key")
    STATIC_DIR = "/opt/app-root/src/static"

    # PostgreSQL
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    POSTGRES_SSL = os.getenv("POSTGRES_SSL", "False").lower() == "true"
    POSTGRES_CACHE_TTL = int(os.getenv("POSTGRES_CACHE_TTL", 10))

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "quotation-book-redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASS")
    REDIS_SSL = os.getenv("REDIS_SSL", "False").lower() == "true"
    USERINFO_CACHE_TTL = int(os.getenv("USERINFO_CACHE_TTL", 20))

    CA_CERTIFICATE = os.getenv("CA_CERTIFICATE", "False")

    # Keycloak
    KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "quotation-book-keycloak")
    KEYCLOAK_PORT = os.getenv("KEYCLOAK_PORT", "1443")
    KEYCLOAK_EXTERNAL_HOST = os.getenv("KEYCLOAK_EXTERNAL_HOST", "localhost")
    KEYCLOAK_EXTERNAL_PORT = os.getenv("KEYCLOAK_EXTERNAL_PORT", "8443")
    KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "quotation-book-client")
    KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "QuotationBookSecret123!")
    KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "quotation-book")
    KEYCLOAK_REDIRECT_URI = os.getenv("KEYCLOAK_REDIRECT_URI", "https://localhost:8443/auth/callback")

    # Minio S3 (общие для backend и worker)
    MINIO_ENDPOINT = f"{os.getenv('MINIO_URL', 'http://quotation-book-minio')}:{os.getenv('MINIO_PORT', '9000')}"
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "gpn-admin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "changeme")
    MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "library") # Проверь это значение
    MINIO_SSL_VERIFY = os.getenv("MINIO_SSL_VERIFY", "true").lower() == "true"

    # RabbitMQ (общие для backend и worker)
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "quotation-book-rabbitmq")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "gpn-admin")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "changeme")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

    # flask
    SERVER_NAME = f"{KEYCLOAK_EXTERNAL_HOST}:{KEYCLOAK_EXTERNAL_PORT}"
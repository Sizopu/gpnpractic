"""Логика работы с Minio S3."""
import boto3
from botocore.exceptions import ClientError
from ..extensions import get_s3_client
from ..utils.content_generation import create_random_pdf_book
from ..config import Config
import time
import logging

logger = logging.getLogger(__name__)
def list_books_from_s3():
    """Получение списка книг из S3"""
    try:
        # Органзовываем клиент S3
        s3_client = get_s3_client()
        if not s3_client:
            return []
        # Получаем список объектов в bucket'е
        response = s3_client.list_objects_v2(Bucket=Config.MINIO_BUCKET_NAME)
        books = []
        # Проверяем, есть ли объекты в ответе
        if 'Contents' in response:
            # Сортируем объекты по имени ключа
            sorted_objects = sorted([obj for obj in response['Contents'] if obj['Key'].endswith('.pdf')],
                                    key=lambda x: x['Key'])
            # Проходим по отсортированным объектам и формируем список книг
            for idx, obj in enumerate(sorted_objects, 1):
                try:
                    # Получаем метаданные объекта
                    head_response = s3_client.head_object(
                        Bucket=Config.MINIO_BUCKET_NAME,
                        Key=obj['Key']
                    )
                    metadata = head_response.get('Metadata', {})
                    # Добавляем информацию о книге в список
                    books.append({
                        'filename': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        # Используем метаданные или значения по умолчанию
                        'title': metadata.get('title', f'Сгенерированная книга {idx}'),
                        'author': metadata.get('author', 'Неизвестный автор'),
                        'description': metadata.get('description', 'Описание отсутствует')
                    })
                except Exception as e:
                    # Логируем ошибку получения метаданных, но продолжаем обработку
                    logger.error(f"Ошибка получения метаданных для {obj['Key']}: {e}")
                    # Добавляем книгу с дефолтными значениями
                    books.append({
                        'filename': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'title': f'Сгенерированная книга {idx}',
                        'author': 'GPN',
                        'description': 'Книга со случайным содержанием'
                    })
        return books
    except Exception as e:
        logger.error(f"Ошибка получения списка книг из S3: {e}")
        return []
def upload_random_books_to_minio():
    """Загрузка рандомных книг в Minio"""
    try:
        # Организовываем клиент S3
        s3_client = get_s3_client()
        if not s3_client:
            return False
        # Генерируем и загружаем 3 рандомных книги
        for i in range(1, 4):
            title = f"Generated Book {i}"
            author = "GPN"
            description = "Book with random content"
            filename = f"book_{i}_{int(time.time())}.pdf"
            # Создаем PDF книгу
            pdf_bytes = create_random_pdf_book(f"Сгенерированная книга {i}", "GPN")
            if not pdf_bytes:
                logger.error(f"Не удалось создать PDF для {filename}")
                continue
            # Загружаем книгу в Minio S3
            s3_client.put_object(
                Bucket=Config.MINIO_BUCKET_NAME,
                Key=filename,
                Body=pdf_bytes,
                ContentType='application/pdf',
                Metadata={
                    'title': title,
                    'author': author,
                    'description': description,
                    'generated': 'true',
                    'timestamp': str(int(time.time())),
                    'language': 'en',
                    'book_number': str(i)
                }
            )
            logger.info(f"Загружена рандомная книга: {filename}")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки рандомных книг в Minio: {e}")
        return False
def init_minio():
    """Инициализация Minio S3 bucket"""
    try:
        # клиент S3
        s3_client = get_s3_client()
        if not s3_client:
            return None
        # Проверяем существование bucket'а
        try:
            s3_client.head_bucket(Bucket=Config.MINIO_BUCKET_NAME)
            logger.info(f"Bucket {Config.MINIO_BUCKET_NAME} уже существует")
        except ClientError:
            # Создаем bucket если его нет
            s3_client.create_bucket(Bucket=Config.MINIO_BUCKET_NAME)
            logger.info(f"Создан bucket {Config.MINIO_BUCKET_NAME}")
        # Проверяем содержимое bucket'а и загружаем рандомные книги при необходимости
        try:
            response = s3_client.list_objects_v2(Bucket=Config.MINIO_BUCKET_NAME)
            if 'Contents' not in response or len(response['Contents']) == 0:
                upload_random_books_to_minio()
            else:
                logger.info("В bucket'е уже есть файлы, пропускаем генерацию")
        except Exception as e:
            logger.error(f"Ошибка проверки содержимого bucket'а: {e}")
            upload_random_books_to_minio()
        return s3_client
    except Exception as e:
        logger.error(f"Ошибка инициализации Minio: {e}")
        return None
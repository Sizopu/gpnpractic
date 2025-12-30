"""Модуль с обработчиками сообщений из очередей RabbitMQ."""
import json
import time
import uuid
import os
import random
from .content_generation import (
    create_random_pdf_book, generate_random_image,
    create_large_pdf_book, set_task_status
)
from .connections import get_s3_client
from ..config import Config
import logging

logger = logging.getLogger(__name__)

def process_book_generation(ch, method, properties, body):
    """Обработчик задачи генерации книг с искусственной задержкой"""
    try:
        task = json.loads(body.decode('utf-8'))
        task_id = task.get('task_id', str(uuid.uuid4()))
        user_id = task.get('user_id', 'unknown_user')
        count = task.get('count', 3)

        logger.info(
            f"[Worker] Начало обработки задачи генерации {count} книг: Task ID {task_id} для пользователя {user_id}")

        # Устанавливаем начальный статус задачи
        set_task_status(task_id, "started", f"Начало обработки задачи генерации {count} книг", 5)

        s3_client = get_s3_client()
        if not s3_client:
            logger.error("[Worker] Не удалось подключиться к S3 для генерации книг")
            set_task_status(task_id, "failed", "Сервис временно недоступен", 0)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        # Генерируем книги
        generated_books = []

        # Получаем существующие книги для определения следующего номера
        try:
            response = s3_client.list_objects_v2(Bucket=Config.MINIO_BUCKET_NAME)
            existing_books = [obj for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]
            next_number = len(existing_books) + 1
        except:
            next_number = 1

        for i in range(count):
            book_number = next_number + i
            title = f"Сгенерированная книга {book_number}"
            author = "GPN"
            description = "Книга со случайным содержанием"
            filename = f"book_{book_number}_{int(time.time())}_{i}.pdf"

            logger.info(f"[Worker] Генерация книги: {filename}")

            # Обновляем статус задачи
            progress = int((i / count) * 80) + 10
            set_task_status(task_id, "processing", f"Генерация книги {i + 1}/{count}", progress)

            # Добавляем искусственную задержку для каждой книги
            time.sleep(random.uniform(0.2, 0.5))  # 0.2-0.5 секунд задержки

            # Создаем PDF с заголовком и автором
            pdf_bytes = create_random_pdf_book(title, author)
            if not pdf_bytes:
                logger.error(f"[Worker] Не удалось создать PDF для {filename}")
                continue  # Продолжаем с другими книгами, даже если одна не удалась

            # Загружаем в Minio S3
            try:
                s3_client.put_object(
                    Bucket=Config.MINIO_BUCKET_NAME,
                    Key=filename,
                    Body=pdf_bytes,
                    ContentType='application/pdf',
                    Metadata={
                        'title': f"Generated Book {book_number}",  
                        'author': 'GPN', 
                        'description': 'Book with random English content',  
                        'generated': 'true',
                        'timestamp': str(int(time.time())),
                        'language': 'en',
                        'book_number': str(book_number) 
                    }
                )
                generated_books.append(filename)
                logger.info(f"[Worker] Книга {filename} успешно загружена в S3")
            except Exception as e:
                logger.error(f"[Worker] Ошибка загрузки книги {filename} в S3: {e}")
                # Не nack'аем сообщение из-за одной неудачной загрузки, продолжаем

        # Устанавливаем финальный статус задачи
        set_task_status(task_id, "completed", f"Сгенерировано {len(generated_books)} книг из {count}", 100)
        logger.info(f"[Worker] Задача генерации книг {task_id} завершена. Сгенерировано {len(generated_books)} книг.")

        # Acknowledge сообщения
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as je:
        logger.error(f"[Worker] Ошибка декодирования JSON из сообщения: {je}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"[Worker] Необработанная ошибка в process_book_generation: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
def process_large_book_generation(ch, method, properties, body):
    """Обработчик задачи генерации больших книг с искусственной задержкой"""
    try:
        task = json.loads(body.decode('utf-8'))
        task_id = task.get('task_id', str(uuid.uuid4()))
        user_id = task.get('user_id', 'unknown_user')
        book_number = task.get('book_number', 1)
        word_count = task.get('word_count', 5000)

        logger.info(
            f"[Worker] Начало обработки задачи генерации большой книги: Task ID {task_id} для пользователя {user_id}")

        # Устанавливаем начальный статус задачи
        set_task_status(task_id, "started", f"Начало обработки задачи генерации большой книги {book_number}", 5)

        s3_client = get_s3_client()
        if not s3_client:
            logger.error("[Worker] Не удалось подключиться к S3 для генерации большой книги")
            set_task_status(task_id, "failed", "Сервис временно недоступен", 0)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        # Генерируем название и автора книги
        title = f"Сгенерированная книга {book_number}"
        author = "GPN"
        description = "Книга со случайным содержанием "
        filename = f"large_book_{book_number}_{int(time.time())}.pdf"

        logger.info(f"[Worker] Генерация большой книги {book_number} с {word_count} словами")

        # Обновляем статус задачи
        set_task_status(task_id, "processing", f"Генерация большой книги {book_number} с {word_count} словами", 15)

        # Добавляем искусственную задержку перед началом генерации
        time.sleep(random.uniform(1.5, 2.5))  # 1.5-2.5 секунд задержки

        # Создаем большую PDF книгу с искусственной задержкой
        pdf_bytes = create_large_pdf_book(title, author, word_count, task_id)
        if not pdf_bytes:
            logger.error(f"[Worker] Не удалось создать большую PDF книгу {book_number}")
            set_task_status(task_id, "failed", f"Не удалось создать большую PDF книгу {book_number}", 0)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        # Обновляем статус задачи
        set_task_status(task_id, "processing", f"Загрузка книги {book_number} в S3", 95)

        # Добавляем искусственную задержку перед загрузкой
        time.sleep(random.uniform(0.3, 0.8))  # 0.3-0.8 секунд задержки

        # Загружаем в Minio S3
        try:
            s3_client.put_object(
                Bucket=Config.MINIO_BUCKET_NAME,
                Key=filename,
                Body=pdf_bytes,
                ContentType='application/pdf',
                Metadata={
                    'title': f"Generated Book {book_number}",  # Только ASCII
                    'author': 'GPN',  # Только ASCII
                    'description': 'Book with random English content',  # Только ASCII
                    'generated': 'true',
                    'timestamp': str(int(time.time())),
                    'language': 'en',
                    'book_number': str(book_number),  # Только ASCII
                    'word_count': str(word_count),  # Только ASCII
                    'user_id': user_id  # Только ASCII
                }
            )
            logger.info(f"[Worker] Большая книга {book_number} успешно загружена в S3: {filename}")
        except Exception as e:
            logger.error(f"[Worker] Ошибка загрузки большой книги {book_number} в S3: {e}")
            set_task_status(task_id, "failed", f"Ошибка загрузки книги {book_number} в S3: {str(e)}", 0)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        # Устанавливаем финальный статус задачи
        set_task_status(task_id, "completed", f"Большая книга {book_number} успешно сгенерирована и загружена", 100)
        logger.info(f"[Worker] Задача генерации большой книги {task_id} завершена.")

        # Acknowledge сообщения
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as je:
        logger.error(f"[Worker] Ошибка декодирования JSON из сообщения: {je}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"[Worker] Необработанная ошибка в process_large_book_generation: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def process_image_generation(ch, method, properties, body):
    """Обработчик задачи генерации изображений"""
    try:
        task = json.loads(body.decode('utf-8'))
        task_id = task.get('task_id', 'unknown')
        logger.info(
            f"[Worker] Начало обработки задачи генерации изображений: Task ID {task_id} для пользователя {task.get('user_id', 'unknown')}")

        # Устанавливаем начальный статус задачи
        set_task_status(task_id, "started", "Начало обработки задачи генерации изображений", 5)

        # Определяем директорию для статики
        if not os.path.exists(Config.STATIC_DIR):
            os.makedirs(Config.STATIC_DIR)
            logger.info(f"[Worker] Создана директория для статики: {Config.STATIC_DIR}")

        # Генерируем изображения
        generated_images = []
        count = task.get('count', 4)

        for i in range(count):
            # Обновляем статус задачи
            progress = int((i / count) * 90) + 10
            set_task_status(task_id, "processing", f"Генерация изображения {i + 1}/{count}", progress)

            # Генерируем уникальное имя файла
            timestamp_part = int(time.time() * 1000) % 100000  # Часть timestamp для уникальности
            filename = f"image_{timestamp_part}_{i}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(Config.STATIC_DIR, filename)

            logger.info(f"[Worker] Генерация изображения: {filename}")
            try:
                generate_random_image(filepath)
                generated_images.append(filename)
                logger.info(f"[Worker] Изображение {filename} успешно сгенерировано")
            except Exception as e:
                logger.error(f"[Worker] Ошибка генерации изображения {filename}: {e}")

        # Устанавливаем финальный статус задачи
        set_task_status(task_id, "completed", f"Сгенерировано {len(generated_images)} изображений", 100)
        logger.info(
            f"[Worker] Задача генерации изображений {task_id} завершена. Сгенерировано {len(generated_images)} изображений.")

        # Подтверждаем сообщения
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as je:
        logger.error(f"[Worker] Ошибка декодирования JSON из сообщения: {je}")
        # Nack без requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"[Worker] Необработанная ошибка в process_image_generation: {e}")
        # Nack с requeue=True для повторной попытки
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
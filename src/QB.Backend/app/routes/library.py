"""Маршруты для работы с электронной библиотекой."""
from flask import Blueprint, jsonify, redirect, session, Response, request, url_for
from ..services.s3_service import list_books_from_s3, \
    get_s3_client  # extract_text_from_pdf перемещен в content_generation
from ..utils.content_generation import extract_text_from_pdf  # Импортируем отсюда
from ..utils.static_files import generate_library_html
from ..utils.task_helpers import get_rabbitmq_connection
from ..config import Config
from ..extensions import get_redis_connection
import os
import random
import uuid
import json
import pika
import time
from botocore.exceptions import ClientError
import logging

bp = Blueprint('library', __name__, url_prefix='/library')


# Маршрут для библиотеки книг
@bp.route('/')
def library():
    """Отображение страницы электронной библиотеки."""
    access_token = session.get('access_token')
    if not access_token:
        logging.getLogger(__name__).warning("В сессии отсутствует токен доступа")
        return redirect(url_for('auth.auth_login'))  # Используем url_for для blueprint'а
    try:
        # Получаем список книг из S3
        books = list_books_from_s3()
        # Генерируем HTML страницы библиотеки
        html_content = generate_library_html(books)
        if html_content:
            return html_content
        else:
            return "<h1>Ошибка загрузки библиотеки</h1>", 500
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка отображения библиотеки: {e}")
        return "<h1>Ошибка загрузки библиотеки</h1>", 500

# Маршрут для просмотра содержимого книги
@bp.route('/view/<filename>')
def view_book(filename):
    """Просмотр содержимого книги."""
    access_token = session.get('access_token')
    if not access_token:
        logging.getLogger(__name__).warning("В сессии отсутствует токен доступа")
        return redirect(url_for('auth.auth_login'))  # Используем url_for для blueprint'а
    try:
        # Получаем клиент S3
        s3_client = get_s3_client()  # Импортируем из services
        if not s3_client:
            return "<h1>Сервис временно недоступен</h1>", 500

        # Получаем метаданные файла (для отображения заголовка/автора)
        try:
            head_response = s3_client.head_object(Bucket=Config.MINIO_BUCKET_NAME, Key=filename)
            metadata = head_response.get('Metadata', {})
        except ClientError:
            # Если файл не найден
            return "<h1>Файл не найден</h1>", 404

        # Получаем содержимое файла из S3
        response = s3_client.get_object(Bucket=Config.MINIO_BUCKET_NAME, Key=filename)
        pdf_bytes = response['Body'].read()

        # Извлекаем текст из PDF
        book_text = extract_text_from_pdf(pdf_bytes)  # Импортируем из utils.content_generation

        # Генерируем HTML для просмотра книги
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Просмотр книги - {metadata.get('title', filename)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            color: white;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .title {{
            font-size: 2em;
            margin-bottom: 10px;
            color: #fff;
        }}
        .author {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #e0e0e0;
        }}
        .actions {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .back-button, .download-button {{
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            border: 1px solid rgba(255, 255, 255, 0.3);
            font-weight: bold;
        }}
        .back-button:hover, .download-button:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }}
        .content {{
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            line-height: 1.6;
            font-size: 1.1em;
            white-space: pre-wrap;
            text-align: justify;
        }}
        .no-content {{
            text-align: center;
            padding: 50px;
            color: #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🕮 {metadata.get('title', filename)}</div>
            <div class="author">🖋 Автор: {metadata.get('author', 'Неизвестный автор')}</div>
            <div class="actions">
                <a href="/library" class="back-button">← Назад к библиотеке</a>
                <a href="/library/download/{filename}" class="download-button" target="_blank">⬇ Скачать PDF</a>
            </div>
        </div>
        <div class="content">
            {book_text if book_text else '<div class="no-content">Содержимое книги не найдено</div>'}
        </div>
    </div>
</body>
</html>'''
        return html_content
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка просмотра книги {filename}: {e}")
        return "<h1>Ошибка при просмотре книги</h1>", 500


# Маршрут для скачивания книг
@bp.route('/download/<filename>')
def download_book(filename):
    """Скачивание книги в формате PDF."""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401
    try:
        # Получаем клиент S3
        s3_client = get_s3_client()  # Импортируем из services
        if not s3_client:
            return jsonify({"error": "Сервис временно недоступен"}), 500

        # Проверяем существование файла
        try:
            head_response = s3_client.head_object(Bucket=Config.MINIO_BUCKET_NAME, Key=filename)
        except ClientError:
            # Если файл не найден
            return jsonify({"error": "Файл не найден"}), 404

        # Получаем содержимое файла из S3
        response = s3_client.get_object(Bucket=Config.MINIO_BUCKET_NAME, Key=filename)
        file_content = response['Body'].read()

        # Возвращаем файл как ответ
        return Response(
            file_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(file_content))
            }
        )
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка скачивания книги {filename}: {e}")
        return jsonify({"error": "Ошибка при скачивании файла"}), 500

# Маршрут для генерации новых книг на стороне backend без использования брокера Rabbitmq
# т.е. без использование worker'a
@bp.route('/generate-new-books')
def generate_new_books():
    """Синхронная генерация новых книг (для тестирования)."""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401
    try:
        # Получаем клиент S3
        s3_client = get_s3_client()  # Импортируем из services
        if not s3_client:
            return jsonify({"error": "Сервис временно недоступен"}), 500

        new_books = []
        # Получаем список существующих книг для определения следующего номера
        try:
            response = s3_client.list_objects_v2(Bucket=Config.MINIO_BUCKET_NAME)
            existing_books = [obj for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]
            next_number = len(existing_books) + 1
        except:
            next_number = 1

        # Импортируем функцию генерации PDF
        from ..utils.content_generation import create_random_pdf_book

        # Генерируем 3 новые книги
        for i in range(3):
            book_number = next_number + i
            title = f"Generated Book {book_number}"
            author = "GPN"
            description = "Book with random content"
            filename = f"book_{book_number}_{int(time.time())}_{i}.pdf"

            # Создаем PDF
            pdf_bytes = create_random_pdf_book(f"Сгенерированная книга {book_number}", "GPN")
            if not pdf_bytes:
                logging.getLogger(__name__).error(f"Не удалось создать PDF для {filename}")
                continue  # Продолжаем с другими книгами, даже если одна не удалась

            # Загружаем в Minio S3 (только ASCII в метаданных)
            s3_client.put_object(
                Bucket=Config.MINIO_BUCKET_NAME,
                Key=filename,
                Body=pdf_bytes,
                ContentType='application/pdf',
                Metadata={
                    'title': title,  # Только ASCII
                    'author': author,  # Только ASCII
                    'description': description,  # Только ASCII
                    'generated': 'true',
                    'timestamp': str(int(time.time())),
                    'language': 'en',
                    'book_number': str(book_number)  # Только ASCII
                }
            )
            new_books.append({
                'filename': filename,
                'title': f'Сгенерированная книга {book_number}',
                'author': 'GPN'
            })
            logging.getLogger(__name__).info(f"Сгенерирована новая книга: {filename}")

        return jsonify({
            "status": "success",
            "message": f"Сгенерировано {len(new_books)} новых книг",
            "books": new_books
        })
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка генерации новых книг: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
@bp.route('/generate-async', methods=['GET', 'POST'])
def generate_books_async():
    """Асинхронная генерация книг через RabbitMQ"""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401

    # Для GET запроса - возвращаем HTML форму или JSON статус
    if request.method == 'GET':
        return jsonify({
            "status": "ready",
            "message": "Endpoint готов для генерации книг через POST запрос"
        })

    # Для POST запроса - ставим задачу в очередь
    try:
        # Получаем данные из запроса
        data = request.get_json() if request.is_json else {}
        count = data.get('count', 3) if data else 3
        user_id = session.get('user', request.headers.get('X-Forwarded-User', 'unknown_user'))
        logging.getLogger(__name__).info(
            f"Постановка задачи генерации {count} книг в очередь от пользователя {user_id}")

        # Создаем подключение к RabbitMQ
        connection = get_rabbitmq_connection()  # Импортируем из utils.task_helpers
        if not connection:
            return jsonify({"error": "Сервис генерации временно недоступен"}), 503

        channel = connection.channel()
        # Объявляем очередь для задач генерации книг (durable для надежности)
        queue_name = 'book_generation_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        # Формируем сообщение задачи
        task_message = {
            'task_id': str(uuid.uuid4()),
            'user_id': user_id,
            'count': count,
            'timestamp': time.time(),
            'type': 'book_generation'
        }

        # Отправляем сообщение в очередь
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(task_message, ensure_ascii=True),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
            )
        )
        logging.getLogger(__name__).info(
            f"Задача генерации книг поставлена в очередь '{queue_name}'. Task ID: {task_message['task_id']}")
        connection.close()

        return jsonify({
            "status": "queued",
            "task_id": task_message['task_id'],
            "message": f"Задача генерации {count} книг поставлена в очередь"
        }), 202

    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка при постановке задачи генерации книг в очередь: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера при постановке задачи"}), 500
@bp.route('/tasks/status')
def get_tasks_status():
    """Получение статуса задач генерации (реальный прогресс из Redis)"""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401
    try:
        # Получаем подключение к Redis
        redis_conn = get_redis_connection()  # Импортируем из extensions
        if not redis_conn:
            return jsonify({"error": "Сервис временно недоступен"}), 500

        # Получаем все задачи из Redis по шаблону
        tasks_pattern = "task_status:*"
        task_keys = redis_conn.keys(tasks_pattern)

        active_tasks = []
        completed_tasks = []
        failed_tasks = []

        for key in task_keys:
            try:
                cached_data = redis_conn.get(key)
                if cached_data:
                    task_data = json.loads(cached_data)
                    # Извлекаем task_id из ключа
                    task_id = key.replace("task_status:", "")

                    if task_data.get('status') == 'completed':
                        completed_tasks.append({
                            'task_id': task_id,
                            'message': task_data.get('message', ''),
                            'progress': task_data.get('progress', 100)
                        })
                    elif task_data.get('status') == 'failed':
                        failed_tasks.append({
                            'task_id': task_id,
                            'message': task_data.get('message', ''),
                            'progress': task_data.get('progress', 0)
                        })
                    else:
                        # Считаем активными все остальные статусы (started, processing и т.д.)
                        active_tasks.append({
                            'task_id': task_id,
                            'message': task_data.get('message', ''),
                            'progress': task_data.get('progress', 0)
                        })
            except Exception as e:
                logging.getLogger(__name__).error(f"Ошибка получения данных задачи {key}: {e}")
                continue  # Продолжаем обработку других задач

        return jsonify({
            "status": "success",
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "total_tasks": len(active_tasks) + len(completed_tasks) + len(failed_tasks)
        })
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка получения статуса задач: {e}")
        return jsonify({"error": "Ошибка получения статуса задач"}), 500
@bp.route('/generate-large-books', methods=['POST'])
def generate_large_books():
    """Генерация больших книг через RabbitMQ с реальным прогрессом(исп. Redis)"""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401
    try:
        # Получаем данные из запроса
        data = request.get_json() if request.is_json else {}
        count = data.get('count', 5) if data else 5  # По умолчанию 5 больших книг
        word_count = data.get('word_count', 5000) if data else 5000  # По умолчанию 5000 слов
        user_id = session.get('user', request.headers.get('X-Forwarded-User', 'unknown_user'))
        logging.getLogger(__name__).info(
            f"Постановка задачи генерации {count} больших книг ({word_count} слов) в очередь от пользователя {user_id}")

        try:
            # Создаем подключение к RabbitMQ
            connection = get_rabbitmq_connection()  
            if not connection:
                return jsonify({"error": "Сервис генерации временно недоступен"}), 503

            channel = connection.channel()
            # Объявляем очередь для задач генерации больших книг (durable для надежности)
            queue_name = 'large_book_generation_queue'
            channel.queue_declare(queue=queue_name, durable=True)

            task_ids = []  # Список для отслеживания ID задач

            # Ставим несколько задач в очередь
            for i in range(count):
                task_id = str(uuid.uuid4())  # Генерируем уникальный ID задачи
                task_message = {
                    'task_id': task_id,
                    'user_id': user_id,
                    'book_number': i + 1,  # Номер книги для отображения
                    'word_count': word_count,  # Количество слов в книге
                    'timestamp': time.time(),
                    'type': 'large_book_generation',
                    # Можно добавить приоритет, если нужно
                    'priority': 'high' if i < 2 else 'normal'  # Первые 2 задачи с высоким приоритетом
                }

                # Отправляем сообщение в очередь с возможностью установки приоритета
                channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(task_message, ensure_ascii=True),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                        # Устанавливаем приоритет, если он есть в сообщении
                        priority=1 if i < 2 else 0  # 1 - высокий, 0 - нормальный
                    )
                )
                task_ids.append(task_id)  # Добавляем ID задачи в список
                logging.getLogger(__name__).info(
                    f"Задача генерации большой книги поставлена в очередь '{queue_name}'. Task ID: {task_id}")

            connection.close()

            # Дополнительно: записываем начальный статус задач в Redis для отслеживания
            redis_conn = get_redis_connection()  # Импортируем из extensions
            if redis_conn:
                for task_id in task_ids:
                    task_key = f"task_status:{task_id}"
                    task_data = {
                        'status': 'queued',  # Начальный статус - в очереди
                        'message': f'Задача поставлена в очередь для генерации большой книги {task_id}',
                        'progress': 0,  # Начальный прогресс 0%
                        'updated_at': int(time.time())
                    }
                    # Записываем статус задачи в Redis с TTL 1 час (3600 секунд)
                    redis_conn.setex(task_key, 3600, json.dumps(task_data))

            # Возвращаем успешный ответ с информацией о поставленных задачах
            return jsonify({
                "status": "queued",
                "message": f"Поставлено в очередь {count} задач генерации больших книг",
                "tasks": task_ids,  # Список ID задач для дальнейшего отслеживания
                "queue": queue_name  # Имя очереди, куда были поставлены задачи
            }), 202  # 202 Accepted - задача принята, но еще не выполнена

        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка подключения к RabbitMQ: {e}")
            # Возвращаем ошибку 503 Service Unavailable, если RabbitMQ недоступен
            return jsonify({"error": "Сервис генерации временно недоступен"}), 503

    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка при постановке задач генерации больших книг в очередь: {e}")
        # Возвращаем ошибку 500 Internal Server Error для других ошибок
        return jsonify({"error": "Внутренняя ошибка сервера при постановке задач"}), 500
"""Маршруты для работы с галереей изображений."""
from flask import Blueprint, jsonify, redirect, session, send_from_directory, request, url_for
from ..config import Config

from ..utils.static_files import generate_gallery_html, generate_sample_files
from ..utils.content_generation import generate_random_image
from ..utils.task_helpers import get_rabbitmq_connection
import os
import random
import uuid
import json
import pika
import time
import logging

bp = Blueprint('gallery', __name__, url_prefix='/gallery')
@bp.route('/')
def gallery():
    """Отображение страницы галереи изображений."""
    access_token = session.get('access_token')
    if not access_token:
        logging.getLogger(__name__).warning("В сессии отсутствует токен доступа")
        return redirect(url_for('auth.auth_login'))  # Используем url_for для blueprint'а
    # Генерируем HTML галереи (обновляем список файлов)
    generate_gallery_html()
    # Отправляем сгенерированный HTML файл
    return send_from_directory(Config.STATIC_DIR, 'gallery.html')
@bp.route('/generate-images')
def generate_images():
    """Синхронная генерация изображений (для тестирования)."""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401
    try:
        new_images = []
        # Получаем список существующих изображений для определения следующего номера
        existing_images = [f for f in os.listdir(Config.STATIC_DIR) if f.endswith('.png')]
        next_index = len([f for f in existing_images if f.startswith('image_')]) + 1

        # Генерируем 4 новых изображения
        for i in range(4):
            filename = f"image_{next_index + i}.png"
            filepath = os.path.join(Config.STATIC_DIR, filename)
            generate_random_image(filepath)
            new_images.append(filename)
            logging.getLogger(__name__).info(f"Сгенерировано новое изображение: {filename}")

        # Обновляем HTML галереи
        generate_gallery_html()

        return jsonify({
            "status": "success",
            "message": f"Сгенерировано {len(new_images)} новых изображений",
            "images": new_images
        })
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка генерации изображений: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
@bp.route('/refresh-static')
def refresh_static():
    """Обновление статических файлов."""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401
    try:
        generate_sample_files()
        return jsonify({"status": "success", "message": "Статические файлы обновлены"})
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка обновления статики: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
@bp.route('/generate-images-async', methods=['GET', 'POST'])
def generate_images_async():
    """Асинхронная генерация изображений через RabbitMQ"""
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({"error": "Требуется аутентификация"}), 401

    # Для GET запроса - возвращаем HTML форму или JSON статус
    if request.method == 'GET':
        return jsonify({
            "status": "ready",
            "message": "Endpoint готов для генерации изображений через POST запрос"
        })

    # Для POST запроса - ставим задачу в очередь
    try:
        # Получаем данные из запроса
        data = request.get_json() if request.is_json else {}
        count = data.get('count', 4) if data else 4
        user_id = session.get('user', request.headers.get('X-Forwarded-User', 'unknown_user'))
        logging.getLogger(__name__).info(
            f"Постановка задачи генерации {count} изображений в очередь от пользователя {user_id}")

        # Создаем подключение к RabbitMQ
        connection = get_rabbitmq_connection()
        if not connection:
            return jsonify({"error": "Сервис генерации временно недоступен"}), 503

        channel = connection.channel()
        # Объявляем очередь для задач генерации изображений (durable для надежности)
        queue_name = 'image_generation_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        # Формируем сообщение задачи
        task_message = {
            'task_id': str(uuid.uuid4()),
            'user_id': user_id,
            'count': count,
            'timestamp': time.time(),
            'type': 'image_generation'
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
            f"Задача генерации изображений поставлена в очередь '{queue_name}'. Task ID: {task_message['task_id']}")
        connection.close()

        return jsonify({
            "status": "queued",
            "task_id": task_message['task_id'],
            "message": f"Задача генерации {count} изображений поставлена в очередь"
        }), 202

    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка при постановке задачи генерации изображений в очередь: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера при постановке задачи"}), 500
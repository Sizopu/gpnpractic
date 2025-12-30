"""Основные маршруты приложения."""
from flask import Blueprint, jsonify, redirect, session, request, url_for, render_template_string
from ..utils.content_generation import get_random_quote
import logging

bp = Blueprint('main', __name__)
@bp.route('/check')
def check():
    """Маршрут для проверки состояния сервиса (без аутентификации)."""
    return jsonify({"status": "OK"})

@bp.route('/')
def index():
    """Главная страница приложения."""
    access_token = session.get('access_token')
    if not access_token:
        logging.getLogger(__name__).info("В сессии отсутствует токен доступа для главной страницы, перенаправление на вход")
        return redirect('/auth/login')
    return redirect('/jason')

@bp.route('/jason')
def jason():
    """Страница с цитатой и ссылками на галерею и библиотеку."""
    access_token = session.get('access_token')
    if not access_token:
        logging.getLogger(__name__).info("В сессии отсутствует токен доступа для /jason, перенаправление на вход")
        return redirect(url_for('auth.auth_login'))  # Используем url_for для blueprint'а
    try:
        quote_data = get_random_quote()
        html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Quotation-book</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .quote-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 800px;
            margin: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .quote {
            font-size: 28px;
            font-style: italic;
            margin-bottom: 30px;
            line-height: 1.6;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }
        .buttons-container {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .action-button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            border: 1px solid rgba(255, 255, 255, 0.3);
            font-weight: bold;
        }
        .action-button:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .user-info {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 14px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="user-info">
        Пользователь: ''' + request.headers.get('X-Forwarded-User', 'Неизвестный пользователь') + '''</div>
    <div class="quote-container">
        <div class="quote">"''' + quote_data['quote'] + '''"</div>
        <div class="buttons-container">
            <!-- Новая кнопка для /metrics -->
            <a href="/metrics" class="action-button">📊 Метрики</a>
            <a href="/gallery" class="action-button">🖼 Галерея изображений</a>
            <a href="/library" class="action-button">📚 Электронная библиотека</a>
        </div>
    </div>
</body>
</html>'''
        return html_content
    except Exception as e:
        logging.getLogger(__name__).error(f"Ошибка обработки запроса: {e}")
        return "<h1>Ошибка получения цитаты</h1>", 500
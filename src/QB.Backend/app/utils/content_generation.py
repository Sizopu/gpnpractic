"""Утилиты для генерации контента (цитаты, PDF, изображения)."""
import random
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import textwrap
import io
import datetime
import hashlib
import json
from ..extensions import get_redis_connection, get_db_connection
from ..config import Config
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger(__name__)

def get_random_quote():
    """Функция для получения случайной цитаты с кэшированием в Redis"""
    redis_conn = None
    try:
        # Пытаемся получить подключение к Redis
        redis_conn = get_redis_connection()
        # Пробуем получить список цитат из Redis кэша
        cached_quotes = redis_conn.lrange("random_quotes", 0, -1)
        if cached_quotes:
            # Если кэш найден, выбираем случайную цитату из него
            quote = random.choice(cached_quotes)
            logger.info("Случайная цитата выбрана из Redis кэша")
            return {"quote": quote}
    except Exception as e:
        # Логируем ошибку при работе с Redis, но не прерываем выполнение
        logger.error(f"Ошибка при работе с Redis: {e}")

    # Если кэш пуст или Redis недоступен, получаем цитаты из PostgreSQL
    logger.info("Обновление кэша цитат из PostgreSQL")
    try:
        # Получаем подключение к базе данных
        conn = get_db_connection()
        cur = conn.cursor()
        # Выполняем запрос к таблице quotes, выбирая 10 случайных записей
        cur.execute("SELECT quote FROM quotes ORDER BY RANDOM() LIMIT 10;")
        # Извлекаем все результаты и формируем список цитат
        quotes = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        # Если цитаты получены и Redis доступен, обновляем кэш
        if redis_conn and quotes:
            try:
                # Удаляем старый кэш
                redis_conn.delete("random_quotes")
                # Добавляем новые цитаты в кэш с TTL из конфигурации
                redis_conn.lpush("random_quotes", *quotes)
                redis_conn.expire("random_quotes", Config.POSTGRES_CACHE_TTL)
                logger.info(f"В кэш Redis добавлено {len(quotes)} цитат")
                # Возвращаем случайную цитату из только что полученных
                quote = random.choice(quotes)
                return {"quote": quote}
            except Exception as e:
                logger.error(f"Ошибка сохранения данных в Redis: {e}")

        # Если Redis недоступен, возвращаем одну случайную цитату напрямую
        if quotes:
            return {"quote": random.choice(quotes)}
    except Exception as e:
        logger.error(f"Ошибка получения цитат из PostgreSQL: {e}")

    # Если ничего не удалось получить, возвращаем сообщение об ошибке
    return {"quote": "Цитаты не найдены"}

def generate_book_content(word_count=500):
    """Генерирует случайное содержание для книги"""
    # Объявляем словарь для генерации
    english_words = [
        "abstract", "basic", "virtual", "general", "dynamic", "electronic",
        "fundamental", "global", "innovative", "quantum", "logistic",
        "mathematical", "navigation", "optimal", "progressive", "qualitative",
        "recursive", "synthetic", "transformational", "universal", "analysis",
        "library", "configuration", "documentation", "encyclopedia", "framework",
        "generator", "identifier", "coding", "localization", "modernization",
        "optimization", "protocol", "repository", "synchronization", "translation",
        "utility", "validation", "interface", "algorithm", "database",
        "vector", "graphic", "diagram", "function", "class", "method",
        "object", "property", "variable", "constant", "array", "list",
        "dictionary", "string", "number", "logic", "theory", "practice",
        "experiment", "observation", "hypothesis", "conclusion", "summary",
        "process", "system", "structure", "model", "pattern", "architecture",
        "design", "component", "module", "service", "application", "platform",
        "tool", "technology", "methodology", "paradigm", "concept", "principle",
        "development", "implementation", "integration", "solution", "approach",
        "strategy", "infrastructure", "environment", "deployment", "monitoring",
        "performance", "scalability", "reliability", "security", "availability",
        "maintainability", "compatibility", "portability", "efficiency", "simplicity",
        "flexibility", "extensibility", "modularity", "interoperability", "standardization",
        "specification", "requirement", "constraint", "capability", "feature",
        "characteristic", "attribute", "quality", "metric", "benchmark", "testing",
        "debugging", "profiling", "optimization", "refactoring", "maintenance",
        "documentation", "training", "support", "consulting", "implementation",
        "migration", "upgrade", "enhancement", "extension", "customization"
    ]

    words = []
    for _ in range(word_count):
        word = random.choice(english_words)
        # Рандом функция которая проставляет слово с заглавной буквы :)
        if random.random() < 0.1:
            word = word.capitalize()
        words.append(word)

    # Разбиваем на предложения
    sentences = []
    sentence_length = random.randint(8, 20)
    current_sentence = []

    for i, word in enumerate(words):
        current_sentence.append(word)
        if len(current_sentence) >= sentence_length or i == len(words) - 1:
            # Добавляем точку в конце предложения
            sentence = " ".join(current_sentence) + "."
            sentences.append(sentence)
            current_sentence = []
            sentence_length = random.randint(8, 20)

    # Разбиваем на абзацы
    paragraphs = []
    paragraph_size = random.randint(3, 10)
    current_paragraph = []

    for i, sentence in enumerate(sentences):
        current_paragraph.append(sentence)
        if len(current_paragraph) >= paragraph_size or i == len(sentences) - 1:
            paragraph = " ".join(current_paragraph)
            paragraphs.append(paragraph)
            current_paragraph = []
            paragraph_size = random.randint(3, 10)

    return "\n\n".join(paragraphs)

def create_random_pdf_book(title, author):
    """Создаёт PDF книгу"""
    try:
        # Создаем буфер для PDF
        buffer = io.BytesIO()

        # Создаем PDF документ
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Заголовок
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 50, title)

        # Автор
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 70, f"Автор: {author}")

        # Дата генерации
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 90, f"Сгенерировано: {datetime.datetime.now().strftime('%Y-%m-%d')}")

        # Разделительная линия
        c.line(50, height - 110, width - 50, height - 110)

        # Генерируем содержание
        content = generate_book_content(random.randint(300, 800))

        # Текст книги
        c.setFont("Helvetica", 10)
        y_position = height - 140
        margin = 50
        line_height = 14

        # Разбиваем текст на строки
        lines = content.split('\n')

        for line in lines:
            if y_position < 50:  # Если достигли конца страницы
                c.showPage()
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(width / 2, height - 50, title)
                c.setFont("Helvetica", 10)
                y_position = height - 80

            # Перенос длинных строк
            if len(line) > 80:
                wrapped_lines = textwrap.wrap(line, width=80)
                for wrapped_line in wrapped_lines:
                    c.drawString(margin, y_position, wrapped_line)
                    y_position -= line_height
                    if y_position < 50:
                        c.showPage()
                        c.setFont("Helvetica-Bold", 16)
                        c.drawCentredString(width / 2, height - 50, title)
                        c.setFont("Helvetica", 10)
                        y_position = height - 80
            else:
                c.drawString(margin, y_position, line)
                y_position -= line_height

            # Дополнительный отступ между абзацами
            if line.strip() == "":
                y_position -= line_height * 0.5

        c.save()

        # Получаем байты PDF
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except Exception as e:
        logger.error(f"Ошибка создания PDF книги '{title}': {e}")
        return None

def extract_text_from_pdf(pdf_bytes):
    """Извлекает текст из PDF файла"""
    try:
        # Создаем объект BytesIO из байтов PDF
        pdf_file = io.BytesIO(pdf_bytes)
        # Создаем объект PdfReader для чтения PDF
        pdf_reader = PdfReader(pdf_file)
        # Инициализируем переменную для хранения текста
        text = ""
        # Проходим по всем страницам PDF и извлекаем текст
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        # Если текст длиннее 2000 символов, обрезаем его и добавляем многоточие
        return text[:2000] + "..." if len(text) > 2000 else text
    except Exception as e:
        # Логируем ошибку и возвращаем сообщение об ошибке
        logger.error(f"Ошибка извлечения текста из PDF: {e}")
        return "Ошибка извлечения текста из PDF файла"

def generate_random_image(filepath):
    """Генерирует случайное изображение"""
    width, height = 400, 300
    image = Image.new('RGB', (width, height),
                      (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
    draw = ImageDraw.Draw(image)

    for _ in range(15):
        shape_type = random.choice(['rectangle', 'ellipse', 'line'])
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)

        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        if shape_type == 'rectangle':
            draw.rectangle([x_min, y_min, x_max, y_max], fill=color)
        elif shape_type == 'ellipse':
            draw.ellipse([x_min, y_min, x_max, y_max], fill=color)
        elif shape_type == 'line':
            draw.line([x1, y1, x2, y2], fill=color, width=random.randint(1, 8))

    image.save(filepath, 'PNG')
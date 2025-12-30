"""Модуль для генерации контента (PDF, изображения)."""
import random
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import textwrap
import io
import datetime
from .connections import get_redis_connection
import time
import json
import logging

logger = logging.getLogger(__name__)
def generate_book_content(word_count=500):
    """Генерирует случайное содержание для книги"""
    # Объявляем словарь
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
        "documentation", "training", "support", "consulting", "migration",
        "upgrade", "enhancement", "extension", "customization"
    ]

    words = []
    for _ in range(word_count):
        word = random.choice(english_words)
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
        # import datetime # Уже импортирован
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
def create_large_pdf_book(title, author, word_count=5000, task_id=None):
    """Создаёт большую PDF книгу с указанным количеством слов и искусственной задержкой в +- 2-3 секунды"""
    try:
        logger.info(f"Начало генерации большой книги: {title} ({word_count} слов)")
        start_time = time.time()

        # Добавляем искусственную задержку для демонстрации прогресса
        # Имитируем длительную генерацию
        artificial_delay = random.uniform(3.0, 5.0)  # 3-5 секунд задержки
        logger.info(f"Добавлена искусственная задержка: {artificial_delay:.2f} секунд")

        # Обновляем статус задачи
        if task_id:
            set_task_status(task_id, "processing", f"Начало генерации книги {title}", 10)

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
        # import datetime # Уже импортирован
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 90,
                            f"Сгенерировано: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Разделительная линия
        c.line(50, height - 110, width - 50, height - 110)

        # Генерируем содержание
        content = generate_book_content(word_count)

        # Обновляем статус задачи
        if task_id:
            set_task_status(task_id, "processing", f"Генерация содержания книги {title}", 30)

        # Текст книги
        c.setFont("Helvetica", 10)
        y_position = height - 140
        margin = 50
        line_height = 14

        lines = content.split('\n')

        total_lines = len(lines)
        processed_lines = 0

        for line_idx, line in enumerate(lines):
            processed_lines += 1

            # Добавляем искусственную задержку каждые 50 строк
            if line_idx % 50 == 0 and line_idx > 0:
                time.sleep(0.4)  # 0.4 секунды задержки каждые 50 строк
                # Обновляем прогресс
                if task_id:
                    progress = 30 + int((processed_lines / total_lines) * 60)
                    set_task_status(task_id, "processing",
                                    f"Генерация строки {processed_lines}/{total_lines} книги {title}", progress)

            if y_position < 50:  # Если достигли конца страницы
                c.showPage()
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(width / 2, height - 50, title)
                c.setFont("Helvetica", 10)
                y_position = height - 80

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

            if line.strip() == "":
                y_position -= line_height * 0.5

        c.save()

        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        end_time = time.time()
        logger.info(
            f"Завершена генерация большой книги: {title}. Размер: {len(pdf_bytes)} байт. Время: {end_time - start_time:.2f}с")

        # Обновляем статус задачи
        if task_id:
            set_task_status(task_id, "processing", f"Завершена генерация книги {title}", 90)

        return pdf_bytes

    except Exception as e:
        logger.error(f"Ошибка создания большой PDF книги '{title}': {e}")
        if task_id:
            # Импортируем set_task_status локально, чтобы избежать циклического импорта
            from .connections import get_redis_connection
            redis_conn = get_redis_connection()
            if redis_conn:
                task_key = f"task_status:{task_id}"
                task_data = {
                    'status': 'failed',
                    'message': f"Ошибка создания книги {title}: {str(e)}",
                    'progress': 0,
                    'updated_at': int(time.time())
                }
                redis_conn.setex(task_key, 3600, json.dumps(task_data))
        return None
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

def set_task_status(task_id, status, message="", progress=0):
    """Установка статуса задачи в Redis"""
    try:
        redis_conn = get_redis_connection() # Используем импортированную функцию
        if not redis_conn:
            return False

        task_key = f"task_status:{task_id}"
        task_data = {
            'status': status,
            'message': message,
            'progress': progress,
            'updated_at': int(time.time())
        }

        redis_conn.setex(task_key, 3600, json.dumps(task_data))  # Храним 1 час
        logger.info(f"Статус задачи {task_id} обновлен: {status}")
        return True
    except Exception as e:
        logger.error(f"Ошибка установки статуса задачи {task_id}: {e}")
        return False
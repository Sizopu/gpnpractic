"""Утилиты для работы со статическими файлами."""
import os
import time
from .content_generation import generate_random_image
from ..services.s3_service import init_minio  
from ..config import Config
import logging

logger = logging.getLogger(__name__)
def init_static_dir():
    """Создает директорию для статических файлов"""
    # Проверяем существование директории и создаем её при необходимости
    if not os.path.exists(Config.STATIC_DIR):
        os.makedirs(Config.STATIC_DIR)
        logger.info(f"Создана директория для статики: {Config.STATIC_DIR}")
    # Генерируем начальные статические файлы
    generate_sample_files()
    # Инициализируем Minio S3 bucket
    init_minio()
def generate_sample_files():
    """Генерирует начальные статические файлы"""
    try:
        # Генерируем 4 начальных изображения
        for i in range(4):
            filename = f"image_{i + 1}.png"
            filepath = os.path.join(Config.STATIC_DIR, filename)
            generate_random_image(filepath)
            logger.info(f"Сгенерировано изображение: {filename}")

        # Создаем CSS файл с необходимыми стилями
        css_content = '''body {
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
    margin: 0;
    padding: 20px;
    color: white;
    min-height: 100vh;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
}
h1 {
    text-align: center;
    margin-bottom: 30px;
    font-size: 2.5em;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}
.controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 15px;
}
.generate-button {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;
    border: 1px solid rgba(255, 255, 255, 0.3);
    font-weight: bold;
    font-family: Arial, sans-serif;
}
.generate-button:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}
.generate-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}
.message {
    padding: 12px 24px;
    border-radius: 6px;
    margin-bottom: 15px;
    text-align: center;
    font-weight: bold;
}
.message.success {
    background: rgba(46, 204, 113, 0.2);
    border: 1px solid rgba(46, 204, 113, 0.5);
}
.message.error {
    background: rgba(231, 76, 60, 0.2);
    border: 1px solid rgba(231, 76, 60, 0.5);
}
.gallery {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}
.image-card {
    background: rgba(255, 255, 255, 0.1);
    padding: 15px;
    border-radius: 12px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    text-align: center;
    transition: transform 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.2);
}
.image-card:hover {
    transform: translateY(-5px);
    background: rgba(255, 255, 255, 0.15);
}
.image-card img {
    max-width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.image-name {
    font-weight: bold;
    margin: 10px 0;
    font-size: 1.1em;
}
.back-link {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;
    border: 1px solid rgba(255, 255, 255, 0.3);
    font-weight: bold;
    font-family: Arial, sans-serif;
}
.back-link:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}
/* Адаптивность */
@media (max-width: 768px) {
    .controls {
        flex-direction: column;
        text-align: center;
    }
    .back-link, .generate-button {
        width: 100%;
        text-align: center;
    }
}'''
        # Полный путь к CSS файлу
        css_path = os.path.join(Config.STATIC_DIR, "styles.css")
        # Удаляем старый CSS файл, если он существует
        if os.path.exists(css_path):
            os.remove(css_path)
        # Создаем новый CSS файл и записываем в него содержимое
        with open(css_path, "w", encoding='utf-8') as f:
            f.write(css_content)
        logger.info("Создан CSS файл с необх. стилями")
        # Генерируем HTML файл галереи
        generate_gallery_html()
    except Exception as e:
        logger.error(f"Ошибка генерации статических файлов: {e}")

def generate_gallery_html():
    """Генерирует HTML файл галереи"""
    try:
        # Получаем список PNG изображений из директории статики
        image_files = [f for f in os.listdir(Config.STATIC_DIR) if f.endswith('.png') and f.startswith('image_')]
        # Получаем текущую временную метку для версионирования CSS
        timestamp = int(time.time())
        # Формируем HTML содержимое галереи
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Галерея изображений</title>
    <link rel="stylesheet" href="/static/styles.css?v={timestamp}">
</head>
<body>
    <div class="container">
        <h1>Галерея случайных изображений</h1>
        <div class="controls">
            <a href="/jason" class="back-link">← Назад к цитатам</a>
            <button class="generate-button" onclick="generateImages()">Генерировать новые изображения</button>
        </div>
        <div id="message" class="message"></div>
        <div class="gallery">
'''
        # Добавляем HTML код для каждого изображения
        for filename in sorted(image_files):
            html_content += f'''
            <div class="image-card">
                <img src="/static/{filename}" alt="Изображение {filename}">
                <div class="image-name">{filename}</div>
            </div>
'''
        # Завершаем HTML содержимое
        html_content += '''
        </div>
    </div>
    <script>
    async function generateImages() {
    const button = document.querySelector('.generate-button');
    const message = document.getElementById('message');
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Генерация...';
    message.textContent = '';
    message.className = 'message';
    try {
        const response = await fetch('/gallery/generate-images-async', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                count: 4  // Количество изображений для генерации
            })
        });
        const data = await response.json();
        if (response.ok) {
            message.textContent = data.message;
            message.className = 'message success';
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            message.textContent = 'Ошибка: ' + data.message;
            message.className = 'message error';
        }
    } catch (error) {
        message.textContent = 'Ошибка сети: ' + error.message;
        message.className = 'message error';
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}
    </script>
</body>
</html>'''
        # Полный путь к HTML файлу галереи
        gallery_path = os.path.join(Config.STATIC_DIR, "gallery.html")
        # Удаляем старый HTML файл галереи, если он существует
        if os.path.exists(gallery_path):
            os.remove(gallery_path)
        # Создаем новый HTML файл галереи и записываем в него содержимое
        with open(gallery_path, "w", encoding='utf-8') as f:
            f.write(html_content)
        logger.info("Создан HTML файл галереи с версионированием CSS")
    except Exception as e:
        logger.error(f"Ошибка генерации HTML галереи: {e}")

def generate_library_html(books):
    """Генерирует HTML файл библиотеки с кнопкой для генерации объемн. книг"""
    try:
        # Получаем текущую временную метку для версионирования CSS
        timestamp = int(time.time())
        # Начинаем формировать HTML содержимое библиотеки
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Электронная библиотека</title>
    <link rel="stylesheet" href="/static/styles.css?v={timestamp}">
</head>
<body>
    <div class="container">
        <h1>📚 Электронная библиотека</h1>
        <div class="controls">
            <a href="/jason" class="back-link">← Назад к цитатам</a>
            <div class="generate-buttons">
                <button class="generate-button" onclick="generateBooks()">🕮 Подготовить новые книги</button>
                <button class="generate-large-button" onclick="generateLargeBooks()">🕮 Добавить объёмные книги</button>
            </div>
        </div>
        <div id="message" class="message"></div>
        <div id="progress" class="progress-bar" style="display: none;">
            <div class="progress-fill"></div>
            <div class="progress-text">0%</div>
        </div>
        <div class="books-grid">
'''
        # Если список книг пуст, показываем сообщение
        if not books:
            html_content += '''
            <div class="no-books">
                <p>🕮 В библиотеке пока нет книг</p>
                <p>Книги генерируются автоматически при первом запуске</p>
            </div>
'''
        else:
            # Добавляем HTML код для каждой книги
            for book in books:
                # Рассчитываем размер файла в МБ или байтах
                size_mb = book['size'] / (1024 * 1024)
                size_formatted = f"{size_mb:.2f} МБ" if size_mb > 1 else f"{book['size']} байт"
                html_content += f'''
            <div class="book-card">
                <div class="book-icon">🕮</div>
                <div class="book-title">{book['title']}</div>
                <div class="book-author">🖋 Автор: {book['author']}</div>
                <div class="book-size">🗂 Размер: {size_formatted}</div>
                <div class="book-description">{book['description']}</div>
                <div class="book-actions">
                    <a href="/library/view/{book['filename']}" class="view-button">
                        👁 Просмотреть
                    </a>
                    <a href="/library/download/{book['filename']}" class="download-button" target="_blank">
                        ⬇ Скачать PDF
                    </a>
                </div>
            </div>
'''
        # Завершаем HTML содержимое
        html_content += '''
        </div>
    </div>
    <script>
        async function generateBooks() {
            const button = document.querySelector('.generate-button');
            const message = document.getElementById('message');
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Генерация...';
            message.textContent = '';
            message.className = 'message';
            try {
                const response = await fetch('/library/generate-async', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        count: 3
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    message.textContent = data.message;
                    message.className = 'message success';
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    message.textContent = 'Ошибка: ' + data.message;
                    message.className = 'message error';
                }
            } catch (error) {
                message.textContent = 'Ошибка сети: ' + error.message;
                message.className = 'message error';
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
    async function generateLargeBooks() {
    const button = document.querySelector('.generate-large-button');
    const message = document.getElementById('message');
    const progress = document.getElementById('progress');
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Постановка в очередь...';
    message.textContent = '';
    message.className = 'message';
    if (progress) {
        progress.style.display = 'block';
        updateProgressBar(0, 'Подготовка к генерации...');
    }
    try {
        const response = await fetch('/library/generate-large-books', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                count: 5,
                word_count: 5000
            })
        });
        const data = await response.json();
        if (response.ok) {
            message.textContent = data.message;
            message.className = 'message success';
            if (progress) {
                updateProgressBar(0, 'Поставлено в очередь 5 задач генерации больших книг');
            }
            if (data.tasks && data.tasks.length > 0) {
                monitorRealProgress(data.tasks);
            } else {
                if (progress) {
                    updateProgressBar(100, 'Задачи поставлены в очередь, ожидание обработки...');
                }
                setTimeout(() => {
                    location.reload();
                }, 5000);
            }
        } else {
            message.textContent = 'Ошибка: ' + data.message;
            message.className = 'message error';
            if (progress) {
                progress.style.display = 'none';
            }
        }
    } catch (error) {
        message.textContent = 'Ошибка сети: ' + error.message;
        message.className = 'message error';
        if (progress) {
            progress.style.display = 'none';
        }
    } finally {
        button.textContent = originalText;
    }
}
async function monitorRealProgress(tasks) {
    const progress = document.getElementById('progress');
    const message = document.getElementById('message');
    let processedTasks = new Set();
    let totalTasks = tasks.length;
    let completedTasks = 0;
    let failedTasks = 0;
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/library/tasks/status');
            const data = await response.json();
            if (response.ok) {
                let currentCompleted = data.completed_tasks ? data.completed_tasks.length : 0;
                let currentFailed = data.failed_tasks ? data.failed_tasks.length : 0;
                let currentActive = data.active_tasks ? data.active_tasks.length : 0;
                let currentTotal = currentCompleted + currentFailed + currentActive;
                currentTotal = Math.min(currentTotal, totalTasks);
                currentCompleted = Math.min(currentCompleted, totalTasks);
                currentFailed = Math.min(currentFailed, totalTasks - currentCompleted);
                if (currentCompleted + currentFailed >= totalTasks) {
                    clearInterval(pollInterval);
                    if (currentFailed > 0) {
                        updateProgressBar(100, `Генерация завершена с ошибками (${currentFailed}/${totalTasks} задач не выполнено)!`);
                        message.textContent = `Генерация завершена. ${currentCompleted} из ${totalTasks} задач выполнено успешно.`;
                        message.className = 'message error';
                    } else {
                        updateProgressBar(100, 'Генерация завершена успешно!');
                        message.textContent = `Все ${totalTasks} задач генерации выполнены успешно!`;
                        message.className = 'message success';
                    }
                    setTimeout(() => {
                        location.reload();
                    }, 3000);
                } else {
                    let overallProgress = Math.round(((currentCompleted + currentFailed) / totalTasks) * 100);
                    overallProgress = Math.min(overallProgress, 99);
                    updateProgressBar(overallProgress, `Генерация... ${overallProgress}% (${currentCompleted}/${totalTasks} завершено)`);
                }
            } else {
                console.error('Ошибка получения статуса задач:', data.message);
                if (!processedTasks.has('error')) {
                    updateProgressBar(0, 'Ошибка получения статуса задач');
                    message.textContent = 'Ошибка: ' + data.message;
                    message.className = 'message error';
                    processedTasks.add('error');
                }
            }
        } catch (error) {
            console.error('Ошибка мониторинга:', error);
            if (!processedTasks.has('network_error')) {
                updateProgressBar(0, 'Ошибка сети при мониторинге');
                message.textContent = 'Ошибка сети: ' + error.message;
                message.className = 'message error';
                processedTasks.add('network_error');
            }
        }
    }, 200);
    setTimeout(() => {
        if (pollInterval) {
            clearInterval(pollInterval);
            updateProgressBar(100, 'Таймаут ожидания завершения генерации');
            message.textContent = 'Превышено время ожидания завершения генерации';
            message.className = 'message warning';
        }
    }, 120000);
}
function updateProgressBar(percent, text) {
    const progress = document.getElementById('progress');
    if (!progress) return;
    const fill = progress.querySelector('.progress-fill');
    const textElement = progress.querySelector('.progress-text');
    if (fill) {
        percent = Math.max(0, Math.min(100, percent));
        fill.style.width = percent + '%';
        if (percent < 30) {
            fill.style.background = 'linear-gradient(90deg, #ff6b6b, #ffa500)';
        } else if (percent < 70) {
            fill.style.background = 'linear-gradient(90deg, #ffa500, #4ecdc4)';
        } else {
            fill.style.background = 'linear-gradient(90deg, #4ecdc4, #45b7d1)';
        }
    }
    if (textElement) {
        textElement.textContent = text || Math.round(percent) + '%';
    }
}
    </script>
    <style>
        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .generate-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .generate-button, .generate-large-button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            border: 1px solid rgba(255, 255, 255, 0.3);
            font-weight: bold;
            font-family: Arial, sans-serif;
        }
        .generate-large-button {
            background: rgba(255, 165, 0, 0.2);
            border: 1px solid rgba(255, 165, 0, 0.3);
        }
        .generate-button:hover:not(:disabled), .generate-large-button:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .generate-large-button:hover:not(:disabled) {
            background: rgba(255, 165, 0, 0.3);
        }
        .generate-button:disabled, .generate-large-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .message {
            padding: 12px 24px;
            border-radius: 6px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: bold;
        }
        .message.success {
            background: rgba(46, 204, 113, 0.2);
            border: 1px solid rgba(46, 204, 113, 0.5);
        }
        .message.error {
            background: rgba(231, 76, 60, 0.2);
            border: 1px solid rgba(231, 76, 60, 0.5);
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 15px;
            position: relative;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            width: 0%;
            transition: width 0.5s ease, background 0.5s ease;
            border-radius: 15px;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
            font-size: 0.9em;
            white-space: nowrap;
        }
        .message.warning {
            background: rgba(241, 196, 15, 0.2);
            border: 1px solid rgba(241, 196, 15, 0.5);
        }
        .books-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .book-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .book-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }
        .book-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        .book-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #fff;
        }
        .book-author {
            font-size: 1em;
            margin-bottom: 8px;
            color: #e0e0e0;
        }
        .book-size {
            font-size: 0.9em;
            margin-bottom: 10px;
            color: #ccc;
        }
        .book-description {
            font-size: 0.9em;
            margin-bottom: 15px;
            color: #ddd;
            line-height: 1.4;
        }
        .book-actions {
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .view-button, .download-button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            border: 1px solid rgba(255, 255, 255, 0.3);
            font-weight: bold;
        }
        .view-button:hover, .download-button:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .no-books {
            grid-column: 1 / -1;
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            font-size: 1.2em;
        }
        @media (max-width: 768px) {
            .controls {
                flex-direction: column;
                text-align: center;
            }
            .generate-buttons {
                width: 100%;
                justify-content: center;
            }
            .back-link, .generate-button, .generate-large-button {
                width: 100%;
                text-align: center;
            }
            .books-grid {
                grid-template-columns: 1fr;
            }
            .book-actions {
                flex-direction: column;
            }
        }
    </style>
</body>
</html>'''
        # Возвращаем сгенерированное HTML содержимое
        return html_content
    except Exception as e:
        logger.error(f"Ошибка генерации HTML библиотеки: {e}")
        return None
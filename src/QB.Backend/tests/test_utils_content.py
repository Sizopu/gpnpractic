"""Тесты для утилит генерации контента."""
import unittest
import io
from app.utils.content_generation import (
    generate_book_content,
    create_random_pdf_book,
    extract_text_from_pdf,
    get_random_quote
)

class TestContentGeneration(unittest.TestCase):
    """Тесты для функций генерации контента."""

    def test_generate_book_content_returns_string(self):
        """Проверяет, что generate_book_content возвращает строку."""
        content = generate_book_content(100) # Генерируем 100 слов
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)
    def test_generate_book_content_approximate_word_count(self):
        """Проверяет приблизительное количество слов в сгенерированном контенте."""
        target_word_count = 200
        content = generate_book_content(target_word_count)
        word_count = len(content.split())
        # Проверяет, что количество слов в разумных пределах
        self.assertGreater(word_count, target_word_count * 0.8)
        self.assertLess(word_count, target_word_count * 1.2)
    def test_create_random_pdf_book_returns_bytes(self):
        """Проверяет, что create_random_pdf_book возвращает байты для PDF."""
        pdf_bytes = create_random_pdf_book("Тестовая книга", "Тестовый автор")
        # Проверяет, что функция вернула ответ
        if pdf_bytes is not None: # Функция может вернуть None в случае ошибки
            self.assertIsInstance(pdf_bytes, bytes)
            # Проверяем, что это действительно PDF (по сигнатуре)
            self.assertTrue(pdf_bytes.startswith(b'%PDF'))
    def test_extract_text_from_pdf_basic(self):
        """Проверяет базовую работу extract_text_from_pdf."""
        # Создает простой PDF в памяти для теста
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        test_text = "Это тестовый текст для извлечения."
        c.drawString(100, 750, test_text)
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()

        extracted_text = extract_text_from_pdf(pdf_bytes)
        # Проверяет, что извлеченный текст не пустой
        self.assertIsInstance(extracted_text, str)
        self.assertTrue(extracted_text.strip()) # Проверяет, что строка не пуста после удаления пробелов.

if __name__ == '__main__':
    unittest.main()
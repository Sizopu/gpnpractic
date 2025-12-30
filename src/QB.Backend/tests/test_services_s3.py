"""Тесты для сервиса работы с S3 (Minio)."""
import unittest
from unittest.mock import patch, MagicMock
# Импортируем тестируемую функцию
from app.services.s3_service import list_books_from_s3


class TestS3Service(unittest.TestCase):
    """Тесты для функций в s3_service."""
    @patch('app.services.s3_service.get_s3_client')  # Мокаем клиент S3
    def test_list_books_from_s3_success(self, mock_get_s3_client):
        """Тест успешного получения списка книг из S3."""
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client

        # Настраиваем mock ответа s3 (List_object)
        mock_response = {
            'Contents': [
                {'Key': 'book_1.pdf', 'Size': 102400, 'LastModified': MagicMock()},
                {'Key': 'book_2.pdf', 'Size': 204800, 'LastModified': MagicMock()},
                {'Key': 'image.png', 'Size': 51200, 'LastModified': MagicMock()},  # Не PDF
            ]
        }
        mock_s3_client.list_objects_v2.return_value = mock_response

        # Настраиваем mock head_object для получения метаданных
        def side_effect_head_object(Bucket, Key):
            if Key == 'book_1.pdf':
                return {'Metadata': {'title': 'Title 1', 'author': 'Author 1', 'description': 'Desc 1'}}
            elif Key == 'book_2.pdf':
                return {'Metadata': {'title': 'Title 2', 'author': 'Author 2', 'description': 'Desc 2'}}
            else:
                return {'Metadata': {}}  # Для случая, если head_object вызывается для image.png

        mock_s3_client.head_object.side_effect = side_effect_head_object

        # Вызываем тестиремую функцию
        result = list_books_from_s3()

        # Проверяем результат
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)  # Только 2 PDF файла
        # Проверяем структуру первого элемента
        self.assertEqual(result[0]['filename'], 'book_1.pdf')
        self.assertEqual(result[0]['size'], 102400)
        self.assertEqual(result[0]['title'], 'Title 1')
        self.assertEqual(result[0]['author'], 'Author 1')
        self.assertEqual(result[0]['description'], 'Desc 1')

        self.assertEqual(result[1]['filename'], 'book_2.pdf')
        self.assertEqual(result[1]['size'], 204800)

        # Проверяем, что list_objects был вызван
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket=unittest.mock.ANY)  
        # Проверяем, что head_object был вызван дважды (для двух PDF)
        self.assertEqual(mock_s3_client.head_object.call_count, 2)

    @patch('app.services.s3_service.get_s3_client')
    def test_list_books_from_s3_empty_bucket(self, mock_get_s3_client):
        """Тест получения списка книг из пустого S3 bucket'а."""
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client

        # Настраиваем mock ответа list_objects для пустого bucket'а
        mock_response = {}
        mock_s3_client.list_objects_v2.return_value = mock_response

        # Вызываем тестируемую функцию
        result = list_books_from_s3()

        # Проверяем результат
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)  # Список пуст

        # Проверяем, что list_objects_v2 был вызван
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket=unittest.mock.ANY)

    @patch('app.services.s3_service.get_s3_client')
    def test_list_books_from_s3_no_s3_client(self, mock_get_s3_client):
        """Тест получения списка книг, если клиент S3 не создан."""
        # Настраиваем mock, чтобы он возвращал None
        mock_get_s3_client.return_value = None

        # Вызываем тестируемую функцию
        result = list_books_from_s3()

        # Проверяем результат
        self.assertEqual(result, [])  # Должен вернуться пустой список

if __name__ == '__main__':
    unittest.main()

"""Тесты для основных маршрутов приложения."""
import unittest
from unittest.mock import patch, MagicMock
from app import create_app

class TestMainRoutes(unittest.TestCase):
    """Тесты для маршрутов в main blueprint."""
    def setUp(self):
        """Создает тестовый клиент перед каждым тестом."""
        # Мокируем get_redis_connection
        patcher = patch('app.extensions.get_redis_connection')
        self.addCleanup(patcher.stop)
        mock_get_redis = patcher.start()
        # Настраиваем mock
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_check_route(self):
        """Тест маршрута /check."""
        # Отправляем GET запрос
        response = self.client.get('/check')
        # Проверяем код ответа
        self.assertEqual(response.status_code, 200)
        # Проверяем, что ответ является JSON
        self.assertEqual(response.content_type, 'application/json')
        # Проверяем содержимое JSON
        data = response.get_json()
        self.assertEqual(data, {"status": "OK"})

    def test_index_redirects_without_token(self):
        """Тест, что / перенаправляет на /auth/login без токена."""
        with self.client.session_transaction() as sess:
            sess.pop('access_token', None)
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)

    def test_jason_redirects_without_token(self):
        """Тест, что /jason перенаправляет на /auth/login без токена."""
        with self.client.session_transaction() as sess:
            sess.pop('access_token', None)
        
        response = self.client.get('/jason')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)

if __name__ == '__main__':
    unittest.main()

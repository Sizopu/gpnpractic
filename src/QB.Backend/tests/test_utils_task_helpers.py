"""Тесты для утилит работы с задачами (RabbitMQ, Redis)."""
import unittest
from unittest.mock import patch, MagicMock
import json
import hashlib # Импортируем hashlib для хэширования
from app.utils.task_helpers import cache_userinfo, get_cached_userinfo, invalidate_userinfo_cache
from app.config import Config

class TestTaskHelpers(unittest.TestCase):
    """Тесты для функций в task_helpers."""

    def _hash_token(self, token):
        """Вспомогательная функция для хэширования токена с исп. sha256"""
        return hashlib.sha256(token.encode()).hexdigest()

    @patch('app.utils.task_helpers.get_redis_connection') # Мокаем подключение к Redis
    def test_cache_userinfo_success(self, mock_get_redis):
        """Тест успешного кэширования userinfo."""
        # Настраивает mock Redis соединения
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        test_token = "test_access_token_123"
        test_userinfo = {"preferred_username": "testuser", "email": "test@gazprom-neft.ru"}
        test_ttl = 300 # 5 минут

        # Вызывает тестируемую функцию
        result = cache_userinfo(test_token, test_userinfo, test_ttl)

        # Проверяет, что функция вернула True
        self.assertTrue(result)
        expected_key = f"userinfo:{self._hash_token(test_token)}"
        expected_json = json.dumps(test_userinfo)
        mock_redis_conn.setex.assert_called_once_with(expected_key, test_ttl, expected_json)
    @patch('app.utils.task_helpers.get_redis_connection')
    def test_get_cached_userinfo_found(self, mock_get_redis):
        """Тест получения userinfo из кэша, когда он есть."""
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        test_token = "test_access_token_456"
        test_userinfo = {"preferred_username": "cacheduser", "name": "Cached User"}
        expected_key = f"userinfo:{self._hash_token(test_token)}"

        # Настраивает mock, чтобы get возвращал закодированный JSON
        mock_redis_conn.get.return_value = json.dumps(test_userinfo)

        # Вызывает тестируемую функцию
        result = get_cached_userinfo(test_token)

        # Проверяет, что результат совпадает
        self.assertEqual(result, test_userinfo)
        # Проверяет, что был вызван метод get у Redis клиента
        mock_redis_conn.get.assert_called_once_with(expected_key)
    @patch('app.utils.task_helpers.get_redis_connection')
    def test_get_cached_userinfo_not_found(self, mock_get_redis):
        """Тест получения userinfo из кэша, когда его нет."""
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        test_token = "nonexistent_token"

        # Настраивает mock, чтобы get возвращал None
        mock_redis_conn.get.return_value = None

        # Вызывает тестируемую функцию
        result = get_cached_userinfo(test_token)

        # Проверяет, что результат None
        self.assertIsNone(result)
    @patch('app.utils.task_helpers.get_redis_connection')
    def test_invalidate_userinfo_cache(self, mock_get_redis):
        """Тест удаления userinfo из кэша."""
        mock_redis_conn = MagicMock()
        mock_get_redis.return_value = mock_redis_conn

        test_token = "token_to_invalidate"
        expected_key = f"userinfo:{self._hash_token(test_token)}"
        # Вызывает тестируемую функцию
        result = invalidate_userinfo_cache(test_token)

        # Проверяет, что функция вернула True
        self.assertTrue(result)
        # Проверяет, что был вызван метод delete у Redis клиента
        mock_redis_conn.delete.assert_called_once_with(expected_key)

if __name__ == '__main__':
    unittest.main()

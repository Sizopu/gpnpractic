"""Тесты для модуля конфигурации."""
import unittest
from app.config import Config

class TestConfig(unittest.TestCase):
    """Тесты для класса конфигурации."""

    def test_config_has_required_attributes(self):
        """Проверяет, что в конфигурации определены ключевые атрибуты."""
        # Проверяем, что атрибуты существуют и имеют значения по умолчанию или из env
        self.assertTrue(hasattr(Config, 'FLASK_SECRET_KEY'))
        self.assertTrue(hasattr(Config, 'BACKEND_PORT'))
        self.assertTrue(hasattr(Config, 'STATIC_DIR'))
        self.assertTrue(hasattr(Config, 'REDIS_HOST'))
        self.assertTrue(hasattr(Config, 'MINIO_BUCKET_NAME'))
        self.assertTrue(hasattr(Config, 'RABBITMQ_HOST'))
    def test_config_default_values(self):
        """Проверяет значения по умолчанию для некоторых атрибутов."""
        # Проверяем значения по умолчанию, определенные в классе Config
        self.assertEqual(Config.BACKEND_PORT, 5000) # Проверяет значение по умолчанию
        self.assertEqual(Config.REDIS_PORT, 6380)   # Проверяет значение по умолчанию
        self.assertEqual(Config.RABBITMQ_PORT, 5671) # Проверяет значение по умолчанию
        # Проверяем, что булевы значения корректно интерпретируются
        self.assertIsInstance(Config.SESSION_COOKIE_SECURE, bool)
        self.assertIsInstance(Config.REDIS_SSL, bool)

if __name__ == '__main__':
    unittest.main()
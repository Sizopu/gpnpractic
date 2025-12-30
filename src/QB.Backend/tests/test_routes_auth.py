"""Тесты для маршрутов аутентификации."""
import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from app.utils.task_helpers import invalidate_userinfo_cache

class TestAuthRoutes(unittest.TestCase):
    """Тесты для маршрутов в auth blueprint."""

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
    @patch('app.routes.auth.requests.post')
    def test_auth_callback_success(self, mock_post):
        """Тест успешного получения токена в /auth/callback."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token'
        }
        mock_post.return_value = mock_response

        response = self.client.get('/auth/callback?code=test_code')
        mock_post.assert_called_once()
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['access_token'], 'test_access_token')
            self.assertEqual(sess['refresh_token'], 'test_refresh_token')

    def test_auth_logout_clears_session(self):
        """Тест, что /auth/logout очищает сессию."""
        with self.client.session_transaction() as sess:
            sess['access_token'] = 'test_token'
            sess['refresh_token'] = 'test_refresh'

        response = self.client.get('/auth/logout')
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertNotIn('access_token', sess)
            self.assertNotIn('refresh_token', sess)


if __name__ == '__main__':
    unittest.main()

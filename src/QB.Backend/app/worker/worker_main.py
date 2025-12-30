"""Модуль с основной логикой worker'а"""
import pika
import time
from .task_handlers import (
    process_book_generation,
    process_large_book_generation,
    process_image_generation
)
from .connections import get_rabbitmq_connection
import logging

logger = logging.getLogger(__name__)
def main():
    """Основная функция worker'а"""
    logger.info("[Worker] Запуск RabbitMQ Worker'а для обработки задач генерации")

    # Подключение к RabbitMQ
    while True:
        try:
            connection = get_rabbitmq_connection() # Используем импортированную функцию
            if not connection:
                 logger.error("[Worker] Не удалось подключиться к RabbitMQ.")
                 time.sleep(5)
                 continue

            channel = connection.channel()
            logger.info("[Worker] Канал RabbitMQ открыт.")

            # Объявляем очереди (durable для надежности)
            channel.queue_declare(queue='book_generation_queue', durable=True)
            channel.queue_declare(queue='image_generation_queue', durable=True)
            channel.queue_declare(queue='large_book_generation_queue',
                                  durable=True) 
            logger.info(
                "[Worker] Очереди 'book_generation_queue', 'image_generation_queue' и 'large_book_generation_queue' объявлены.")

            # Устанавливаем prefetch_count для ограничения параллелизма
            channel.basic_qos(prefetch_count=1)
            logger.info("[Worker] QoS prefetch_count установлен на 1.")

            # Регистрируем обработчики
            channel.basic_consume(queue='book_generation_queue', on_message_callback=process_book_generation)
            channel.basic_consume(queue='image_generation_queue', on_message_callback=process_image_generation)
            channel.basic_consume(queue='large_book_generation_queue',
                                  on_message_callback=process_large_book_generation) 
            logger.info("[Worker] Обработчики сообщений зарегистрированы.")

            logger.info("[Worker] Ожидание сообщений. Для выхода нажмите CTRL+C")
            channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("[Worker] Получен сигнал завершения работы (CTRL+C)")
            break
        except pika.exceptions.AMQPConnectionError as amqp_error:
            logger.error(f"[Worker] Ошибка подключения к RabbitMQ (AMQP): {amqp_error}")
        except Exception as e:
            logger.error(f"[Worker] Критическая ошибка worker'а: {e}")
        finally:
            if 'connection' in locals() and connection and not connection.is_closed:
                connection.close()
                logger.info("[Worker] Подключение к RabbitMQ закрыто.")

        logger.info("[Worker] Повторная попытка подключения через 5 секунд...")
        time.sleep(5)

    logger.info("[Worker] Worker остановлен.")
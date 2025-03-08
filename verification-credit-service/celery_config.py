from celery import Celery

celery_app = Celery(
    "tasks",
    broker="pyamqp://guest@rabbitmq//",  # RabbitMQ comme broker
    backend="redis://redis:6379/0"  # Redis comme backend
)

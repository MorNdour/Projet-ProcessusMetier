from celery import Celery

celery_app = Celery(
    "tasks",
    broker="pyamqp://guest@rabbitmq//",  # Utilisation de RabbitMQ
    backend="redis://redis:6379/0"  # Stockage des résultats dans Redis
)

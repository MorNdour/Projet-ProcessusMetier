from celery import Celery

celery_app = Celery(
    "tasks",
    broker="pyamqp://guest@rabbitmq//",  # RabbitMQ comme broker
    backend="redis://redis:6379/0"  # Stockage des résultats dans Redis
)

# Configuration Celery
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,  # Suivi des tâches en cours
    task_time_limit=300,  # Temps max pour exécuter une tâche (5 min)
    worker_send_task_events=True,  # Active les événements pour Flower
    result_expires=3600  # Expiration des résultats après 1h
)

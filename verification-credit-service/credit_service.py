import logging
import json
import pika
from fastapi import FastAPI
from celery.result import AsyncResult
from tasks import credit_check

# Configuration des logs
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUE_INPUT = "verification_completude"
QUEUE_OUTPUT = "credit_evaluation"

def consume_messages():
    """Écoute la file d'attente des demandes de prêt et déclenche la vérification du crédit"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_INPUT, durable=True)
    channel.queue_declare(queue=QUEUE_OUTPUT, durable=True)

    def callback(ch, method, properties, body):
        logging.info(f" [✔] Reçu une demande pour vérification du crédit: {body.decode()}")
        demande = json.loads(body)

        # Lancer la tâche Celery
        task = credit_check.delay(demande["nom_du_client"], demande["revenu_mensuel"], demande["depenses_mensuelles"])
        demande["task_id"] = task.id  # Associer l'ID de la tâche pour suivi

        # Publier l'état "en cours" de la vérification
        channel.basic_publish(exchange='', routing_key=QUEUE_OUTPUT, body=json.dumps(demande))
        logging.info(f" [✔] Demande envoyée à Celery, task_id: {task.id}")

    channel.basic_consume(queue=QUEUE_INPUT, on_message_callback=callback, auto_ack=True)
    logging.info(f" [✔] En attente des demandes sur {QUEUE_INPUT}...")
    channel.start_consuming()

# Endpoint pour vérifier le statut d'une tâche Celery
@app.get("/credit/status/{task_id}")
def get_credit_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        return {"status": "completed", "result": task_result.result}
    return {"status": "pending"}

# Lancer la consommation RabbitMQ en arrière-plan
import threading
threading.Thread(target=consume_messages).start()

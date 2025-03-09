import logging
import json
import pika
from fastapi import FastAPI
from celery.result import AsyncResult
from tasks import property_evaluation

# Configuration des logs
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUE_INPUT = "dossier-complet"  # Dossiers complets à évaluer
QUEUE_OUTPUT = "property_evaluation_result"  # Résultats de l’évaluation

def consume_messages():
    """Écoute la file d'attente et lance l’évaluation du bien immobilier"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST,port=5672))
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_INPUT, durable=True)
    channel.queue_declare(queue=QUEUE_OUTPUT, durable=True)

    def callback(ch, method, properties, body):
        logging.info(f" [✔] Reçu une demande pour évaluation du bien: {body.decode()}")
        demande = json.loads(body)

        # Lancer la tâche Celery pour estimer la valeur du bien
        task = property_evaluation.delay(demande["propriete_reference"], demande["type_de_la_propriete"])
        demande["task_id"] = task.id  # Associer l'ID de la tâche pour suivi

        # Publier l'état "en cours" de l’évaluation
        channel.basic_publish(exchange='', routing_key=QUEUE_OUTPUT, body=json.dumps(demande))
        logging.info(f" [✔] Demande envoyée à Celery, task_id: {task.id}")

    channel.basic_consume(queue=QUEUE_INPUT, on_message_callback=callback, auto_ack=True)
    logging.info(f" [✔] En attente des demandes sur {QUEUE_INPUT}...")
    channel.start_consuming()

# Endpoint pour vérifier le statut d'une tâche Celery
@app.get("/property/status/{task_id}")
def get_property_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        return {"status": "completed", "result": task_result.result}
    return {"status": "pending"}

# Lancer la consommation RabbitMQ en arrière-plan
import threading
threading.Thread(target=consume_messages).start()

import logging
import json
import pika
import threading
from fastapi import FastAPI
from celery.result import AsyncResult
from tasks import credit_check

# Configuration des logs
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUE_INPUT = "dossier-complet"
QUEUE_OUTPUT = "credit_evaluation"


def consume_messages():
    """Écoute la file d'attente des demandes de prêt et déclenche la vérification du crédit"""

    while True:  # Boucle pour assurer la reconnexion en cas d'erreur
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()

            channel.queue_declare(queue=QUEUE_INPUT, durable=True)
            channel.queue_declare(queue=QUEUE_OUTPUT, durable=True)

            def callback(ch, method, properties, body):
                logging.info(f" [✔] Reçu une demande pour vérification du crédit: {body.decode()}")
                demande = json.loads(body)

                # Lancer la tâche Celery
                task = credit_check.delay(
                    demande["nom_du_client"],
                    demande["revenu_mensuel"],
                    demande["depenses_mensuelles"]
                )
                demande["task_id"] = task.id  # Associer l'ID de la tâche pour suivi

                # Publier l'état "en cours" de la vérification
                channel.basic_publish(exchange='', routing_key=QUEUE_OUTPUT, body=json.dumps(demande))
                logging.info(f" [✔] Demande envoyée à Celery, task_id: {task.id}")

                # Accuser réception du message pour éviter qu'il ne soit ré-envoyé
                ch.basic_ack(delivery_tag=method.delivery_tag)

            # Consommer les messages en mode auto_ack=False pour éviter les pertes en cas de crash
            channel.basic_consume(queue=QUEUE_INPUT, on_message_callback=callback, auto_ack=False)
            logging.info(f" [✔] En attente des demandes sur {QUEUE_INPUT}...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f" [❌] Problème de connexion à RabbitMQ : {e}. Reconnexion dans 5s...")
            import time
            time.sleep(5)  # Attente avant la reconnexion


# Endpoint pour vérifier le statut d'une tâche Celery
@app.get("/credit/status/{task_id}")
def get_credit_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        return {"status": "completed", "result": task_result.result}
    return {"status": "pending"}


# Lancer la consommation RabbitMQ en arrière-plan
threading.Thread(target=consume_messages, daemon=True).start()

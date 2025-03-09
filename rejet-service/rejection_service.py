import logging
import json
import pika
from fastapi import FastAPI

# Configuration des logs
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUE_REJECTED = "loan_rejected"


def connect_rabbitmq():
    """ Établit la connexion avec RabbitMQ """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_REJECTED, durable=True)
    return connection, channel


def rejection_callback(ch, method, properties, body):
    """ Écoute les refus et envoie une notification """
    data = json.loads(body)
    client_id = data["client_id"]

    logging.info(
        f" [❌] Prêt REFUSÉ pour {client_id} - Score crédit: {data['credit_score']}, Valeur bien: {data['property_value']}")

    # Simuler l’envoi d’un email de rejet (peut être intégré avec un vrai service mail)
    print(f"📩 Notification envoyée à {client_id}: Votre prêt a été refusé.")


def consume_messages():
    """ Écoute la file `loan_rejected` """
    connection, channel = connect_rabbitmq()
    channel.basic_consume(queue=QUEUE_REJECTED, on_message_callback=rejection_callback, auto_ack=True)
    logging.info(f" [✔] En attente des décisions de refus...")
    channel.start_consuming()


# Lancer la consommation des messages en arrière-plan
import threading

threading.Thread(target=consume_messages, daemon=True).start()

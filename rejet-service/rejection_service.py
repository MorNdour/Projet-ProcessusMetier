import logging
import json
import pika

# Configuration des logs
logging.basicConfig(level=logging.INFO)

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUE_REJECTED = "loan_rejected"


def connect_rabbitmq():
    """ Établit la connexion avec RabbitMQ """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST,port=5672))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_REJECTED, durable=True)
    return connection, channel


def publish_rejection(client_id, credit_score, property_value):
    """ Publie un rejet de prêt dans RabbitMQ """
    message = {
        "client_id": client_id,
        "credit_score": credit_score,
        "property_value": property_value,
        "status": "rejected"
    }

    connection, channel = connect_rabbitmq()
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_REJECTED,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2  # Persistance des messages
        )
    )
    connection.close()

    logging.info(f" [❌] Prêt refusé pour {client_id}, publié dans {QUEUE_REJECTED}.")




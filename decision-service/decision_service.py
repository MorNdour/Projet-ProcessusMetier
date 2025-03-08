import logging
import json
import pika
from fastapi import FastAPI

# Configuration des logs
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUE_CREDIT = "credit_evaluation"
QUEUE_PROPERTY = "property_evaluation_result"
QUEUE_DECISION = "loan_decision"

# Stock temporaire des résultats en attente
pending_decisions = {}

def connect_rabbitmq():
    """ Établit la connexion avec RabbitMQ """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_CREDIT, durable=True)
    channel.queue_declare(queue=QUEUE_PROPERTY, durable=True)
    channel.queue_declare(queue=QUEUE_DECISION, durable=True)
    return connection, channel

def make_decision(client_id):
    """ Vérifie si toutes les données sont disponibles pour prendre une décision """
    if client_id in pending_decisions and "credit_score" in pending_decisions[client_id] and "property_value" in pending_decisions[client_id]:
        data = pending_decisions.pop(client_id)
        decision = "APPROUVÉ" if data["credit_score"] > 600 and data["property_value"] > 200000 else "REFUSÉ"

        # Création du message final
        decision_data = {
            "client_id": client_id,
            "credit_score": data["credit_score"],
            "property_value": data["property_value"],
            "decision": decision
        }

        # Publication du résultat dans RabbitMQ
        connection, channel = connect_rabbitmq()
        channel.basic_publish(exchange='', routing_key=QUEUE_DECISION, body=json.dumps(decision_data))
        connection.close()

        logging.info(f" [✔] Décision prise pour client {client_id}: {decision}")

def credit_callback(ch, method, properties, body):
    """ Écoute les résultats du score de crédit """
    data = json.loads(body)
    client_id = data["nom_client"]
    pending_decisions.setdefault(client_id, {})["credit_score"] = data["score_credit"]
    make_decision(client_id)

def property_callback(ch, method, properties, body):
    """ Écoute les résultats de l’évaluation immobilière """
    data = json.loads(body)
    client_id = data["propriete_reference"]  # Associer la propriété au client
    pending_decisions.setdefault(client_id, {})["property_value"] = data["valeur_estimee"]
    make_decision(client_id)

def consume_messages():
    """ Écoute les files `credit_evaluation` et `property_evaluation_result` """
    connection, channel = connect_rabbitmq()
    channel.basic_consume(queue=QUEUE_CREDIT, on_message_callback=credit_callback, auto_ack=True)
    channel.basic_consume(queue=QUEUE_PROPERTY, on_message_callback=property_callback, auto_ack=True)
    logging.info(f" [✔] En attente des résultats de crédit et d'évaluation du bien...")
    channel.start_consuming()

# Lancer la consommation des messages en arrière-plan
import threading
threading.Thread(target=consume_messages).start()

@app.get("/decision/status/{client_id}")
def get_decision_status(client_id: str):
    """ Vérifier si une décision a été prise pour un client """
    if client_id in pending_decisions:
        return {"status": "pending"}
    return {"status": "processed"}

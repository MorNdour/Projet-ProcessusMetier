import logging
import json
import pika
import threading
from fastapi import FastAPI

# Configuration des logs
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"

# Files d’entrée
QUEUE_CREDIT = "credit_evaluation"
QUEUE_PROPERTY = "property_evaluation_result"

# Files de sortie
QUEUE_ELIGIBLE = "eligibility_verified"  # Passera à l’assurance habitation
QUEUE_REJECTED = "loan_rejected"  # Enverra vers le service de refus

# Stock temporaire des résultats en attente
pending_decisions = {}


def connect_rabbitmq():
    """ Établit la connexion avec RabbitMQ """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Déclaration des files
    channel.queue_declare(queue=QUEUE_CREDIT, durable=True)
    channel.queue_declare(queue=QUEUE_PROPERTY, durable=True)
    channel.queue_declare(queue=QUEUE_ELIGIBLE, durable=True)
    channel.queue_declare(queue=QUEUE_REJECTED, durable=True)

    return connection, channel


def check_eligibility(client_id):
    """ Vérifie si toutes les informations sont disponibles et prend une décision """
    if client_id in pending_decisions and "credit_score" in pending_decisions[client_id] and "property_value" in \
            pending_decisions[client_id]:
        data = pending_decisions.pop(client_id)

        # Nouvelle logique : l’éligibilité dépend du score de crédit et de la valeur du bien
        if data["credit_score"] > 600 and data["property_value"] > 200000:
            decision = "ÉLIGIBLE"
            queue_output = QUEUE_ELIGIBLE  # Passe à l’étape suivante : assurance habitation
        else:
            decision = "REFUSÉ"
            queue_output = QUEUE_REJECTED  # Rejeté, passera au service de refus

        # Création du message final
        decision_data = {
            "client_id": client_id,
            "credit_score": data["credit_score"],
            "property_value": data["property_value"],
            "decision": decision
        }

        # Publier la décision
        connection, channel = connect_rabbitmq()
        channel.basic_publish(exchange='', routing_key=queue_output, body=json.dumps(decision_data))
        connection.close()

        logging.info(f" [✔] Décision prise pour client {client_id}: {decision} → envoyé à {queue_output}")


def credit_callback(ch, method, properties, body):
    """ Écoute les résultats du score de crédit """
    data = json.loads(body)
    client_id = data["nom_client"]

    # Stocker le score de crédit pour ce client
    pending_decisions.setdefault(client_id, {})["credit_score"] = data["score_credit"]

    # Vérifier si on peut prendre une décision (si on a aussi l'évaluation immobilière)
    check_eligibility(client_id)


def property_callback(ch, method, properties, body):
    """ Écoute les résultats de l’évaluation immobilière """
    data = json.loads(body)
    client_id = data["propriete_reference"]  # Associer la propriété au client

    # Stocker la valeur estimée du bien
    pending_decisions.setdefault(client_id, {})["property_value"] = data["valeur_estimee"]

    # Vérifier si on peut prendre une décision (si on a aussi le score de crédit)
    check_eligibility(client_id)


def consume_messages():
    """ Écoute les files `credit_evaluation` et `property_evaluation_result` """
    while True:
        try:
            connection, channel = connect_rabbitmq()
            channel.basic_consume(queue=QUEUE_CREDIT, on_message_callback=credit_callback, auto_ack=True)
            channel.basic_consume(queue=QUEUE_PROPERTY, on_message_callback=property_callback, auto_ack=True)
            logging.info(f" [✔] En attente des résultats de crédit et d'évaluation du bien...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f" [❌] Problème de connexion à RabbitMQ : {e}. Reconnexion dans 5s...")
            import time
            time.sleep(5)  # Attente avant de réessayer


# Lancer la consommation des messages en arrière-plan
threading.Thread(target=consume_messages, daemon=True).start()


@app.get("/eligibility/status/{client_id}")
def get_eligibility_status(client_id: str):
    """ Vérifier si une décision a été prise pour un client """
    if client_id in pending_decisions:
        return {"status": "pending"}
    return {"status": "processed"}

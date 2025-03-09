import logging
logging.basicConfig (level = logging.DEBUG) 
from fastapi import BackgroundTasks, FastAPI
import requests
from pydantic import BaseModel
import pika
import json

app = FastAPI()


class Accord(BaseModel):
    #Définition des champs de la classe pour la demande
    mail:str
    accept:bool
    reference_property:str

class VerificationAccord:
    def __init__(self, host="rabbitmq", d1_queue="accord-accepter",d2_queue="accord-rejeter"):
        """
        Initialise le processeur RabbitMQ.
        :param host: Adresse du serveur RabbitMQ
        :param s_queue: Queue où écouter les messages
        :param d1_queue: Queue où publier les messages dans la file dossier complet
        :param d2_queue: Queue où publier les messages dans la file dossier incomplet
        """
        self.host = host
        self.d1_queue = d1_queue
        self.d2_queue = d2_queue
        self.connection = None
        self.channel = None

    def connect(self):
        """ Établit la connexion avec RabbitMQ et déclare les queues. """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,port=5672))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.d1_queue, durable=True)
        self.channel.queue_declare(queue=self.d2_queue, durable=True)

    def accord_verification(self, accord):
        """ Traitement du message (modifie ici si besoin) """
        is_accord_accepted = bool(accord.get("accept"))
        if is_accord_accepted:
            self.publish_message(accord,self.d1_queue)
        else:
            self.publish_message(accord,self.d2_queue)
      

    def publish_message(self, message,queue):
        """ Établit la connexion avec RabbitMQ et déclare les queues. """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,port=5672))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.d1_queue, durable=True)
        self.channel.queue_declare(queue=self.d2_queue, durable=True)

        """ Publie un message dans la queue de destination """
        message_bytes = json.dumps(message).encode('utf-8')
        self.channel.basic_publish(
            exchange="", routing_key=queue, body=message_bytes
        )
        print(f"Message publié : {message} dans {queue}")
        self.connection.close()

@app.post("/accord-de-rembourchement-signer")
def encode_documents(accord:Accord):
    accord_rembourchement = accord.json()
    VerificationAccord.accord_verification(accord_rembourchement)
    

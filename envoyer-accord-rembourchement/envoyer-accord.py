import logging
logging.basicConfig (level = logging.DEBUG) 
import pika
import json
import smtplib
from email.message import EmailMessage
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp_server")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))

class EnvoyerAccordRembourchement:
    def __init__(self, host="rabbitmq", queue="loan-eligible"):
        """
        Initialise le processeur RabbitMQ.
        :param host: Adresse du serveur RabbitMQ
        :param queue: Queue où écouter les messages
        """
        self.host = host
        self.queue = queue
        self.connection = None
        self.channel = None

    def connect(self):
        """ Établit la connexion avec RabbitMQ et déclare les queues. """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,port=5672))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True)

    def envoyer_accord_rembourchement(self, body):
        """ Traitement du message """
        message = json.loads(body.decode())  # Convertit les données en texte
        mail = message.get("email")

        msg = EmailMessage()
        msg.set_content("Veuillez signer l'accord de rembourchement et nous le renvoyer")
        msg['Subject'] = f'Accord de rembourchement a signer'
        msg['From'] = "monmail@gmail.com"
        msg['To'] = mail
        # Send the message via our own SMTP server.
        s = smtplib.SMTP(SMTP_HOST,SMTP_PORT)
        s.send_message(msg)
        s.quit()
        print("Mail envoye")
      

    def callback(self, ch, method, properties, body):
        """ Fonction appelée lorsqu'un message est reçu. """
        self.envoyer_accord_rembourchement(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Accuse réception du message

    def start_processing(self):
        """ Démarre l'écoute des messages de la queue source. """
        if self.connection is None or self.channel is None:
            self.connect()

        print(f"En attente de messages dans la queue '{self.queue}'...")
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=False)
        self.channel.start_consuming()

    def close_connection(self):
        """ Ferme proprement la connexion RabbitMQ. """
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Connexion RabbitMQ fermée.")

# Exécution
if __name__ == "__main__":
    processor = EnvoyerAccordRembourchement(host="rabbitmq", queue="loan-eligible")
    try:
        processor.start_processing()
    except KeyboardInterrupt:
        print("\n Arrêt demandé par l'utilisateur.")
        processor.close_connection()

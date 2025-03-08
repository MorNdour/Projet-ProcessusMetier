import logging
logging.basicConfig (level = logging.DEBUG) 
import pika
import json
import smtplib
# Import the email modules we'll need
from email.message import EmailMessage

class CompletuterDossier:
    def __init__(self, host="host.docker.internal", queue="dossier-incomplet"):
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

    def message_compter_dossier(self, body):
        """ Traitement du message (modifie ici si besoin) """
        message = json.loads(body.decode())  # Convertit les données en texte
        mail = message.get("email")

        msg = EmailMessage()
        msg.set_content("Veuillez completer et renvoyer votre dossier")
        msg['Subject'] = f'Dossier incomplet'
        msg['From'] = "monmail@gmail.com"
        msg['To'] = mail
        # Send the message via our own SMTP server.
        s = smtplib.SMTP('host.docker.internal',1025)
        s.send_message(msg)
        s.quit()
        print("Mail envoye")
      

    def callback(self, ch, method, properties, body):
        """ Fonction appelée lorsqu'un message est reçu. """
        self.message_compter_dossier(body)
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
    processor = CompletuterDossier(host="host.docker.internal", queue="dossier-incomplet")
    try:
        processor.start_processing()
    except KeyboardInterrupt:
        print("\n Arrêt demandé par l'utilisateur.")
        processor.close_connection()

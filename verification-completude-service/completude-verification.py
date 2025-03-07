import logging
logging.basicConfig (level = logging.DEBUG) 
import pika

class VerificationCompletudeDemande:
    def __init__(self, host="localhost", s_queue="verification-completude", d1_queue="dossier-complet",d2_queue="dossier-incomplet"):
        """
        Initialise le processeur RabbitMQ.
        :param host: Adresse du serveur RabbitMQ
        :param s_queue: Queue où écouter les messages
        :param d1_queue: Queue où publier les messages dans la file dossier complet
        :param d2_queue: Queue où publier les messages dans la file dossier incomplet
        """
        self.host = host
        self.s_queue = s_queue
        self.d1_queue = d1_queue
        self.d2_queue = d2_queue
        self.connection = None
        self.channel = None

    def connect(self):
        """ Établit la connexion avec RabbitMQ et déclare les queues. """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.s_queue, durable=True)
        self.channel.queue_declare(queue=self.d1_queue, durable=True)
        self.channel.queue_declare(queue=self.d2_queue, durable=True)

    def completude_verification(self, body):
        """ Traitement du message (modifie ici si besoin) """
        message = body.decode()  # Convertit les données en texte
        dossier_complet = any(value in (None, "", " ") for value in message.values())
        if dossier_complet:
            self.publish_message(message,self.d1_queue)
        else:
            self.publish_message(message,self.d2_queue)
      

    def publish_message(self, message,queue):
        """ Publie un message dans la queue de destination """
        self.channel.basic_publish(
            exchange="", routing_key=queue, body=message
        )
        print(f"Message publié : {message} dans {queue}")

    def callback(self, ch, method, properties, body):
        """ Fonction appelée lorsqu'un message est reçu. """
        self.completude_verification(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Accuse réception du message

    def start_processing(self):
        """ Démarre l'écoute des messages de la queue source. """
        if self.connection is None or self.channel is None:
            self.connect()

        print(f"En attente de messages dans la queue '{self.s_queue}'...")
        self.channel.basic_consume(queue=self.s_queue, on_message_callback=self.callback, auto_ack=False)
        self.channel.start_consuming()

    def close_connection(self):
        """ Ferme proprement la connexion RabbitMQ. """
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Connexion RabbitMQ fermée.")

# Exécution
if __name__ == "__main__":
    processor = VerificationCompletudeDemande(host="localhost", s_queue="s_queue", d1_queue="dossier-complet", d2_queue="dossier-incomplet")
    try:
        processor.start_processing()
    except KeyboardInterrupt:
        print("\n Arrêt demandé par l'utilisateur.")
        processor.close_connection()

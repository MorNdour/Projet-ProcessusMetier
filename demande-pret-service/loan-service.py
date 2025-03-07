import logging
logging.basicConfig (level = logging.DEBUG) 
from fastapi import BackgroundTasks, FastAPI
import requests
from pydantic import BaseModel
import pika

app = FastAPI()

class DemandeData(BaseModel):
    #Définition des champs de la classe pour la demande
    nom_du_client = str
    adresse = str
    email = str
    numero_de_telephone = str
    montant_du_pret_demande = int
    duree_du_pret = str
    type_de_la_propriete = str
    propriete_reference = str
    revenu_mensuel = str
    depenses_mensuelles = str

def publie_dans_queue_verification_completude(dossier_client):
    queue_name = 'verification_completude'
    host_name='localhost'
    # Paramètres de connexion à RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host_name))
    channel = connection.channel()

    # Déclarer une file d’attente
    channel.queue_declare(queue=queue_name)

    # Publier un message dans la file d’attente
    channel.basic_publish(exchange='', routing_key=queue_name, body=dossier_client)
    print(f" [x] Envoyé '{dossier_client}'")
    # Fermer la connexion
    connection.close()

@app.post("/demande-de-pret")
async def encode_documents(demande_data:DemandeData,background_tasks: BackgroundTasks):
    dossier_client = demande_data.demande_data
    background_tasks.add_task(publie_dans_queue_verification_completude,dossier_client)
    return {"Bonjour, Demande bien recue! Nous allons l'etudier avec attention."}

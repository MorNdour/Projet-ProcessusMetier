import json
import asyncio
import pika
import logging
import threading
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from typing import List

# Logger
logging.basicConfig(level=logging.INFO)

# Initialisation de FastAPI
app = FastAPI()

# Stockage des WebSockets actifs
connected_clients: List[WebSocket] = []

# Connexion à RabbitMQ
RABBITMQ_HOST = "rabbitmq"
QUEUES = ["loan_decision", "dossier-complet", "dossier-incomplet", "rejet_demande"]

def connect_rabbitmq():
    """Connexion à RabbitMQ et déclaration des files."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST,port=5672))
    channel = connection.channel()
    for queue in QUEUES:
        channel.queue_declare(queue=queue, durable=True)
    return connection, channel

async def broadcast_message(message: str):
    """Envoie un message à tous les clients WebSocket connectés."""
    if connected_clients:
        await asyncio.gather(*[client.send_text(message) for client in connected_clients])

def consume_notifications():
    """Consomme les notifications de plusieurs files RabbitMQ."""
    connection, channel = connect_rabbitmq()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        message = json.dumps(data)
        loop.call_soon_threadsafe(asyncio.create_task, broadcast_message(message))
        logging.info(f" [✔] Notification envoyée : {message}")

    # Écoute toutes les files
    for queue in QUEUES:
        channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)

    logging.info(" [✔] En attente des notifications...")
    channel.start_consuming()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Gère les connexions WebSocket."""
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

@app.get("/sse")
async def sse_notifications():
    """Gère les notifications en SSE."""
    async def event_generator():
        while True:
            await asyncio.sleep(1)  # Simulation d'un envoi périodique
            if connected_clients:
                yield f"data: {json.dumps({'message': 'Mise à jour disponible'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Lancer le consommateur RabbitMQ en arrière-plan
threading.Thread(target=consume_notifications, daemon=True).start()










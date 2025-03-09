from celery_config import celery_app
import time
import random
import logging


@celery_app.task(name="tasks.property_evaluation")
def property_evaluation(propriete_reference, type_de_la_propriete):
    """Simule une évaluation immobilière"""
    logging.info(f" [✔] Évaluation en cours pour {propriete_reference}, Type: {type_de_la_propriete}")

    time.sleep(5)  # Simulation d’un délai de traitement

    # Estimation basée sur le type de propriété
    valeur_estimee = {
        "Appartement": random.randint(100000, 500000),
        "Maison": random.randint(150000, 800000),
        "Bureau": random.randint(200000, 1000000)
    }.get(type_de_la_propriete, random.randint(50000, 300000))  # Valeur par défaut si type inconnu

    result = {
        "propriete_reference": propriete_reference,
        "type_de_la_propriete": type_de_la_propriete,
        "valeur_estimee": valeur_estimee
    }

    logging.info(f" [✔] Résultat de l’évaluation: {result}")
    return result




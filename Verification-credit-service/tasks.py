from celery_config import celery_app
import time
import random


@celery_app.task(name="tasks.credit_check")
def credit_check(nom_client, revenu_mensuel, depenses_mensuelles):
    """Simule une vérification du score de crédit"""
    logging.info(f" [✔] Vérification du crédit pour {nom_client}")

    time.sleep(5)  # Simulation du temps de traitement
    score = max(300, min(850, random.randint(revenu_mensuel // 10, 850)))  # Score basé sur revenus

    decision = "APPROUVÉ" if score > 600 else "REFUSÉ"

    result = {
        "nom_client": nom_client,
        "score_credit": score,
        "decision": decision
    }
    logging.info(f" [✔] Résultat du crédit: {result}")
    return result

# Utilisation d'une image Python légère
FROM python:3.10

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Copie des fichiers de l'application
COPY . /app

# Installation des dépendances
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Exposition du port utilisé par l'API
EXPOSE 8004

# Commande pour lancer le service de décision
CMD ["python3", "decision_service.py"]

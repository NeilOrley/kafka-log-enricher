import torch
from torch.utils.data import Dataset
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from sklearn.model_selection import train_test_split
import numpy as np
import os
from tqdm import tqdm
import json
from confluent_kafka import Consumer
from transformers import DistilBertTokenizer, TrainingArguments, DistilBertForSequenceClassification, Trainer
import configparser
import random

def fetch_kafka_messages():
    # Lire le fichier de configuration pour obtenir des paramètres tels que les paramètres Kafka
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Configuration du consommateur Kafka
    # Générer un identifiant de groupe de consommateurs aléatoire pour éviter les conflits
    consumer_group = f"KafkaLogEnricher_{random.randint(1, 10000)}"
    CONSUMER_CONFIG = {
        'bootstrap.servers': config['ENRICHED']['bootstrap.servers'],
        'group.id': consumer_group,
        'auto.offset.reset': config['ENRICHED']['auto.offset.reset']
    }
    # Définir le sujet à partir duquel les messages seront consommés
    INPUT_TOPIC = config['ENRICHED']['topic']

    # Création du consumer Kafka
    c = Consumer(CONSUMER_CONFIG)    
    c.subscribe([INPUT_TOPIC])

    # Liste pour stocker les données
    data = []

    # Lire les messages de Kafka avec une barre de progression
    with tqdm(desc="Reading messages", dynamic_ncols=True) as pbar:
        while True:
            msg = c.poll(1.0)
            
            if not msg:
                break
            
            # Décoder le message et l'ajouter à la liste
            try:
                data.append(json.loads(msg.value().decode('utf-8')))
                pbar.update(1)  # Mettre à jour la barre de progression
            except UnicodeDecodeError:
                continue

    c.close()  # Fermer le consumer

    print(f"Total messages conservés : {len(data)}")

    return data


def prepare_data(data, input_labels, default_value):
    messages = [item['message'] for item in data]
    default_severity = input_labels.get(default_value)
    labels = [input_labels.get(item['severity'], default_severity) for item in data]

    # Diviser les données en train et validation
    train_texts, val_texts, train_labels, val_labels = train_test_split(messages, labels, test_size=0.2)
    
    return train_texts, val_texts, train_labels, val_labels

def _compute_metrics(eval_pred):
    """
    Calcule les métriques d'évaluation pour les prédictions du modèle.

    Args:
    - eval_pred (tuple): Un tuple contenant les prédictions du modèle et les vraies étiquettes. 
                         Les prédictions doivent être sous forme de logits (sortie brute du modèle).

    Retourne:
    - dict: Un dictionnaire contenant la précision, la précision, le rappel et le score F1.
    """

    # Divise le tuple d'entrée en prédictions et en vraies étiquettes
    predictions, labels = eval_pred

    # Convertit les logits (sorties brutes du modèle) en prédictions de classe en sélectionnant la classe avec le score/logit le plus élevé
    predictions = np.argmax(predictions, axis=1)

    # Calcule et retourne les métriques d'évaluation
    return {
        'accuracy': accuracy_score(labels, predictions),  # Calcule la précision des prédictions
        'precision': precision_score(labels, predictions, average='weighted'),  # Calcule la précision pondérée
        'recall': recall_score(labels, predictions, average='weighted'),  # Calcule le rappel pondéré
        'f1': f1_score(labels, predictions, average='weighted')  # Calcule le score F1 pondéré
    }

def _check_and_load_pretrained(path, type_name):
    """
    Vérifie si un modèle ou un tokenizer pré-formé existe et interroge l'utilisateur pour savoir s'il souhaite l'utiliser.

    :param path: Chemin vers le fichier.
    :param type_name: Nom du type (par exemple, "modèle" ou "tokenizer").
    :return: Boolean indiquant si l'utilisateur souhaite utiliser le pré-entraîné.
    """
    if os.path.exists(path):
        answer = input(f"Un {type_name} pré-formé existe dans '{path}'. Voulez-vous l'utiliser? (oui/non): ").strip().lower()
        return answer == 'oui'
    return False


def initialize_and_train_tokenizer(model_path, train_texts, val_texts, train_labels, val_labels):
    # Demande à l'utilisateur s'il souhaite utiliser le tokenizer précédement entrainé
    use_pretrained_tokenizer = _check_and_load_pretrained(f"{model_path}/tokenizer", "tokenizer")
    if use_pretrained_tokenizer:
        tokenizer = DistilBertTokenizer.from_pretrained(f"{model_path}/tokenizer")
    else:
        tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

    # Tokenization des textes
    train_encodings = tokenizer(train_texts, truncation=True, padding=True)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True)

    # Création des datasets de train et validation
    train_dataset = CustomDataset(train_encodings, train_labels)
    val_dataset = CustomDataset(val_encodings, val_labels)

    # Paramètres d'entraînement
    training_args = TrainingArguments(
        per_device_train_batch_size=8,  # Nombre d'exemples par batch pendant l'entraînement pour chaque dispositif (par exemple GPU)
        per_device_eval_batch_size=8,   # Nombre d'exemples par batch pendant l'évaluation pour chaque dispositif (par exemple GPU)
        num_train_epochs=3,             # Nombre total d'époques d'entraînement
        evaluation_strategy="epoch",    # Stratégie d'évaluation - ici, l'évaluation est effectuée après chaque époque
        logging_dir=f"{model_path}/logs",         # Dossier où les logs d'entraînement seront stockés
        output_dir=f"{model_path}/model"        # Dossier où les résultats d'entraînement (modèle, configurations, etc.) seront sauvegardés
    )

    return tokenizer, train_dataset, val_dataset, training_args


def initialize_and_train_model(training_args, train_dataset, val_dataset, model_path, num_items):
    # Demande à l'utilisateur s'il souhaite utiliser le modèle pré-entrainé
    use_pretrained_model = _check_and_load_pretrained(f"{model_path}/model", "modèle")
    if use_pretrained_model:
        model = DistilBertForSequenceClassification.from_pretrained(f"{model_path}/model")
    else:
        model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=num_items)

    # Création de l'objet Trainer pour gérer l'entraînement et l'évaluation
    trainer = Trainer(
        model=model,                         # Modèle à entraîner
        args=training_args,                  # Arguments et paramètres d'entraînement précédemment définis
        train_dataset=train_dataset,        # Données d'entraînement
        eval_dataset=val_dataset,           # Données d'évaluation (validation)
        compute_metrics=_compute_metrics     # Fonction pour calculer les métriques pendant l'évaluation
    )

    # Démarrer l'entraînement
    trainer.train()


    metrics = trainer.evaluate()
    return model, metrics


def save_assets(model, tokenizer, model_path):
    model.save_pretrained(f"{model_path}/model")
    tokenizer.save_pretrained(f"{model_path}/tokenizer")


# Classe pour le dataset personnalisé
class CustomDataset(Dataset):
    def __init__(self, encodings, labels):
        """
        Constructeur pour la classe CustomDataset.

        Args:
        - encodings (dict): Dictionnaire contenant les encodages/tokenisations des textes. 
                             Typiquement, il s'agit des sorties du tokenizer (tokens, masques d'attention, etc.).
        - labels (list): Liste des étiquettes pour chaque texte du dataset.
        """
        self.encodings = encodings  # Stocke les encodages
        self.labels = labels  # Stocke les étiquettes

    # Renvoie un élément du dataset
    def __getitem__(self, idx):
        """
        Méthode pour obtenir un élément du dataset à un indice spécifié.

        Args:
        - idx (int): L'indice de l'élément à récupérer.

        Retourne:
        - dict: Dictionnaire contenant les encodages et l'étiquette de l'élément à l'indice `idx`.
        """
        # Récupère les encodages pour l'indice donné et les convertit en tenseurs
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        # Ajoute l'étiquette correspondante pour l'indice donné
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    # Renvoie la taille du dataset
    def __len__(self):
        """
        Méthode pour obtenir la taille/longueur du dataset.

        Retourne:
        - int: Le nombre d'éléments dans le dataset.
        """
        return len(self.labels)

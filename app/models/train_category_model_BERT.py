import json
import torch
from confluent_kafka import Consumer
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import configparser
import os
from tqdm import tqdm
import random
import atexit
import numpy as np


# Définition de la variable d'environnement pour la certification
os.environ['CURL_CA_BUNDLE'] = "../caadmin.netskope.com"

# Fonction qui sera appelée à la sortie pour fermer le consumer
@atexit.register
def shutdown():    
    c.close()

# Lire le fichier de configuration
config = configparser.ConfigParser()
config.read('../config.ini')

# Configuration Kafka Consumer
consumer_group = f"KafkaLogEnricher_{random.randint(1, 10000)}"  # Générer un nom de groupe de consommateurs aléatoire
CONSUMER_CONFIG = {
    'bootstrap.servers': config['ENRICHED']['bootstrap.servers'],
    'group.id': consumer_group,
    'auto.offset.reset': config['ENRICHED']['auto.offset.reset']
}

INPUT_TOPIC = config['ENRICHED']['topic']

# Mappage des catégories aux indices
CATEGORY_LABELS = {label: idx for idx, label in enumerate(config['CLASSIFIERS']['categories'].split(','))}

# Création du consumer Kafka
c = Consumer(CONSUMER_CONFIG)
c.subscribe([INPUT_TOPIC])



def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)

    return {
        'accuracy': accuracy_score(labels, predictions),
        'precision': precision_score(labels, predictions, average='weighted'),
        'recall': recall_score(labels, predictions, average='weighted'),
        'f1': f1_score(labels, predictions, average='weighted')
    }


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

# Extraire les messages et leurs labels
messages = [item['message'] for item in data]
default_category = CATEGORY_LABELS.get("Application")
category_labels = [CATEGORY_LABELS.get(item['category'], default_category) for item in data]

# Diviser les données en train et validation
train_texts, val_texts, train_category_labels, val_category_labels = train_test_split(messages, category_labels, test_size=0.2)

# Initialiser le tokenizer DistilBert
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

# Classe pour le dataset personnalisé
class CustomDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    # Renvoie un élément du dataset
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    # Renvoie la taille du dataset
    def __len__(self):
        return len(self.labels)

# Tokenization des textes
train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)

# Création des datasets de train et validation
train_dataset = CustomDataset(train_encodings, train_category_labels)
val_dataset = CustomDataset(val_encodings, val_category_labels)

# Paramètres d'entraînement
training_args = TrainingArguments(
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    evaluation_strategy="epoch",
    logging_dir='app/logs',
    output_dir='app/results'
)

# Nombre de catégories
num_categories = len(CATEGORY_LABELS)
print("Total number of categories:", num_categories)

# Initialiser le modèle DistilBert pour la classification de séquences
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=num_categories)

# Initialiser le Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

# Démarrer l'entraînement
trainer.train()
metrics = trainer.evaluate()
print(metrics)


# Sauvegarder le modèle et le tokenizer
model.save_pretrained("./category_model")
tokenizer.save_pretrained("./category_model")

# Fermer le consumer Kafka
c.close()
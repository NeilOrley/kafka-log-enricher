import json
import torch
from confluent_kafka import Consumer
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
import configparser
import os
os.environ['CURL_CA_BUNDLE'] = "../caadmin.netskope.com"

# Lire le fichier de configuration
config = configparser.ConfigParser()
config.read('../config.ini')

# Configuration Kafka Consumer
CONSUMER_CONFIG = {
    'bootstrap.servers': config['PRODUCER']['bootstrap.servers'],
    'group.id': config['PRODUCER']['group.id'],
    'auto.offset.reset': config['PRODUCER']['auto.offset.reset'],
    'max.poll.interval.ms': int(config['PRODUCER']['max_wait_time']) * 1000,
}

INPUT_TOPIC = config['PRODUCER']['output_topic']

EVENT_TYPE_LABELS = {label: idx for idx, label in enumerate(config['CLASSIFIERS']['event_types'].split(','))}

# Créer le consumer
consumer = Consumer(CONSUMER_CONFIG)
consumer.subscribe([INPUT_TOPIC])

data = []
message_count = 0
while True:
    msg = consumer.poll(timeout=int(config['ENRICHED']['max_wait_time']))

    if msg is None:
        break

    if msg.error():
        print(f"Consumer error: {msg.error()}")
    else:
        data.append(json.loads(msg.value().decode('utf-8')))
        message_count += 1
    
    if message_count >= 100000:
            break

# Prétraitement des données
messages = [item['message'] for item in data]
event_type_labels = [EVENT_TYPE_LABELS[item['event_type']] for item in data]

# Division des données
train_texts, val_texts, train_event_type_labels, val_event_type_labels = train_test_split(messages, event_type_labels, test_size=0.2)

# Tokenization et Création du dataset
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

class CustomDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)
train_dataset = CustomDataset(train_encodings, train_event_type_labels)
val_dataset = CustomDataset(val_encodings, val_event_type_labels)

# Entraînement
training_args = TrainingArguments(
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    evaluation_strategy="epoch",
    logging_dir='./logs',
)

model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased')
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)

trainer.train()

# Sauvegarde
model.save_pretrained("./event_type_model")
tokenizer.save_pretrained("./event_type_model")

# Fermeture du consumer
consumer.close()

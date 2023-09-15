import json
import os
import configparser
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
from confluent_kafka import Consumer, Producer

os.environ['CURL_CA_BUNDLE'] = "caadmin.netskope.com"

# Chargez le fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Configuration Kafka Consumer
consumer_conf = {
    'bootstrap.servers': config['CONSUMER']['bootstrap.servers'],
    'group.id': config['CONSUMER']['group.id'],
    'auto.offset.reset': config['CONSUMER']['auto.offset.reset'],
    'value.deserializer': lambda x: json.loads(x.decode('utf-8'))
}

# Configuration Kafka Producer
producer_conf = {
    'bootstrap.servers': config['ENRICHED']['bootstrap.servers'],
    'value.serializer': lambda x: json.dumps(x).encode('utf-8')
}

# Charger tokenizer et modèles
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
severity_model = DistilBertForSequenceClassification.from_pretrained("./severity_model")
event_type_model = DistilBertForSequenceClassification.from_pretrained("./event_type_model")
category_model = DistilBertForSequenceClassification.from_pretrained("./category_model")

# Mappages label: idx
SEVERITY_LABELS_IDX = {label: idx for idx, label in enumerate(config['CLASSIFIERS']['severities'].split(','))}
EVENT_TYPE_LABELS_IDX = {label: idx for idx, label in enumerate(config['CLASSIFIERS']['event_types'].split(','))}
CATEGORY_LABELS_IDX = {label: idx for idx, label in enumerate(config['CLASSIFIERS']['categories'].split(','))}

SEVERITY_LABELS = {idx: label for label, idx in SEVERITY_LABELS_IDX.items()}
EVENT_TYPE_LABELS = {idx: label for label, idx in EVENT_TYPE_LABELS_IDX.items()}
CATEGORY_LABELS = {idx: label for label, idx in CATEGORY_LABELS_IDX.items()}

def classify_with_model(model, log_message):
    with torch.no_grad():
        inputs = tokenizer(log_message, return_tensors="pt", truncation=True, padding=True, max_length=512)
        logits = model(**inputs).logits
        prediction = torch.argmax(logits, dim=1).item()
    return prediction

def classify_message(log_message):
    severity = SEVERITY_LABELS[classify_with_model(severity_model, log_message)]
    event_type = EVENT_TYPE_LABELS[classify_with_model(event_type_model, log_message)]
    category = CATEGORY_LABELS[classify_with_model(category_model, log_message)]
    return {
        "severity": severity,
        "event_type": event_type,
        "category": category
    }

def main():
    consumer = Consumer(consumer_conf)
    producer = Producer(producer_conf)

    consumer.subscribe([config['CONSUMER']['topic']])
    
    message_count = 0
    max_wait_time = int(config['CONSUMER']['max_wait_time'])

    while True:
        msg = consumer.poll(max_wait_time)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        original_message = msg.value().get('message') or msg.value().get('log') or 'No Content'
        if original_message:
            labels = classify_message(original_message)
            enriched_message = {
                "message": original_message,
                "severity": labels["severity"],
                "event_type": labels["event_type"],
                "category": labels["category"]
            }
            producer.produce(config['ENRICHED']['topic'], value=enriched_message)
            message_count += 1

        if message_count >= 100000:
            break

    consumer.close()

if __name__ == "__main__":
    main()

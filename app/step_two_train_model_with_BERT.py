# Import des bibliothèques nécessaires
import configparser
import os
from step_two_commons import *


def process_classifier_key(key, config, model_path_base):
    """Traite une clé de classification spécifique (par exemple, severities)"""

    # Mappage des éléments de la clé aux indices pour faciliter la classification
    _LABELS = {label: idx for idx, label in enumerate(config['CLASSIFIERS'][key].split(','))}

    # Utilisation de la fonction helper pour extraire les messages de Kafka
    print("Récupération des données dans Kafka...")
    data = fetch_kafka_messages(key)

    # Transformation des données brutes : extraction des messages, division en sets d'entraînement et de validation et obtention des labels
    default_value = config['DEFAULT_CLASSIFIERS'].get(key, list(_LABELS.keys())[0])  # Default au premier élément si non spécifié
    print("Préparation des données : train_texts, val_texts, train_labels, val_labels...")
    train_texts, val_texts, train_labels, val_labels = prepare_data(data, _LABELS, default_value, key)

    # Initialisation du tokenizer, tokenization des données et définition des paramètres d'entraînement
    print("Initialisation du tokenizer et tokenization des données...")
    tokenizer, train_dataset, val_dataset, training_args = initialize_and_train_tokenizer(model_path_base + "/" + key, train_texts, val_texts, train_labels, val_labels)

    # Calcul du nombre total de classes pour la classification
    num_items = len(_LABELS)
    print(f"Total number of {key}:", num_items)

    # Initialisation du modèle, entraînement avec les données préparées et obtention des métriques d'évaluation
    print("Initialisation du modèle, entraînement avec les données préparées et obtention des métriques d'évaluation...")
    model, metrics = initialize_and_train_model(training_args, train_dataset, val_dataset, model_path_base + "/" + key, num_items)
    print(metrics)

    # Une fois l'entraînement terminé, sauvegarder le modèle et le tokenizer pour des utilisations ultérieures
    print("Sauvegarde du modèle et du tokenizer pour utilisation ultérieure...")
    save_assets(model, tokenizer, model_path_base + "/" + key)


model_path_base = "./models"

# Vérifier si le certificat existe
cert_file_path = "caadmin.netskope.com"
if os.path.exists(cert_file_path):
    # Définir la variable d'environnement
    os.environ['CURL_CA_BUNDLE'] = cert_file_path

if not os.path.exists("config.ini"):
    print("Impossible de trouver le fichier de configuration 'config.ini'")
    exit

# Vérifie que Pytorch utilisera un GPU si disponible
if torch.cuda.is_available():
    print("PyTorch est configuré pour utiliser CUDA et donc un GPU") 
else :
    num_gpus = torch.cuda.device_count()
    if num_gpus :
        print(f"/!\ : PyTorch n'est pas configuré pour utiliser CUDA et donc un GPU alors que {num_gpus} GPU sont disponible")      
        for i in range(num_gpus):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")


# Lire le fichier de configuration pour obtenir des paramètres tels que les paramètres Kafka
config = configparser.ConfigParser()
config.read('config.ini')

# Récupérez toutes les clés de la section CLASSIFIERS
classifier_keys = config.options('CLASSIFIERS')

# Itérer sur chaque clé de classification et traiter les données correspondantes
for key in classifier_keys:
    print(f"Entrainement du modèle pour le label '{key}'...")
    process_classifier_key(key, config, model_path_base)
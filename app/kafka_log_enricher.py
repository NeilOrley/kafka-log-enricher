import numpy as np
from modAL.models import ActiveLearner
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from confluent_kafka import Consumer
import json
import configparser
from flask import Flask, render_template, request
from confluent_kafka import Consumer, Producer
from joblib import dump, load
from tqdm import tqdm
import atexit
import re
import random

@atexit.register
def shutdown():    
    c.unsubscribe()
    c.unassign()
    c.close()
    p.flush()


# Variable globale pour activer/désactiver l'Active Learning
ACTIVE_LEARNING_ENABLED = True


# Lire la configuration
print("Chargement de la configuration...")
config = configparser.ConfigParser()
config.read('config.ini')

# Configurer le Consumer
consumer_config = {
    'bootstrap.servers': config.get('CONSUMER', 'bootstrap.servers'),
    'group.id': config.get('CONSUMER', 'group.id'),
    'auto.offset.reset': config.get('CONSUMER', 'auto.offset.reset')
}

print("Configuration du Consumer...")
c = Consumer(consumer_config)


# Configurer le Producer
producer_config = {
    'bootstrap.servers': config.get('PRODUCER', 'bootstrap.servers')
}

print("Configuration du Producer...")
p = Producer(producer_config)

# Au début, lisez le délai d'attente de la configuration:
MAX_WAIT_TIME = int(config.get('CONSUMER', 'max_wait_time', fallback=10))  # fallback est le délai d'attente par défaut

# Récupére la liste des types événements:
event_types = config.get('CLASSIFIERS', 'event_types').split(',')
categories = config.get('CLASSIFIERS', 'categories').split(',')
severities = config.get('CLASSIFIERS', 'severities').split(',')


# Initialisation des données
X_pool = []
y_pool = []

# Initialisez le vectorizer
vectorizer = TfidfVectorizer(max_features=1000)

def convert_to_vector(data_point):
    vector = vectorizer.transform([data_point]).toarray()
    return vector[0]


def build_sample_text(max_messages = 100):
    
    # Générer un nouveau nom de groupe de consommateurs
    consumer_group = f"KafkaLogEnricher_{random.randint(1, 10000)}"  # Remplacez ceci par votre base de nom de groupe de consommateurs
    consumer_config = {
        'bootstrap.servers': config.get('CONSUMER', 'bootstrap.servers'),
        'group.id': consumer_group,
        'auto.offset.reset': config.get('CONSUMER', 'auto.offset.reset')
    }

    c = Consumer(consumer_config)
    
    topic_name = config.get('CONSUMER', 'topic')
    c.subscribe([topic_name])
    
    sample_texts = []    

    for _ in tqdm(range(max_messages), desc="Récupération des messages", ncols=100):  # ncols détermine la largeur de la barre de progression
        msg = c.poll(1.0)
        if msg:
            try:
                msg_content = json.loads(msg.value().decode('utf-8'))
                message = msg_content.get('message', 'No Content')
                if message:
                    sample_texts.append(message)
            except UnicodeDecodeError:
                #print("Erreur lors du décodage du message:", msg.value())
                continue
            
    return sample_texts


def fetch_initial_training_data(topic_name):

    # Générer un nouveau nom de groupe de consommateurs
    consumer_group = f"KafkaLogEnricher_{random.randint(1, 10000)}"  # Remplacez ceci par votre base de nom de groupe de consommateurs
    consumer_config = {
        'bootstrap.servers': config.get('CONSUMER', 'bootstrap.servers'),
        'group.id': consumer_group,
        'auto.offset.reset': config.get('CONSUMER', 'auto.offset.reset')
    }

    c = Consumer(consumer_config)

    c.subscribe([topic_name])

    training_data = []
    labels = []

    # Initialisation de la barre de progression
    pbar = tqdm(desc="Récupération des messages", ncols=100, unit=" messages")

    while True:
        msg = c.poll(1.0)
        if msg is None:
            break  # No more messages to read
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        try:
            msg_content = json.loads(msg.value().decode('utf-8'))
            log = msg_content.get('log', 'No Content')
            if log:
                training_data.append(log)
                combined_label = f"{msg_content.get('severity', 'INFO')}_{msg_content.get('event_type', 'Useless')}_{msg_content.get('category', 'Uncategorized')}"
                labels.append(combined_label)
        except UnicodeDecodeError:
            print("Erreur lors du décodage du message:", msg.value())

        # Mettre à jour la barre de progression
        pbar.update(1)

    pbar.close()

    vectorized_data = vectorizer.fit_transform(training_data).toarray()
    return vectorized_data, labels



print("Initialisation de l'application Flask...")
app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    event_types = config.get('CLASSIFIERS', 'event_types').split(',')
    categories = config.get('CLASSIFIERS', 'categories').split(',')
    severities = config.get('CLASSIFIERS', 'severities').split(',')
    return render_template('index.html', event_types=event_types, categories=categories, severities=severities)


def save_message(message_content):
    """
    Sauvegarde le message après la catégorisation.
    """
    output_topic = config.get('PRODUCER', 'output_topic')
    # Convert the dictionary to a JSON string
    json_msg = json.dumps(message_content)
    p.produce(output_topic, value=json_msg)


def categorize_message(message, msg_content):
    if message == 'No Content':
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Useless'
        msg_content['category'] = 'Uncategorized'
        return True  # Recherchez un autre message à catégoriser

    # Catégorisation pour la chaîne spécifique
    # vcenter-pau vsan-health-main - - - }, 'hostRebuildCapacity': 0, 'minSpaceRequiredForVsanOp': 16324541546496, 'enforceCapResrvSpace': 0
    specific_string = "minSpaceRequiredForVsanOp"
    if specific_string in message:
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'Performance and Resources'
        msg_content['category'] = 'Hardware Infrastructure'
        return True  # Recherchez un autre message à catégoriser
    # Request user: ws-arcgis.gfield@axione.fr, Service: GField_Console/MANAGER_READONLY_GALWAY/FeatureServer
    specific_string = "Request user"
    if specific_string in message:
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Authentication and Authorization'
        msg_content['category'] = 'Application & Middleware'
        return True  # Recherchez un autre message à catégoriser
    
    # <14>Sep 6 15:11:37 vma-pprdck-30 consul[1216]: 2023-09-06T15:11:37.706+0200 [DEBUG] agent: Check status updated: check=groot_ppr-tcp status=passing
    specific_string = "Check status updated"
    if specific_string in message:
        msg_content['severity'] = 'DEBUG'
        msg_content['event_type'] = 'Heartbeat'
        msg_content['category'] = 'Application & Middleware'
        return True  # Recherchez un autre message à catégoriser
    
    # <167>Sep 7 07:40:19 vma-prdadm-64 slapd[1722022]: conn=14162247 op=0 BIND dn="cn=app-rt,ou=applications,ou=users,dc=axione,dc=fr" mech=SIMPLE ssf=0
    pattern = re.compile(r'.*slapd.*(BIND|ACCEPT|SRCH|RESULT|UNBIND|closed).*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Authentication and Authorization'
        msg_content['category'] = 'Application & Middleware'
        return True  # Recherchez un autre message à catégoriser
    
    # <167>Sep 7 07:40:20 vma-prdadm-64 slapd[1722022]: <= mdb_equality_candidates: (loginRT) not indexed
    pattern = re.compile(r'.*slapd.*mdb_equality_candidates.*not indexed')
    if pattern.search(message):
        msg_content['severity'] = 'ERROR'
        msg_content['event_type'] = 'Authentication and Authorization'
        msg_content['category'] = 'Application & Middleware'
        return True  # Recherchez un autre message à catégoriser
    
    # <167>Sep 7 07:40:20 vma-prdadm-64 slapd[1722022]: <= mdb_equality_candidates: (loginRT) not indexed
    pattern = re.compile(r'.*pdns_recursor.*(answer|question).*')
    if pattern.search(message):
        msg_content['severity'] = 'DEBUG'
        msg_content['event_type'] = 'Network Communication'
        msg_content['category'] = 'Application & Middleware'
        return True  # Recherchez un autre message à catégoriser

    # <167>Sep 7 07:40:20 vma-prdadm-64 slapd[1722022]: <= mdb_equality_candidates: (loginRT) not indexed
    pattern = re.compile(r'.*snoopy.*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'User Interactions'
        msg_content['category'] = 'Application & Middleware'
        return True  # Recherchez un autre message à catégoriser

    # Si aucune condition n'est satisfaite, retournez False
    return False



def enrich_message(msg_content, prediction):
    """
    Ajoute des métadonnées supplémentaires basées sur la prédiction.

    Args:
    - msg_content (dict): le contenu original du message
    - prediction (array-like): la prédiction retournée par le modèle

    Returns:
    - dict: le message enrichi
    """

        # Scinde le message sur chaque underscore
    parts = prediction[0].split('_')

    # Assurez-vous qu'il y a exactement trois parties (pour severity, event_type, et category)
    if len(parts) == 3:
        severity, event_type, category = parts

        # Ajoute les composantes au msg_content
        msg_content['severity'] = severity
        msg_content['event_type'] = event_type
        msg_content['category'] = category

    # Sinon, vous pourriez vouloir ajouter une gestion d'erreurs ou une logique supplémentaire
    else:
        print("Erreur : le format du message n'est pas ce à quoi on s'attendait.")

    return msg_content



@app.route('/get_message', methods=['GET'])
def get_message():
    elapsed_time = 0
    topic_name = config.get('CONSUMER', 'topic')
    c.subscribe([topic_name])  # Subscribe once during setup
    while elapsed_time < MAX_WAIT_TIME:
        msg = c.poll(1.0)
        if msg:
            # Décoder le message et charger le JSON
            msg_content = json.loads(msg.value().decode('utf-8'))
            # Extraire la valeur associée à la clé "message"
            message = msg_content.get('message', 'No Content')  # Retourne une chaîne vide si la clé "message" n'existe pas
            msg_content['message'] = message

            if ACTIVE_LEARNING_ENABLED:
                message_vector = convert_to_vector(message)
                prediction = learner.predict([message_vector])
                # Si vous n'êtes pas sûr à 100% de la prédiction, demandez une annotation
                max_prob = np.max(learner.predict_proba([message_vector])[0])
                predicted_msg_content = enrich_message(msg_content, prediction) 
                print(f"{predicted_msg_content['message']}")
                print(f"    Severity : {predicted_msg_content['severity']}")
                print(f"    Event Type : {predicted_msg_content['event_type']}")
                print(f"    Category : {predicted_msg_content['category']}")
                print("    Taux de confiance : {:.2f}%".format(max_prob * 100))

                #print(predicted_msg_content)
                #print(msg_content)
                if max_prob < 0.55:
                    # Appel de la fonction de catégorisation
                    if categorize_message(message, msg_content):
                        save_message(msg_content)
                        print("---- Regexp Categorized")
                        print(f"{predicted_msg_content['message']}")
                        print(f"    Severity : {msg_content['severity']} vs {predicted_msg_content['severity']}")
                        print(f"    Event Type :  {msg_content['event_type']} vs {predicted_msg_content['event_type']}")
                        print(f"    Category :  {msg_content['category']} vs {predicted_msg_content['category']}")
                        print("    Taux de confiance : {:.2f}%".format(max_prob * 100))
                        msg_content['max_probability'] = "{:.2f}%".format(max_prob)
                        continue  # Recherchez un autre message à catégoriser

                    return message
                else:
                    # Sauvegarder le message dans le topic "enriched"
                    print("---- AI Categorized")
                    print(f"{predicted_msg_content['message']}")
                    print(f"    Severity : {predicted_msg_content['severity']}")
                    print(f"    Event Type : {predicted_msg_content['event_type']}")
                    print(f"    Category : {predicted_msg_content['category']}")
                    print("    Taux de confiance : {:.2f}%".format(max_prob * 100))
                    save_message(predicted_msg_content)
                    return '', 204  # No Content
            else:
                # Appel de la fonction de catégorisation
                if categorize_message(message, msg_content):
                    save_message(msg_content)
                    continue  # Recherchez un autre message à catégoriser

                # Si l'active learning est désactivé, retournez directement le message sans vérification.
                return message
        elapsed_time += 1

    return '', 204  # No Content

def teach_to_learner(enriched_msg):
    message_vector = convert_to_vector(enriched_msg["log"])
    
    # Combinez les labels. Cette étape dépend de votre cas d'utilisation.
    combined_label = f"{enriched_msg['severity']}_{enriched_msg['event_type']}_{enriched_msg['category']}"
    
    learner.teach([message_vector], [combined_label])

    dump(learner, 'learner_model.pkl')


@app.route('/send', methods=['POST'])
def send():
    log = request.form['log']
    severity = request.form['severity']
    event_type = request.form['event_type']
    category = request.form['category']
    enriched_msg = {
        "log": log,
        "severity": severity,
        "event_type": event_type,
        "category": category
    }
    output_topic = config.get('PRODUCER', 'output_topic')
    
    if ACTIVE_LEARNING_ENABLED:
        teach_to_learner(enriched_msg)

    # Convert the dictionary to a JSON string
    json_msg = json.dumps(enriched_msg)
    p.produce(output_topic, value=json_msg)
    return "Success", 200

if __name__ == '__main__':
    # Pour désactiver l'Active Learning, décommentez la ligne suivante :
    #ACTIVE_LEARNING_ENABLED = False

    if ACTIVE_LEARNING_ENABLED:
        print("Récupération des textes d'échantillon pour l'entraînement du vectorizer...")
        sample_texts = build_sample_text(max_messages = 10000)
        
        # Utilisation de la fonction
        print("Récupération des données d'entraînement initiales...")
        initial_training_data, initial_training_labels = fetch_initial_training_data(config.get('PRODUCER', 'output_topic'))
        
        # Combine sample_texts et initial_training_data pour l'entraînement du vectorizer
        print("Entraînement du vectorizer avec les textes d'échantillon et les données d'entraînement initiales...")
        all_texts = sample_texts + [log for log in initial_training_data]
        all_texts = [str(text) for text in all_texts]
        vectorizer.fit(all_texts)

        # Chargez le modèle si déjà existant
        print("Chargement ou initialisation du modèle ActiveLearner...")
        try:
            learner = load('learner_model.pkl')
            print("Modèle chargé avec succès.")
        except:
            # Si pas trouvé, créez un nouveau
            # Initialisez votre modèle et l'apprenant actif
            print("Aucun modèle préexistant trouvé. Initialisation d'un nouveau modèle...")
            learner = ActiveLearner(
                estimator=RandomForestClassifier(),
                X_training=initial_training_data,  # Vos données d'entraînement initiales converties en vecteurs
                y_training=initial_training_labels  # Vos labels initiaux
            )

    print("Lancement de l'application Flask...")
    app.run(debug=True)
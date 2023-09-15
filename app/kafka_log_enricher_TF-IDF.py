import numpy as np
from modAL.models import ActiveLearner
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import configparser
from flask import Flask, render_template, request
from confluent_kafka import Consumer, Producer
from joblib import dump, load
from tqdm import tqdm
import atexit
import random
from messages_utils import categorize_message, save_message, enrich_message

@atexit.register
def shutdown():    
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
    'bootstrap.servers': config.get('ENRICHED', 'bootstrap.servers')
}

print("Configuration du Producer...")
p = Producer(producer_config)

output_topic = config.get('ENRICHED', 'topic')

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


def teach_to_learner(enriched_msg):
    message_vector = convert_to_vector(enriched_msg["message"])
    
    # Combinez les labels. Cette étape dépend de votre cas d'utilisation.
    combined_label = f"{enriched_msg['severity']}_{enriched_msg['event_type']}_{enriched_msg['category']}"
    
    learner.teach([message_vector], [combined_label])

    dump(learner, 'learner_model_TD-IDF.pkl')



print("Initialisation de l'application Flask...")
app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    event_types = config.get('CLASSIFIERS', 'event_types').split(',')
    categories = config.get('CLASSIFIERS', 'categories').split(',')
    severities = config.get('CLASSIFIERS', 'severities').split(',')
    return render_template('index.html', event_types=event_types, categories=categories, severities=severities)


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
            # Extraire la valeur associée à la clé "message" ou "log". Sinon renvoi 'No Content'
            message = msg_content.get('message') or msg_content.get('log') or 'No Content'
            hostname = msg_content.get('hostname') or 'No Hostname'
            container_name = msg_content.get('container_name') or 'No Container Name'
            msg_content['message'] = message

            if ACTIVE_LEARNING_ENABLED:
                try:
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

                    if max_prob < 0.95:
                        # Appel de la fonction de catégorisation
                        if categorize_message(message, msg_content):
                            save_message(msg_content, p, output_topic)
                            if ACTIVE_LEARNING_ENABLED:
                                try:
                                    teach_to_learner(msg_content)
                                except:
                                    print("Le modèle n'est pas encore entrainé")
                            print("=> Message Regexp Categorized")
                            msg_content['max_probability'] = "{:.2f}%".format(max_prob)
                            continue  # Recherchez un autre message à catégoriser

                        return f"{hostname}, {container_name}, {message}"
                    else:
                        # Sauvegarder le message dans le topic "enriched"
                        print("=> Message AI Categorized")
                        save_message(predicted_msg_content, p, output_topic)
                        if ACTIVE_LEARNING_ENABLED:
                            try:
                                teach_to_learner(predicted_msg_content)
                            except:
                                print("Le modèle n'est pas encore entrainé")
                        return '', 204  # No Content
                except:
                    # Appel de la fonction de catégorisation
                    if categorize_message(message, msg_content):
                        save_message(msg_content, p, output_topic)
                        if ACTIVE_LEARNING_ENABLED:
                            try:
                                teach_to_learner(msg_content)
                            except:
                                print("Le modèle n'esty pas encore entrainé")
                        continue  # Recherchez un autre message à catégoriser

                    # Si l'active learning est désactivé, retournez directement le message sans vérification.
                    return f"{hostname}, {container_name}, {message}"
            else:
                # Appel de la fonction de catégorisation
                if categorize_message(message, msg_content):
                    save_message(msg_content, p, output_topic)
                    if ACTIVE_LEARNING_ENABLED:
                        try:
                            teach_to_learner(msg_content)
                        except:
                            print("Le modèle n'esty pas encore entrainé")
                    continue  # Recherchez un autre message à catégoriser

                # Si l'active learning est désactivé, retournez directement le message sans vérification.
                return f"{hostname}, {container_name}, {message}"
        elapsed_time += 1

    return '', 204  # No Content

@app.route('/send', methods=['POST'])
def send():
    #output_topic = config.get('ENRICHED', 'topic')

    log = request.form['log']
    severity = request.form['severity']
    event_type = request.form['event_type']
    category = request.form['category']
    enriched_msg = {
        "message": log,
        "severity": severity,
        "event_type": event_type,
        "category": category
    }
    
    
    if ACTIVE_LEARNING_ENABLED:
        try:
            teach_to_learner(enriched_msg)
        except:
            print("Le modèle n'est pas encore entrainé")
    #print(f"output_topic : {output_topic}, {enriched_msg}")
    # Convert the dictionary to a JSON string
    save_message(enriched_msg, p, output_topic)
    return "Success", 200


if __name__ == '__main__':
    # Pour désactiver l'Active Learning, décommentez la ligne suivante :
    #ACTIVE_LEARNING_ENABLED = False

    if ACTIVE_LEARNING_ENABLED:
        initial_training_data = []
        initial_training_labels = []
        
        # Utilisation de la fonction
        print("Récupération des données d'entraînement initiales...")
        try:
            initial_training_data, initial_training_labels = fetch_initial_training_data(output_topic)

            print("Récupération des textes d'échantillon pour l'entraînement du vectorizer...")
            sample_texts = build_sample_text(max_messages=10000)
            
            # Combine sample_texts et initial_training_data pour l'entraînement du vectorizer
            print("Entraînement du vectorizer avec les textes d'échantillon et les données d'entraînement initiales...")
            all_texts = sample_texts + [log for log in initial_training_data]
            all_texts = [str(text) for text in all_texts]
            vectorizer.fit(all_texts)
        except Exception as e:
            print(f"Aucune donnée d'entrainement disponible...le topic '{output_topic}' est vide. Erreur : {e}")
        
        # Chargez le modèle si déjà existant
        print("Chargement ou initialisation du modèle ActiveLearner...")
        try:
            learner = load('learner_model_TD-IDF.pkl')
            print("Modèle chargé avec succès.")
        except FileNotFoundError:
            print("Aucun modèle préexistant trouvé. Initialisation d'un nouveau modèle...")
            if len(initial_training_data) > 0 and len(initial_training_labels) > 0:
                initial_training_data = [str(doc) for doc in initial_training_data]
                X_initial_training = vectorizer.transform(initial_training_data)
                learner = ActiveLearner(
                    estimator=RandomForestClassifier(),
                    X_training=X_initial_training,
                    y_training=initial_training_labels
                )
            else:
                print("Données d'entraînement insuffisantes pour initialiser l'ActiveLearner.")


    print("Lancement de l'application Flask...")
    app.run(debug=True)

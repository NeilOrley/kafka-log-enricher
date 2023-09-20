import numpy as np
from modAL.models import ActiveLearner
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import configparser
from flask import Flask, render_template, request, jsonify
from confluent_kafka import Consumer, Producer
from joblib import load
import atexit
import random
from step_one_utils import *

@atexit.register
def shutdown():    
    c.close()
    p.flush()


model_path = "./models/learner_model_TD-IDF.pkl"


# Lire la configuration
print("Chargement de la configuration...")
config = configparser.ConfigParser()
config.read('config.ini')

# Variable globale pour activer/désactiver l'Active Learning
ACTIVE_LEARNING_ENABLED = config.get('GLOBAL', 'active_learning_enables')

# Configurer le Consumer
consumer_config = {
    'bootstrap.servers': config.get('CONSUMER', 'bootstrap.servers'),
    'group.id': config.get('CONSUMER', 'group.id'),
    'auto.offset.reset': config.get('CONSUMER', 'auto.offset.reset')
}

print("Configuration initiale du Consumer...")
c = Consumer(consumer_config)

# Configurer le Producer
producer_config = {
    'bootstrap.servers': config.get('OUTPUT', 'bootstrap.servers')
}

print("Configuration initiale du Producer...")
p = Producer(producer_config)

output_topic = config.get('OUTPUT', 'topic')

# Au début, lisez le délai d'attente de la configuration:
MAX_WAIT_TIME = int(config.get('CONSUMER', 'max_wait_time', fallback=10))  # fallback est le délai d'attente par défaut



# Initialisation des données
X_pool = []
y_pool = []

# Initialisez le vectorizer
print("Initialisation du vectorizer...")
vectorizer = TfidfVectorizer(max_features=1000)

print("Initialisation de l'application Flask...")
app = Flask(__name__, template_folder='../templates')

@app.route("/get_classifier_keys", methods=["GET"])
def get_classifier_keys():
    return jsonify(list(config['CLASSIFIERS'].keys()))

@app.route("/get_classifiers", methods=["GET"])
def get_classifiers():
    classifier_values = {key: config.get('CLASSIFIERS', key).split(',') for key in config['CLASSIFIERS'].keys()}
    return jsonify(classifier_values)

@app.route('/')
def index():
    # Récupération des clés de la section CLASSIFIERS et leur conversion en listes
    classifier_values = {key: config.get('CLASSIFIERS', key).split(',') for key in config['CLASSIFIERS'].keys()}
    # Retour du template en utilisant le déballage du dictionnaire pour les arguments
    return render_template('index.html', **classifier_values)

@app.route('/get_message', methods=['GET'])
def get_message():
    elapsed_time = 0
    # Générer un nouveau nom de groupe de consommateurs
    consumer_group = f"KafkaLogEnricher_{random.randint(1, 10000)}"  # Remplacez ceci par votre base de nom de groupe de consommateurs
    consumer_config = {
        'bootstrap.servers': config.get('CONSUMER', 'bootstrap.servers'),
        'group.id': consumer_group,
        'auto.offset.reset': config.get('CONSUMER', 'auto.offset.reset')
    }

    c = Consumer(consumer_config)

    topic_name = config.get('CONSUMER', 'topic')
    c.subscribe([topic_name])  # Subscribe once during setup

    while elapsed_time < MAX_WAIT_TIME:
        msg = c.poll(1.0)
        if msg:
            # Décoder le message et charger le JSON
            msg_content = json.loads(msg.value().decode('utf-8'))
            # Extraire la valeur associée à la clé "message" ou "log". Sinon renvoi 'No Content'
            message = msg_content.get('message') or msg_content.get('log') or 'No Content'
            msg_content['message'] = message

            if ACTIVE_LEARNING_ENABLED:
                try:
                    message_vector = convert_to_vector(vectorizer, message)
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
                            save_message(msg_content, p, producer_config, output_topic)
                            if ACTIVE_LEARNING_ENABLED:
                                try:
                                    teach_to_learner(msg_content, vectorizer, learner, model_path)
                                except:
                                    print("Le modèle n'est pas encore entrainé")
                            print("=> Message Regexp Categorized")
                            msg_content['max_probability'] = "{:.2f}%".format(max_prob)
                            continue  # Recherchez un autre message à catégoriser

                        return f"{message}"
                    else:
                        
                        # Appel de la fonction de catégorisation
                        if categorize_message(message, msg_content):
                            save_message(msg_content, p, producer_config, output_topic)
                            if ACTIVE_LEARNING_ENABLED:
                                try:
                                    teach_to_learner(msg_content, vectorizer, learner, model_path)
                                except:
                                    print("Le modèle n'est pas encore entrainé")
                            print("=> Message Regexp Categorized")
                            msg_content['max_probability'] = "{:.2f}%".format(max_prob)
                            continue  # Recherchez un autre message à catégoriser
                        else:
                            # Sauvegarder le message dans le topic "enriched"
                            print("=> Message AI Categorized")
                            save_message(predicted_msg_content, p, producer_config, output_topic)
                            if ACTIVE_LEARNING_ENABLED:
                                try:
                                    teach_to_learner(predicted_msg_content, vectorizer, learner, model_path)
                                except:
                                    print("Le modèle n'est pas encore entrainé")
                        return '', 204  # No Content
                except:
                    # Appel de la fonction de catégorisation
                    if categorize_message(message, msg_content):
                        save_message(msg_content, p, producer_config, output_topic)
                        if ACTIVE_LEARNING_ENABLED:
                            try:
                                teach_to_learner(msg_content, vectorizer, learner, model_path)
                            except:
                                print("Le modèle n'esty pas encore entrainé")
                        continue  # Recherchez un autre message à catégoriser

                    # Si l'active learning est désactivé, retournez directement le message sans vérification.
                    return f"{message}"
            else:
                # Appel de la fonction de catégorisation
                if categorize_message(message, msg_content):
                    save_message(msg_content, p, producer_config, output_topic)
                    if ACTIVE_LEARNING_ENABLED:
                        try:
                            teach_to_learner(msg_content, vectorizer, learner, model_path)
                        except:
                            print("Le modèle n'esty pas encore entrainé")
                    continue  # Recherchez un autre message à catégoriser

                # Si l'active learning est désactivé, retournez directement le message sans vérification.
                return f"{message}"
        elapsed_time += 1

    c.close()  # Fermer le consumer
    
    return '', 204  # No Content

@app.route('/send', methods=['POST'])
def send():

    message = request.form['message']

    # Récupérez la section CLASSIFIERS du fichier de configuration
    classifier_keys = config['CLASSIFIERS'].keys()

    # Construire le dictionnaire enriched_msg dynamiquement
    enriched_msg = {"message": message}
    for key in classifier_keys:
        enriched_msg[key] = request.form[key]
    
    
    if ACTIVE_LEARNING_ENABLED:
        try:
            teach_to_learner(enriched_msg, vectorizer, learner, model_path)
        except:
            print("Le modèle n'est pas encore entrainé")

    # Convert the dictionary to a JSON string
    save_message(enriched_msg, p, producer_config, output_topic)
    return "Success", 200


if __name__ == '__main__':

    if ACTIVE_LEARNING_ENABLED:
        initial_training_data = []
        initial_training_labels = []
        
        # Utilisation de la fonction
        print("Récupération des données d'entraînement initiales...")
        try:
            initial_training_data, initial_training_labels = fetch_initial_training_data(config, vectorizer, output_topic)

            print("Récupération des textes d'échantillon pour l'entraînement du vectorizer...")
            sample_texts = build_sample_text(config, max_messages=10000)
            
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
            learner = load(model_path)
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

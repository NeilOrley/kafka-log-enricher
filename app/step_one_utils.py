import re
import json
from confluent_kafka import Producer, Consumer
from tqdm import tqdm
import random
from joblib import dump
import os


def _delivery_report(err, msg):
    """ Indiqué si la livraison du message a réussi. Appelé une fois pour chaque message produit. """
    if err is not None:
        print(f'Erreur de livraison du message: {err}')
    else:
        print(f'Message envoyé au topic "{msg.topic()}" [partition {msg.partition()}] à l\'offset {msg.offset()}')


def convert_to_vector(vectorizer, data_point):
    vector = vectorizer.transform([data_point]).toarray()
    return vector[0]


def build_sample_text(config, max_messages = 100):
    
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
            
    c.close()  # Fermer le consumer

    return sample_texts


def fetch_initial_training_data(config, vectorizer, topic_name):

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
            log = msg_content.get('log') or msg_content.get('message') or 'No Content'
            if log:
                training_data.append(log)
                combined_label = f"{msg_content.get('severity', 'INFO')}_{msg_content.get('event_type', 'Useless')}_{msg_content.get('category', 'Uncategorized')}"
                labels.append(combined_label)
        except UnicodeDecodeError:
            print("Erreur lors du décodage du message:", msg.value())

        # Mettre à jour la barre de progression
        pbar.update(1)

    pbar.close()

    c.close()  # Fermer le consumer

    vectorized_data = vectorizer.fit_transform(training_data).toarray()
    return vectorized_data, labels


def save_message(message_content, p, producer_config, output_topic):
    """
    Sauvegarde le message après la catégorisation.
    """
    print("Configuration du Producer...")
    p = Producer(producer_config)

    # Convert the dictionary to a JSON string
    json_msg = json.dumps(message_content)
    p.produce(output_topic, value=json_msg, callback=_delivery_report)
    # Assurez-vous que tous les messages en attente sont bien envoyés.
    p.flush()
    

def enrich_message(msg_content, prediction):

    # Scinde le message prédit sur chaque underscore
    # il devrait etre sous la forme <severity>_<event_type>_<category>
    parts = prediction[0].split('_')

    # Vérifie qu'il y a exactement trois parties (pour severity, event_type, et category)
    if len(parts) == 3:
        severity, event_type, category = parts

        # Ajoute les composantes au msg_content
        msg_content['severity'] = severity
        msg_content['event_type'] = event_type
        msg_content['category'] = category

    else:
        print("Erreur : le format du message n'est pas ce à quoi on s'attendait.")

    return msg_content


def teach_to_learner(enriched_msg, vectorizer, learner, model_path):
    message_vector = convert_to_vector(vectorizer, enriched_msg["message"])
    
    # Combinez les labels. Cette étape dépend de votre cas d'utilisation.
    combined_label = f"{enriched_msg['severity']}_{enriched_msg['event_type']}_{enriched_msg['category']}"
    
    learner.teach([message_vector], [combined_label])

    dump(learner, model_path)


def categorize_message(message, msg_content):
    nom_fichier = os.path.basename(__file__)
    print(f"To categorize the message using a REGEXP you need to define them in {nom_fichier}...")
    
    if message == 'No Content':
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'None'
        msg_content['category'] = 'Other'
        return True  # Recherchez un autre message à catégoriser
    
    # Catégorisation des messages OK de Traefik
    pattern = re.compile(r'.*"OriginStatus":(2|3)...*RequestHost.*RequestMethod.*RequestPath.*RequestPort.*RequestProtocol.*RequestScheme.*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Middleware'
        return True  # Recherchez un autre message à catégoriser

    # Catégorisation des messages WARNING de Traefik
    pattern = re.compile(r'.*"OriginStatus":4...*RequestHost.*RequestMethod.*RequestPath.*RequestPort.*RequestProtocol.*RequestScheme.*')
    if pattern.search(message):
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Middleware'
        return True  # Recherchez un autre message à catégoriser
    
    # Catégorisation des messages WARNING de Traefik
    pattern = re.compile(r'.*"OriginStatus":5...*RequestHost.*RequestMethod.*RequestPath.*RequestPort.*RequestProtocol.*RequestScheme.*')
    if pattern.search(message):
        msg_content['severity'] = 'ERROR'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Middleware'
        return True  # Recherchez un autre message à catégoriser
    
    return False

    # Catégorisation pour la chaîne spécifique
    # vcenter-pau vsan-health-main - - - }, 'hostRebuildCapacity': 0, 'minSpaceRequiredForVsanOp': 16324541546496, 'enforceCapResrvSpace': 0
    specific_string = "minSpaceRequiredForVsanOp"
    if specific_string in message:
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'Performance'
        msg_content['category'] = 'Hardware Infrastructure'
        return True  # Recherchez un autre message à catégoriser
    
    # Request user: ws-arcgis.gfield@axione.fr, Service: GField_Console/MANAGER_READONLY_GALWAY/FeatureServer
    specific_string = "Request user"
    if specific_string in message:
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Application'
        return True  # Recherchez un autre message à catégoriser
    
    # <14>Sep 6 15:11:37 vma-pprdck-30 consul[1216]: 2023-09-06T15:11:37.706+0200 [DEBUG] agent: Check status updated: check=groot_ppr-tcp status=passing
    specific_string = "Check status updated"
    if specific_string in message:
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Heartbeat'
        msg_content['category'] = 'Monitoring & Logging'
        return True  # Recherchez un autre message à catégoriser
    
    # <166>Sep 8 14:26:56 vma-prdscr-21 httpd-smart[38231] - - - [2023-09-08T14:26:56+0200] 193 10.1.80.231:80 "GET /smart/ HTTP/1.1" 200 5163 "-" "Consul Health Check"
    specific_string = "Consul Health Check"
    if specific_string in message:
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Heartbeat'
        msg_content['category'] = 'Monitoring & Logging'
        return True  # Recherchez un autre message à catégoriser
    
    # Catégorisation des messages WARNING de Traefik
    pattern = re.compile(r'.*vcenter.*"dnsmasq.*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Network Message'
        msg_content['category'] = 'Hardware Infrastructure'
        return True  # Recherchez un autre message à catégoriser
    
    # Catégorisation des messages WARNING de Traefik
    pattern = re.compile(r'.*vcenter.*ERROR.*')
    if pattern.search(message):
        msg_content['severity'] = 'ERROR'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Hardware Infrastructure'
        return True  # Recherchez un autre message à catégoriser

    # Catégorisation des messages WARNING de Traefik
    pattern = re.compile(r'.*vcenter.*WARN.*')
    if pattern.search(message):
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Hardware Infrastructure'
        return True  # Recherchez un autre message à catégoriser
    
    # Catégorisation des messages WARNING de Traefik
    pattern = re.compile(r'.*vcenter.*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Hardware Infrastructure'
        return True  # Recherchez un autre message à catégoriser    
    
    # <167>Sep 7 07:40:19 vma-prdadm-64 slapd[1722022]: conn=14162247 op=0 BIND dn="cn=app-rt,ou=applications,ou=users,dc=axione,dc=fr" mech=SIMPLE ssf=0
    pattern = re.compile(r'.*slapd.*(BIND|ACCEPT|SRCH|RESULT|UNBIND|closed|be_modify|syncrep|slap_queue_csn|TLS established).*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'App Events'
        msg_content['category'] = 'Security System'
        return True  # Recherchez un autre message à catégoriser
    
    # <167>Sep 7 07:40:20 vma-prdadm-64 slapd[1722022]: <= mdb_equality_candidates: (loginRT) not indexed
    pattern = re.compile(r'.*slapd.*mdb_equality_candidates.*not indexed')
    if pattern.search(message):
        msg_content['severity'] = 'ERROR'
        msg_content['event_type'] = 'App Events'
        msg_content['category'] = 'Security System'
        return True  # Recherchez un autre message à catégoriser
    
    pattern =re.compile(r'.*WARN.*logstash.outputs.elasticsearch.*')
    if pattern.search(message):
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'App Events'
        msg_content['category'] = 'Monitoring & Logging'
        return True  # Recherchez un autre message à catégoriser

    # <167>Sep 7 07:40:20 vma-prdadm-64 slapd[1722022]: <= mdb_equality_candidates: (loginRT) not indexed
    pattern = re.compile(r'.*pdns_recursor.*(answer|question).*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Network Message'
        msg_content['category'] = 'Middleware'
        return True  # Recherchez un autre message à catégoriser

    # horus-agent .* successfully 
    pattern = re.compile(r'.consul.*(Check socket connection failed|Check is now critical).*')
    if pattern.search(message):
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Monitoring & Logging'
        return True  # Recherchez un autre message à catégoriser

    # horus-agent .* successfully 
    pattern = re.compile(r'.*(result|prometheus_push|snmpreq|poll|api).go.*(metric_count|poll|success|NoSuchObject|nil value).*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Monitoring & Logging'
        return True  # Recherchez un autre message à catégoriser
    
    # horus-agent .* successfully 
    pattern = re.compile(r'.*(ping|result|prometheus_push|snmpreq|api).go.*(yet|timeout|empty|failed).*')
    if pattern.search(message):
        msg_content['severity'] = 'WARNING'
        msg_content['event_type'] = 'Apps Events'
        msg_content['category'] = 'Monitoring & Logging'
        return True  # Recherchez un autre message à catégoriser
    
    # Snoopy et Amavis
    pattern = re.compile(r'.*(snoopy|amavis).*')
    if pattern.search(message):
        msg_content['severity'] = 'INFO'
        msg_content['event_type'] = 'Security'
        msg_content['category'] = 'Security System'
        return True  # Recherchez un autre message à catégoriser

    # Si aucune condition n'est satisfaite => False
    return False

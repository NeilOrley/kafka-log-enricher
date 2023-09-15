import re
import json


def save_message(message_content, p, output_topic):
    """
    Sauvegarde le message après la catégorisation.
    """
    # Convert the dictionary to a JSON string
    json_msg = json.dumps(message_content)
    p.produce(output_topic, value=json_msg)
    

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

    # Si aucune condition n'est satisfaite => False
    return False
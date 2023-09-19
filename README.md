# Kafka Log Enricher (kafka_log_enricher_TF-IDF.py)

Une interface web permettant d'extraire des messages d'un topic Kafka spécifique, d'afficher ces messages et de proposer un enrichissement avec des informations supplémentaires. Les messages enrichis sont ensuite renvoyés dans un autre topic Kafka.

## Pipeline de fonctionnement

### Classification manuelle : kafka_log_enricher_TF-IDF.py

Catégorisation manuelle : Au tout début il est nécessaire de désactiver l'active learning pour permettre au modèle de commencer son apprentissage.

  ```bash
    ACTIVE_LEARNING_ENABLED = False
  ```

Apprentissage Actif : Le script utilise l'apprentissage actif pour aider à catégoriser les messages. Lorsqu'un message est reçu, si le modèle est assez sûr de sa prédiction (avec une probabilité supérieure à 95 %), il étiquette automatiquement le message. Sinon, il sollicite une intervention humaine pour l'étiquetage.

  ```bash
    #ACTIVE_LEARNING_ENABLED = False
  ```

### Entrainement du modèle : models/train_xxxxx_model_BERT.py

Entrainement du modèle : Ce script consomme des messages de Kafka, contenant des textes et leurs catégories associées, puis entraîne un modèle de classification de texte DistilBert sur ces données, évaluant et sauvegardant ensuite le modèle entraîné pour des utilisations futures dans kafka_log_enricher_BERT.py

### Classification automatique : kafka_log_enricher_BERT.py (non testé pour le moment)

Apprentissage non supervisé : Le script utilise une méthode de transformation basée sur DistilBert et un réseau de neurones simple pour classer les embeddings de BERT. Il étiquette ainsi automatiquement le message.
Cela nécessite un volume conséquent de données correctement anotées.

## Fonctionnalités

- Lire les messages d'un topic Kafka en temps réel.
- Afficher le contenu du champ "log" de messages formatés en JSON.
- Proposer d'enrichir chaque message avec trois informations : sévérité, type d'événement et la Catégorie générale en composant
- Renvoyer le message enrichi dans un topic Kafka défini.

## Prérequis

- Le topic Kafka "ENRICHED" doit disposer d'au moins un millier de messages catégorisés pour que l'active learning puisse être pertinent. 
- Le message dans le topic Kafka doit avoir le format suivant :

   ```bash
    {
        "log": "my_log_message",
        "my_key": "my_value",
        ...
    }
   ```

   ou

      ```bash
    {
        "message": "my_log_message",
        "my_key": "my_value",
        ...
    }
   ```

- Python 3.x
- Flask
- confluent-kafka
- configparser

## Installation

1. **Clonez le répertoire**:

   ```bash
   git clone https://github.com/NeilOrley/kafka-log-enricher.git
   cd kafka-log-enricher
   ```

2. **Configuration**:

   Mettez à jour le fichier `config.ini` avec les informations appropriées pour vos serveurs Kafka, groupes et topics.

3. **Activez l'environnement virtuel**:

   - Naviguez vers le dossier du projet et créer un environnement virtuel :
    ```bash
    cd kafka-log-enricher
    python -m venv venv
    ```

   - Sur Windows:
     ```bash
     .\venv\Scripts\Activate
     ```

   - Sur macOS ou Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Installez les dépendances**:

   - Sur Windows:
   ```bash
   .\venv\Scripts\python.exe -m pip install --upgrade pip
   pip install -r .\app\requirements.txt
   ```

   - Sur macOS ou Linux:
   ```bash
   pip install -r app/requirements.txt
   ```

5. **Exécution**:

   ```bash
   python kafka_log_enricher.py
   ```

## Utilisation

1. Exécutez l'application:

   ```bash
   python kafka_log_enricher.py
   ```

2. Naviguez vers `http://localhost:5000` dans votre navigateur pour accéder à l'interface utilisateur.

3. Les logs de Kafka seront automatiquement récupérés du topic spécifié. Enrichissez chaque log en sélectionnant sa gravité et son type d'événement, puis cliquez sur "Send" pour envoyer le log enrichi vers le topic Kafka de sortie.


## Configuration

La configuration de l'application est gérée par le fichier `config.ini`. Ce fichier contient des sections pour le Consumer Kafka et le Producer Kafka, ainsi que des paramètres spécifiques comme les noms des topics.

Exemple de configuration :

```ini
[CONSUMER]
bootstrap.servers = your_broker
group.id = your_group
auto.offset.reset = earliest
topic = your_topic

[PRODUCER]
bootstrap.servers = your_broker
output_topic = your_output_topic

[CLASSIFIERS]
severities = INFO,DEBUG,WARNING,ERROR,CRITICAL
event_types = Heartbeat,State change,Authentication and Authorization,Operations on files and apps,Network Communication,Security and Anomalies,Performance and Resources,User Interactions,Useless
categories = Hardware Infrastructure,Software Infrastructure,Connectivity and Security,Datas,Application & Middleware,Monitoring & Logging,Automation & CI/CD,Uncategorized
```

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contribution

Les contributions sont les bienvenues ! Assurez-vous de tester vos modifications avant de soumettre une pull request.
Si vous souhaitez contribuer à ce projet, veuillez suivre les étapes suivantes :

1. **Fork** le projet.
2. Créez votre **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Poussez dans la **Branch** (`git push origin feature/AmazingFeature`).
5. Ouvrez une **Pull Request**.

## Contact

Pour toute question ou feedback, n'hésitez pas à contacter [Neil Orley](https://github.com/NeilOrley) ou à ouvrir une issue sur ce dépôt.


> ---
>
> _Note : Ce texte a été généré avec l'aide de ChatGPT, un modèle linguistique développé par OpenAI._

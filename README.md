# Kafka Log Enricher

Une interface web permettant d'extraire des messages d'un topic Kafka spécifique, d'afficher ces messages et de proposer un enrichissement avec des informations supplémentaires. Les messages enrichis sont ensuite renvoyés dans un autre topic Kafka.

## Fonctionnalités

- Lire les messages d'un topic Kafka en temps réel.
- Afficher le contenu du champ "log" de messages formatés en JSON.
- Proposer d'enrichir chaque message avec deux informations :
  - Sévérité: "debug", "info", "warning", "error", "critical"
  - Type d'événement: "Message d'information", "Message de donnée", "Changement de status", "Erreur/Alerte"
- Renvoyer le message enrichi dans un topic Kafka défini.

## Installation

1. **Clonez le répertoire**:

   ```bash
   git clone https://github.com/NeilOrley/KafkaLogEnricher.git
   cd KafkaLogEnricher
   ```

2. **Configuration**:

   Mettez à jour le fichier `config.ini` avec les informations appropriées pour vos serveurs Kafka, groupes et topics.

3. **Installez les dépendances**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Exécution**:

   ```bash
   python kafka_log_enricher.py
   ```

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
```

## Contribuer

Si vous souhaitez contribuer à ce projet, veuillez suivre les étapes suivantes :

1. **Fork** le projet.
2. Créez votre **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Poussez dans la **Branch** (`git push origin feature/AmazingFeature`).
5. Ouvrez une **Pull Request**.

# Kafka Log Enricher

Une interface web permettant d'extraire des messages d'un topic Kafka spécifique, d'afficher ces messages et de proposer un enrichissement avec des informations supplémentaires. Les messages enrichis sont ensuite renvoyés dans un autre topic Kafka.

## Fonctionnalités

- Lire les messages d'un topic Kafka en temps réel.
- Afficher le contenu du champ "log" de messages formatés en JSON.
- Proposer d'enrichir chaque message avec deux informations :
  - Sévérité: "info", "warning", "error", "critical"
  - Type d'événement: 
    - Heartbeat :
      Vérification régulière d'un état

    - Changement d'état (State change) :
      Démarrage et arrêt      
      Redémarrage
      Changements d'état des interfaces

    - Authentification et Autorisation (Authentication and Authorization ou AuthN and AuthZ) :
      Tentatives de connexion réussies / échouées
      Changements de mot de passe
      Modifications des rôles et des permissions

    - Opérations sur les fichiers et applications (Operations on files and apps):
      Création, modification, suppression de fichiers ou de dossiers
      Échecs d'accès aux fichiers
      Transferts de fichiers
      Démarrage et arrêt des services ou applications
      Mises à jour des logiciels
      Erreurs d'exécution des applications

    - Réseau (Network Communication) :
      Connexions établies et terminées
      Erreurs de communication et performance réseau
      Tentatives de connexions suspectes
      Modifications de la configuration réseau

    - Sécurité et Anomalies (Security and Anomalies) :
      Détections d'intrusion
      Violations de politiques de sécurité
      Anomalies détectées par des outils comme les IDS/IPS

    - Performance et ressources (Performance and Resources) :
      Alerte d'espace disque faible
      Échec de sauvegarde
      Seuils d'utilisation dépassés

    - Interactions Utilisateur (User Interactions):
      Commandes exécutées
      Modifications de configuration
      Sessions utilisateur

    - Useless:
      Trucs qui servent a rien

  - Catégorisation générale en composant : 
    - Infrastructure Matérielle (Hardware Infrastructure) :
      Serveurs: Peuvent être physiques ou virtuels (comme les VMs).
      Stockage: Disques durs, SSD, solutions de stockage en réseau (NAS, SAN), etc.
      Réseau: Routeurs, commutateurs, pare-feu, load balancers, etc.

    - Infrastructure Logicielle (Software Infrastructure) :
      Système d'Exploitation: Par exemple, Linux, Windows Server, etc.
      Virtualisation: Solutions comme VMware, Hyper-V, KVM, etc.
      Conteneurs: Technologies comme Docker, Kubernetes, etc.

    - Connectivité et Sécurité (Connectivity and Security) :
      Proxy & Reverse Proxy: Nginx, Apache, HAProxy, etc.
      CDN & transitaires : ArborNetwork, etc.
      VPN & Solutions d'accès distant : Pour la connectivité sécurisée.
      Solutions de sécurité: Vault, IDS/IPS, WAF, etc.

    - Données (Datas) :
      Bases de Données: SQL (comme MySQL, PostgreSQL) et NoSQL (comme MongoDB, Cassandra).
      Caches: Redis, Memcached, etc.
      Systèmes de fichiers distribués: Hadoop HDFS, GlusterFS, etc.

    - Application & Middleware (Application & Middleware) :
      Serveurs d'application: Tomcat, JBoss, etc.
      Middleware: RabbitMQ, Kafka, etc.
      Framework de développement: Express.js, Django, Spring Boot, etc.
      Serveurs Web: Apache, Nginx, etc.
      Frameworks Frontend: React, Angular, Vue.js, etc.

    - Monitoring & Logging :
      Outils de surveillance: Nagios, Prometheus, etc.
      Solutions de logging: ELK stack (Elasticsearch, Logstash, Kibana), Graylog, etc.

    - Automatisation & CI/CD (Automation & CI/CD) :
      Outils d'automatisation: Jenkins, GitLab CI, Terraform, etc.
      Gestion de configuration: Ansible, Salt, etc.

    - Uncategorized:
      Pas besoin de catégoriser
      
- Renvoyer le message enrichi dans un topic Kafka défini.

## Prérequis
- Le message dans le topic Kafka doit avoir le format suivant :

   ```bash
    {
        "log": "my_log_message",
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

## Contribuer

Si vous souhaitez contribuer à ce projet, veuillez suivre les étapes suivantes :

1. **Fork** le projet.
2. Créez votre **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Poussez dans la **Branch** (`git push origin feature/AmazingFeature`).
5. Ouvrez une **Pull Request**.
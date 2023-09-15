- **Sévérité:** 
  - "info"
  - "warning"
  - "error"
  - "critical"

- **Type d'événement:**

- **Heartbeat:**
  - Vérification régulière d'un état

- **Changement d'état (State change):**
  - Démarrage et arrêt      
  - Redémarrage
  - Changements d'état des interfaces

- **Authentification et Autorisation (Authentication and Authorization ou AuthN and AuthZ):**
  - Tentatives de connexion réussies / échouées
  - Changements de mot de passe
  - Modifications des rôles et des permissions

- **Opérations sur les fichiers et applications (Operations on files and apps):**
  - Création, modification, suppression de fichiers ou de dossiers
  - Échecs d'accès aux fichiers
  - Transferts de fichiers
  - Démarrage et arrêt des services ou applications
  - Mises à jour des logiciels
  - Erreurs d'exécution des applications

- **Réseau (Network Communication):**
  - Connexions établies et terminées
  - Erreurs de communication et performance réseau
  - Tentatives de connexions suspectes
  - Modifications de la configuration réseau

- **Sécurité et Anomalies (Security and Anomalies):**
  - Détections d'intrusion
  - Violations de politiques de sécurité
  - Anomalies détectées par des outils comme les IDS/IPS

- **Performance et ressources (Performance and Resources):**
  - Alerte d'espace disque faible
  - Échec de sauvegarde
  - Seuils d'utilisation dépassés

- **Interactions Utilisateur (User Interactions):**
  - Commandes exécutées
  - Modifications de configuration
  - Sessions utilisateur

- **Useless:**
  - Trucs qui servent a rien

- **Catégorisation générale en composant:** 

- **Infrastructure Matérielle (Hardware Infrastructure):**
  - Serveurs: Peuvent être physiques ou virtuels (comme les VMs).
  - Stockage: Disques durs, SSD, solutions de stockage en réseau (NAS, SAN), etc.
  - Réseau: Routeurs, commutateurs, pare-feu, load balancers, etc.

- **Infrastructure Logicielle (Software Infrastructure):**
  - Système d'Exploitation: Par exemple, Linux, Windows Server, etc.
  - Virtualisation: Solutions comme VMware, Hyper-V, KVM, etc.
  - Conteneurs: Technologies comme Docker, Kubernetes, etc.

- **Connectivité et Sécurité (Connectivity and Security):**
  - Proxy & Reverse Proxy: Nginx, Apache, HAProxy, etc.
  - CDN & transitaires : ArborNetwork, etc.
  - VPN & Solutions d'accès distant : Pour la connectivité sécurisée.
  - Solutions de sécurité: Vault, IDS/IPS, WAF, etc.

- **Données (Datas):**
  - Bases de Données: SQL (comme MySQL, PostgreSQL) et NoSQL (comme MongoDB, Cassandra).
  - Caches: Redis, Memcached, etc.
  - Systèmes de fichiers distribués: Hadoop HDFS, GlusterFS, etc.

- **Application & Middleware (Application & Middleware):**
  - Serveurs d'application: Tomcat, JBoss, etc.
  - Middleware: RabbitMQ, Kafka, etc.
  - Framework de développement: Express.js, Django, Spring Boot, etc.
  - Serveurs Web: Apache, Nginx, etc.
  - Frameworks Frontend: React, Angular, Vue.js, etc.

- **Monitoring & Logging:**
  - Outils de surveillance: Nagios, Prometheus, etc.
  - Solutions de logging: ELK stack (Elasticsearch, Logstash, Kibana), Graylog, etc.

- **Automatisation & CI/CD (Automation & CI/CD):**
  - Outils d'automatisation: Jenkins, GitLab CI, Terraform, etc.
  - Gestion de configuration: Ansible, Salt, etc.

- **Uncategorized:**
  - Pas besoin de catégoriser

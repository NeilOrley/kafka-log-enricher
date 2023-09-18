## Guide des Niveaux de Sévérité (Severity) des messages de Log

### 1. INFO
- **Description** : Messages d'information générale destinés à informer l'utilisateur ou l'administrateur d'événements normaux. Par exemple, un système qui démarre ou une opération qui se déroule comme prévu.

### 2. WARNING
- **Description** : Alertes concernant des événements qui ne sont pas nécessairement des erreurs, mais qui pourraient le devenir ou pourraient avoir un impact négatif. Par exemple, un espace disque faible ou une tentative de connexion suspecte.

### 3. ERROR
- **Description** : Indique qu'une erreur s'est produite et qu'une action n'a pas été exécutée comme prévu. Cela ne signifie pas nécessairement que le système est en panne, mais qu'un problème doit être résolu. Par exemple, une erreur de base de données ou un fichier manquant.

### 4. CRITICAL
- **Description** : Signale des événements graves qui peuvent entraîner l'arrêt du système ou une défaillance majeure. Il s'agit d'alertes de la plus haute importance qui nécessitent une intervention immédiate. Par exemple, une défaillance matérielle imminente ou une violation de sécurité grave.



## Classification des "Event type" des messages de Log

### 1. Heartbeat
- **Description** : Il s'agit d'un signal périodique généré par un logiciel ou un matériel pour indiquer qu'il fonctionne normalement. L'absence d'un battement de cœur peut indiquer un problème ou une défaillance.

### 2. State Change
- **Description** : Cet événement est déclenché lorsqu'un système, une application ou un composant passe d'un état à un autre, comme de "en marche" à "arrêté", ou de "connecté" à "déconnecté".

### 3. Operations on files
- **Description** : Référence toute action effectuée sur un fichier, par exemple la création, la modification, la suppression ou la lecture.

### 4. Apps Events
- **Description** : Il s'agit d'événements générés par des applications spécifiques, comme le lancement d'une application, une mise à jour, une erreur d'exécution, etc.

### 5. Network Message
- **Description** : Ce sont des messages liés à la communication réseau, tels que des demandes de connexion, des déconnexions, des erreurs de transmission, etc.

### 6. Security
- **Description** : Ces événements concernent la sécurité. Ils peuvent inclure des tentatives de connexion infructueuses, des détections d'intrusion, des modifications non autorisées ou tout autre incident lié à la sécurité.

### 7. Performance
- **Description** : Evénements liés à la performance du système ou de l'application. Ils peuvent indiquer des temps de réponse lents, des ressources système élevées, des goulots d'étranglement, etc.

### 8. User Interactions
- **Description** : Ces messages sont générés en réponse à des actions effectuées par les utilisateurs, comme des clics de souris, des entrées de clavier, des ouvertures de session, etc.

### 9. None
- **Description** : Si un message de log ne correspond à aucune des classifications ci-dessus, il peut être catégorisé comme "None". Cela peut être utilisé pour des logs qui ne sont pas encore classifiés ou qui ne sont pas jugés pertinents pour une classification spécifique.



## Guide de Classification des "Category" des messages de Log

### 1. Hardware Infrastructure
- **Description** : Cette catégorie concerne tous les événements relatifs au matériel physique d'un système, tels que les serveurs, les unités de stockage, les processeurs, les cartes mères, etc. Les problèmes de surchauffe, de défaillance matérielle ou d'utilisation élevée des ressources entrent dans cette catégorie.

### 2. OS/VM & Dockers
- **Description** : Référence aux événements concernant les systèmes d'exploitation, les machines virtuelles (VM) et les conteneurs Docker. Cela peut inclure des mises à jour du système, des erreurs d'OS, des opérations de VM, et les activités liées à Docker.

### 3. Network Element
- **Description** : Cette catégorie englobe les événements liés aux éléments de réseau comme les routeurs, les commutateurs, les pare-feux, etc. Les activités comme la configuration, les modifications, les déconnexions, et les erreurs réseau sont classées ici.

### 4. Security System
- **Description** : Les événements concernant les systèmes de sécurité, tels que les solutions antivirus, les pare-feux, les systèmes de détection d'intrusion, et autres. Cela peut inclure des alertes, des mises à jour, des détections, etc.

### 5. Datas
- **Description** : Relatif à toutes les opérations et événements liés aux données. Que ce soit la base de données, les opérations CRUD (Création, Lecture, Mise à jour, Suppression), les sauvegardes, les erreurs de base de données, etc.

### 6. Application
- **Description** : Les événements générés par des applications spécifiques. Cela peut inclure des erreurs d'application, des lancements, des fermetures, des mises à jour, etc.

### 7. Middleware
- **Description** : Concernant les logiciels intermédiaires qui facilitent l'intégration de diverses applications et processus. Les messages liés aux serveurs d'applications, aux systèmes de messagerie, aux bus de services d'entreprise (ESB) entrent dans cette catégorie.

### 8. Monitoring & Logging
- **Description** : Les événements associés aux systèmes et outils de surveillance et de journalisation. Cela peut concerner les alertes de surveillance, les échecs de journalisation, les configurations, etc.

### 9. Other
- **Description** : Pour les messages de log qui ne correspondent à aucune des classifications ci-dessus ou qui sont atypiques. Cette catégorie sert de fourre-tout pour tout ce qui n'est pas couvert par les autres catégories.


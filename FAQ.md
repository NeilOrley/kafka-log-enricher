> **Avertissement** : Le contenu suivant a été généré en utilisant ChatGPT, un modèle linguistique d'OpenAI.

## Qu'est ce que l'Apprentissage actif

L'apprentissage actif est une méthode d'apprentissage supervisé où le modèle interroge l'humain pour obtenir des étiquettes pour les données sur lesquelles il est le moins sûr. 

### Comment intégrer l'apprentissage actif ? :

1. **Flux de Données** : Utiliser le flux de données venant de Kafka. Ces données peuvent être enrichies à travers la méthode `/send` par exemple.

2. **Initialisation du Modèle** : 
   - Utiliser un petit ensemble de données étiquetées pour entraîner un modèle de base.
   - Utiliser ce modèle pour prédire les étiquettes des données non étiquetées.

3. **Sélection pour Etiquetage** :
   - Parmi les données non étiquetées, choisir celles pour lesquelles le modèle est le moins sûr (par exemple, où la probabilité de prédiction est proche de 0,5 pour une classification binaire).
   - Proposer ces exemples à l'utilisateur pour étiquetage.

4. **Mise à jour du Modèle** :
   - Comme les données sont étiquetées par l'utilisateur (en utilisant la méthode `/send`), ajoutez-les à l'ensemble d'entraînement.
   - Périodiquement (après N nouveaux échantillons étiquetés ou à intervalles réguliers), réentraîner le modèle avec ces nouvelles données.

5. **Automatisation** :
   - Automatiser ce processus pour que le système continue à sélectionner de manière proactive les exemples dont il a besoin pour l'étiquetage.

## Comment organiser le pipeline ?

1. **Collecte des messages de log** :
   - Depuis Kafka : utiliser des outils tels que Kafka Connect pour récupérer les messages de logs en temps réel et les stocker dans un espace de stockage temporaire pour le traitement.
   - Depuis Loki : extraire des messages de log de Loki via son API.

2. **Annotation manuelle** : 
   - Avoir une interface (un dashboard ou une application web) où un humain peut lire et annoter chaque message de log : criticité ("info", "warning", "error", "critical"), événement ("Message dinformation", "Message de donnée", "Changement de status", "Erreur/Alerte").
   - Cette étape doit être aussi automatisée que possible pour faciliter la tâche à l'annotateur. Plus la tâche est facile, plus les annotations seront de haute qualité en peu de temps.

3. **Prétraitement des données** :
   - Les messages de logs doivent être prétraités pour être utilisés comme entrée pour un modèle Keras. Cela peut inclure la tokenisation, la conversion en séquences, etc.

4. **Active Learning avec Keras** :
   - Avec le petit ensemble de données initialement annoté, entraînez un modèle de base en utilisant Keras.
   - Utiliser ce modèle pour prédire les labels des messages non annotés. 
   - Identifier les messages pour lesquels le modèle est le moins fiable (en utilisant l'entropie des prédictions comme mesure d'incertitude par exemple).
   - Présenter ces messages incertains à l'humain pour annotation.
   - Répéter le processus jusqu'à ce qu'un niveau satisfaisant de performance soit atteint.

5. **Intégration dans la stack** :
   - Une fois un modèle bien entrainé, l'intégrer pour classer automatiquement les nouveaux messages de log à partir de Kafka.
   - Créer un mécanisme de feedback où les erreurs de classification du modèle peuvent être corrigées manuellement et réinjectées dans le pipeline d'apprentissage.

6. **Controle** :
   - Mettre en place des mécanismes de contrôle de la qualité des annotations.


## Qu'est ce que la "conversion en séquence" ?

La conversion en séquences est une étape de prétraitement dans laquelle un texte est transformé en une séquence de nombres. Elle est souvent utilisée dans le contexte de l'apprentissage automatique, en particulier pour les tâches liées au traitement du langage naturel (NLP), afin de rendre le texte compatible avec les modèles qui s'attendent à des entrées numériques.

Voici une illustration simplifiée du processus de conversion en séquences :

1. **Tokenisation** : 
   - Le texte est divisé en unités plus petites, appelées "tokens". Ces tokens peuvent représenter des mots, des caractères, ou même des sous-mots (subwords).
   - Par exemple, la phrase "J'aime le NLP" pourrait être tokenisée en ["J'", "aime", "le", "NLP"].

2. **Création d'un vocabulaire** : 
   - Vous créez une liste de tous les tokens uniques présents dans l'ensemble de données.
   - À chaque token, vous associez un index numérique unique.
   - Par exemple, si votre vocabulaire est ["J'", "aime", "le", "NLP"], les indices pourraient être {0, 1, 2, 3} respectivement.

3. **Conversion des tokens en numéros** : 
   - Chaque token dans un texte est remplacé par son index numérique correspondant du vocabulaire.
   - La phrase "J'aime le NLP" serait transformée en [0, 1, 2, 3].

Les modèles de deep learning comme les réseaux de neurones récurrents (RNNs) ou les Transformers prennent en entrée ces séquences numériques pour traiter le texte. De plus, souvent, une étape supplémentaire consiste à utiliser des embeddings (comme Word2Vec ou GloVe) pour convertir ces indices numériques en vecteurs denses, ce qui offre une représentation plus riche et plus expressive des mots.

Dans le contexte de Keras, il existe des utilitaires comme `Tokenizer` qui peuvent faciliter la tokenisation et la conversion en séquences pour vous.

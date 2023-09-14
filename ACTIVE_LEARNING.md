## Apprentissage actif

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

### Considérations :

- **Interface Utilisateur** : L'efficacité de l'apprentissage actif dépend en grande partie de la facilité avec laquelle les utilisateurs peuvent étiqueter les données. 
    TODO : Rendre cette tâche la plus simple et la plus intuitive possible.
- **Stratégies de Sélection** : Il existe différentes méthodes pour sélectionner les données à étiqueter (par exemple, incertitude, marge, entropie, etc.). La méthode d'incertitude, où les données pour lesquels le modèle est le moins sûr sont sélectionnées, est la plus courante.
- **Efficacité** : S'il y a beaucoup de données, il se peut que le réentraînement complet du modèle à chaque fois soit inefficace. Dans ce cas, envisagez d'utiliser des techniques d'apprentissage en ligne ou des mises à jour partielles du modèle.

Il existe plusieurs bibliothèques Python qui facilitent l'apprentissage actif, comme `modAL` ou `libact`. 
Ces bibliothèques offrent des outils pour sélectionner les exemples à étiqueter, gérer les modèles et intégrer l'apprentissage actif dans vos flux de travail existants.
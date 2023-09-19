### Interprétation des Résultats de l'Entraînement du Modèle

**1. `eval_loss` (Perte à l'évaluation) :**
- C'est la perte (habituellement, la fonction de coût) calculée sur le jeu de données d'évaluation à la fin de chaque époque.
- **Valeur typique :** Un nombre entre 0 et 1 (mais peut varier).
- **Interprétation :** Plus cette valeur est faible, meilleure est la performance du modèle sur le jeu de données d'évaluation. Elle devrait idéalement diminuer au fil des époques.

**2. `eval_runtime` (Durée de l'évaluation) :**
- Le temps total (en secondes) nécessaire pour évaluer le modèle sur le jeu de données d'évaluation.
- **Interprétation :** Donne une idée de la rapidité d'évaluation du modèle. Si elle est trop longue, envisagez d'optimiser ou de réduire la taille du jeu de données d'évaluation.

**3. `eval_samples_per_second` (Échantillons évalués par seconde) :**
- Le nombre moyen d'échantillons du jeu de données d'évaluation traités chaque seconde.
- **Interprétation :** Indique l'efficacité du processus d'évaluation. Une valeur plus élevée signifie que le modèle évalue plus rapidement.

**4. `eval_steps_per_second` (Étapes d'évaluation par seconde) :**
- Le nombre moyen d'étapes d'évaluation effectuées chaque seconde.
- **Interprétation :** Semblable à `eval_samples_per_second` mais basé sur le nombre d'étapes plutôt que sur le nombre d'échantillons.

**5. `train_runtime` (Durée de l'entraînement) :**
- Le temps total (en secondes) nécessaire pour former le modèle pendant toutes les époques.
- **Interprétation :** Donne une idée de la durée totale de l'entraînement. Si elle est trop longue, envisagez d'optimiser ou de réduire la taille du jeu de données d'entraînement.

**6. `train_samples_per_second` (Échantillons formés par seconde) :**
- Le nombre moyen d'échantillons du jeu de données d'entraînement traités chaque seconde.
- **Interprétation :** Indique l'efficacité du processus d'entraînement. Une valeur plus élevée signifie que le modèle se forme plus rapidement.

**7. `accuracy` (Précision) :**
- Le pourcentage total d'échantillons classés correctement.
- **Valeur typique :** Entre 0 et 1 (ou 0% et 100%).
- **Interprétation :** Indique à quel point le modèle fait des prédictions correctes. Une valeur plus élevée est meilleure.

**8. `precision` (Précision) :**
- La précision est le rapport entre les vrais positifs et la somme des vrais positifs et des faux positifs. Elle mesure la capacité du modèle à ne pas étiqueter comme positif un échantillon négatif.
- **Valeur typique :** Entre 0 et 1.
- **Interprétation :** Une valeur plus élevée indique que le modèle fait moins de faux positifs.

**9. `recall` (Rappel) :**
- Le rappel est le rapport entre les vrais positifs et la somme des vrais positifs et des faux négatifs. Il mesure la capacité du modèle à trouver tous les échantillons positifs.
- **Valeur typique :** Entre 0 et 1.
- **Interprétation :** Une valeur plus élevée indique que le modèle fait moins de faux négatifs.

**10. `f1` (Score F1) :**
- Le score F1 est la moyenne harmonique de la précision et du rappel.
- **Valeur typique :** Entre 0 et 1.
- **Interprétation :** Le score F1 tente d'équilibrer la précision et le rappel. Une valeur élevée signifie que le modèle a une bonne précision et un bon rappel.

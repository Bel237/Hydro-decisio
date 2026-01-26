#donnees specifiques a Nkolbison Water SIAD


"""
Ce fichier est la 'Mémoire' du projet. 
C'est ici qu'on définit les critères demandés par le Professeur Tamo.
"""

def get_nkolbisson_context():
    return {
        "quartier": "Nkolbisson",
        "description": "Quartier périphérique de Yaoundé avec un relief accidenté.",
        
        # Définition des critères (Ce que le prof a demandé de décrire)
        "criteres": {
            "Coût": {
                "definition": "Somme des dépenses d'investissement (CAPEX) et d'exploitation (OPEX).",
                "details": "Pour Camwater: Frais de branchement + facturation au m3. Pour le Forage: Coût de réalisation + pompe + électricité."
            },
            "Disponibilité": {
                "definition": "Capacité du système à fournir de l'eau de manière continue.",
                "details": "Mesuré par le nombre d'heures de service par jour et la fréquence des coupures."
            },
            "Accessibilité": {
                "definition": "Facilité d'obtention de l'eau selon la distance et la configuration du terrain.",
                "details": "Distance au réseau existant ou profondeur de la nappe phréatique à Nkolbisson."
            }
        },

        # Valeurs réelles (Signaux) pour Nkolbisson (Notes de 1 à 10)
        "performances": {
            "camwater": {
                "nom": "Réseau CAMWATER",
                "cout": 7,          # Relativement abordable au branchement
                "disponibilite": 3,  # Très faible (coupures fréquentes à Nkolbisson)
                "accessibilite": 4   # Faible si on est loin de la conduite principale
            },
            "forage": {
                "nom": "Alimentation Autonome",
                "cout": 4,          # Très cher à construire (investissement lourd)
                "disponibilite": 9,  # Très élevée (l'eau est là 24h/24)
                "accessibilite": 8   # Élevée car le point d'eau est chez soi
            }
        }
    }
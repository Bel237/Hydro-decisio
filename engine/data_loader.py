# data_loader.py - Version améliorée avec plusieurs quartiers
"""
Base de données des zones d'étude pour le SIAD Hydraulique.
"""

def get_zone_context(zone_name="Nkolbisson"):
    """
    Retourne le contexte spécifique d'une zone d'étude.
    
    Args:
        zone_name (str): Nom de la zone/quartier
        
    Returns:
        dict: Contexte avec critères, performances et coordonnées
    """
    
    # Base de données des zones
    ZONES_DATABASE = {
        "Nkolbisson": {
            "quartier": "Nkolbisson",
            "ville": "Yaoundé",
            "secteur": "Yaoundé VII",
            "description": "Quartier périphérique de Yaoundé avec un relief accidenté et un accès limité au réseau d'eau.",
            "coordonnees": {
                "latitude": 3.8712,
                "longitude": 11.4538,
                "zoom": 14
            },
            
            # Définition des critères
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
                    "details": "Distance au réseau existant ou profondeur de la nappe phréatique."
                }
            },

            # Valeurs par défaut pour cette zone
            "performances_par_defaut": {
                "camwater": {
                    "nom": "Réseau CAMWATER",
                    "cout": 7,
                    "disponibilite": 3,
                    "accessibilite": 4
                },
                "forage": {
                    "nom": "Alimentation Autonome",
                    "cout": 4,
                    "disponibilite": 9,
                    "accessibilite": 8
                },
                "hybride": {
                    "nom": "Système Hybride",
                    "cout": 3,
                    "disponibilite": 10,
                    "accessibilite": 5
                }
            }
        },
        
        "Biyem-Assi": {
            "quartier": "Biyem-Assi",
            "ville": "Yaoundé",
            "secteur": "Yaoundé III",
            "description": "Quartier urbain dense avec un réseau d'eau partiellement développé.",
            "coordonnees": {
                "latitude": 3.8589,
                "longitude": 11.4934,
                "zoom": 14
            },
            "criteres": { ... },  # Tu peux copier et adapter les critères
            "performances_par_defaut": {
                "camwater": {"cout": 6, "disponibilite": 5, "accessibilite": 7},
                "forage": {"cout": 5, "disponibilite": 8, "accessibilite": 6},
                "hybride": {"cout": 4, "disponibilite": 9, "accessibilite": 5}
            }
        },
        
        "Mvog-Betsi": {
            "quartier": "Mvog-Betsi",
            "ville": "Yaoundé",
            "secteur": "Yaoundé I",
            "description": "Zone résidentielle moyenne avec accès variable au réseau.",
            "coordonnees": {
                "latitude": 3.8856,
                "longitude": 11.5117,
                "zoom": 14
            },
            "criteres": { ... },
            "performances_par_defaut": {
                "camwater": {"cout": 5, "disponibilite": 4, "accessibilite": 6},
                "forage": {"cout": 6, "disponibilite": 9, "accessibilite": 7},
                "hybride": {"cout": 4, "disponibilite": 8, "accessibilite": 6}
            }
        },
        
        "Autre": {
            "quartier": "Nouvelle Zone",
            "ville": "Ville à définir",
            "secteur": "Secteur à définir",
            "description": "Zone personnalisée - ajustez les paramètres ci-dessous.",
            "coordonnees": {
                "latitude": 3.8667,
                "longitude": 11.5167,
                "zoom": 12
            },
            "criteres": {
                "Coût": {
                    "definition": "Investissement et coûts opérationnels.",
                    "details": "À adapter selon le contexte local."
                },
                "Disponibilité": {
                    "definition": "Continuité du service d'eau.",
                    "details": "Évaluez la fiabilité du réseau local."
                },
                "Accessibilité": {
                    "definition": "Facilité d'accès à l'eau.",
                    "details": "Considérez la topographie et l'infrastructure."
                }
            },
            "performances_par_defaut": {
                "camwater": {"cout": 5, "disponibilite": 5, "accessibilite": 5},
                "forage": {"cout": 5, "disponibilite": 5, "accessibilite": 5},
                "hybride": {"cout": 5, "disponibilite": 5, "accessibilite": 5}
            }
        }
    }
    
    # Retourne la zone demandée ou Nkolbisson par défaut
    return ZONES_DATABASE.get(zone_name, ZONES_DATABASE["Nkolbisson"])


def get_available_zones():
    """Retourne la liste des zones disponibles"""
    return ["Nkolbisson", "Biyem-Assi", "Mvog-Betsi", "Autre"]


def save_custom_zone(zone_data):
    """
    Permet de sauvegarder une zone personnalisée (optionnel)
    Pourrait être utilisé avec une base de données
    """
    # À implémenter si besoin de sauvegarder des zones personnalisées
    pass
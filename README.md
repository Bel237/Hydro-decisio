# 💧 HYDRO-DECISIO | SIAD Hydraulique (Nkolbisson)

**HYDRO-DECISIO** est un Système d'Aide à la Décision (SIAD) expert conçu pour optimiser le choix d'approvisionnement en eau dans le quartier de Nkolbisson (Yaoundé VII). Il combine l'analyse mathématique multicritère (AHP) et des projections technico-financières réelles.

---

## 🚀 Fonctionnalités Clés

* **Analyse Multicritère (AHP) :** Pondération intelligente entre Coût, Disponibilité et Accessibilité via une interface intuitive.
* **Localisation GPS Interactive :** Sélection précise du point de projet sur une carte Folium avec capture des coordonnées en temps réel.
* **Expertise Photo :** Module d'upload multiple pour la documentation visuelle du terrain.
* **Projection ROI sur 10 ans :** Comparatif financier entre l'abonnement CAMWATER et l'investissement dans un forage autonome (CAPEX/OPEX).
* **Générateur de Rapport PDF :** Exportation d'un rapport d'expertise complet incluant les scores, les cartes, les graphiques financiers et les photos légendées.

---

## 🛠️ Installation et Lancement en Local

Suivez ces étapes pour faire tourner l'application sur votre machine :

### 1. Cloner le projet
```bash
git clone [https://github.com/BEL237/nkolbisson_water_siad.git](https://github.com/BEL237/nkolbisson_water_siad.git)
cd nkolbisson_water_siad ( naviguer vers le dossier du projet vers le projet)

```

### 2. Créer un environnement virtuel (Recommandé)

```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur Mac/Linux
source venv/bin/activate

```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt

```

### 4. Lancer l'application

```bash
streamlit run app.py

```

---

## 📂 Structure du Projet

* `app.py` : Point d'entrée principal (Interface Streamlit).
* `engine/ahp_logic.py` : Cœur mathématique pour le calcul des vecteurs propres et de la cohérence (CR).
* `assets/` : Logos et fichiers CSS personnalisés.
* `requirements.txt` : Liste des bibliothèques nécessaires au projet.

---

## 🧪 Méthodologie Utilisée

Le système repose sur la méthode **Analytic Hierarchy Process (AHP)**.

1. **Matrice de comparaison par paire** pour définir les priorités.
2. **Calcul de l'Indice de Cohérence** pour valider la logique du décideur.
3. **Agrégation des scores** techniques et financiers pour un verdict impartial.

---

## 👤 Auteur

**Nkolo** - *Développement SIAD & Expertise Hydraulique*

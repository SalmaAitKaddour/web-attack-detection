# Machine Learning for Web Attack Detection (OWASP A05:2025 - Injection)

Groupe 2 - Master Intelligence Artificielle et Cybersécurité, USMS Béni Mellal.
Train sur CSIC 2010 (filtré injection), test sur requêtes OWASP Juice Shop collectées en local.
Modèles : Logistic Regression (TF-IDF char n-grams), Random Forest, DistilBERT.

## Structure
- `data/` : jeux de données (non versionnés, voir `data/README.md`)
- `notebooks/` : exploration et expériences (un notebook par étape)
- `src/` : code réutilisable (prétraitement, features, modèles, évaluation)
- `lab/` : Juice Shop (Docker), générateurs de trafic, test live
- `serving/` : API FastAPI + Dockerfile
- `monitoring/` : scripts de suivi (scores, drift)
- `models/` : modèles entraînés (non versionnés)
- `reports/` : résultats, figures, rapport final
- `docs/` : proposition M1 et documents du projet

## Installation
```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Règles d'équipe
1. Ne jamais pousser sur `main` directement : une branche par tâche, puis Pull Request.
2. Le jeu de test Juice Shop n'est JAMAIS utilisé pour l'entraînement ni le réglage.
3. Aucune attaque hors du lab local isolé (Docker, localhost:3000).
4. Pas de données lourdes ni de modèles dans Git (voir `.gitignore`).

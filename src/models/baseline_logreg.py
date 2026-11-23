"""
baseline_logreg.py - Baseline : Régression logistique sur TF-IDF de n-grammes de caractères
+ quelques features manuelles (proposition, section 4).

Pourquoi des n-grammes de CARACTÈRES ?
  Une injection se reconnaît à de petits motifs ("' or", "--", "<scr", "union se").
  Les n-grammes de caractères capturent ces motifs sans tokenisation de mots, et
  restent robustes aux variantes (casse, encodage, espaces).

"""

from __future__ import annotations

import re

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.evaluation.metrics import (
    best_threshold, compute_metrics, format_report, plot_confusion_matrix, save_metrics,
)
from src.preprocessing.build_csic import OUT_DIR, REPORT_DIR, ROOT

# --- Paramètres (modifiables, notés ici pour la reproductibilité) -------------
NGRAM_RANGE = (2, 5)     # motifs de 2 à 5 caractères
MAX_FEATURES = 50_000    # on garde les 50 000 n-grammes les plus fréquents
C = 1.0                  # force de régularisation (petit C = modèle plus simple)
SEED = 42

# Caractères spéciaux comptés par la feature manuelle
_SPECIAL = re.compile(r"['\"`;<>()=%/\\*#|\-]")


def manual_features(texts) -> np.ndarray:
    """4 features numériques simples par requête (calculées sur le texte NORMALISÉ,
    donc de la même façon pour CSIC et Juice Shop)."""
    rows = []
    for t in texts:
        n = len(t)
        n_special = len(_SPECIAL.findall(t))
        rows.append([
            n,                          # longueur de la requête
            n_special,                  # nombre de caractères spéciaux
            n_special / n if n else 0,  # proportion de caractères spéciaux
            t.count("&") + 1,           # nombre approximatif de paramètres
        ])
    return np.array(rows, dtype=float)


class LogRegDetector:
    """Enchaîne : TF-IDF + features manuelles (standardisées) -> LogisticRegression."""

    def __init__(self):
        self.tfidf = TfidfVectorizer(
            analyzer="char", ngram_range=NGRAM_RANGE, max_features=MAX_FEATURES,
            sublinear_tf=True,  # atténue l'effet des n-grammes très répétés
        )
        self.scaler = StandardScaler()
        # class_weight="balanced" : compense le déséquilibre (≈ 28 % d'injections)
        self.clf = LogisticRegression(C=C, class_weight="balanced", max_iter=1000,
                                      random_state=SEED)

    def _features(self, texts, fit: bool):
        if fit:  # on APPREND le vocabulaire et l'échelle sur le train seulement
            X_tfidf = self.tfidf.fit_transform(texts)
            X_man = self.scaler.fit_transform(manual_features(texts))
        else:    # val / test : on applique sans réapprendre (pas de fuite d'information)
            X_tfidf = self.tfidf.transform(texts)
            X_man = self.scaler.transform(manual_features(texts))
        return hstack([X_tfidf, csr_matrix(X_man)]).tocsr()

    def fit(self, texts, y):
        self.clf.fit(self._features(texts, fit=True), y)
        return self

    def predict_proba(self, texts) -> np.ndarray:
        """Probabilité que la requête soit une injection."""
        return self.clf.predict_proba(self._features(texts, fit=False))[:, 1]

    def predict(self, texts, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(texts) >= threshold).astype(int)


def main():
    train = pd.read_csv(OUT_DIR / "train.csv")
    val = pd.read_csv(OUT_DIR / "val.csv")

    model = LogRegDetector().fit(train["text"], train["label"])

    # 1) Évaluation avec le seuil par défaut 0.5
    val_score = model.predict_proba(val["text"])
    m_default = compute_metrics(val["label"], (val_score >= 0.5).astype(int), val_score)
    print(format_report(m_default, "LogReg - validation CSIC (seuil 0.5)"))

    # 2) Seuil optimisé sur la validation (jamais sur Juice Shop !)
    best = best_threshold(val["label"], val_score)
    m_best = compute_metrics(val["label"], (val_score >= best["threshold"]).astype(int), val_score)
    print(format_report(m_best, f"LogReg - validation CSIC (seuil {best['threshold']:.3f})"))

    # 3) Sauvegardes (modèle -> models/, mesures + figure -> reports/)
    joblib.dump({"model": model, "threshold": best["threshold"]},
                ROOT / "models" / "logreg_baseline.joblib")
    save_metrics({"threshold_0.5": m_default, "threshold_best": {**m_best, **best}},
                 REPORT_DIR / "logreg_val_metrics.json")
    plot_confusion_matrix(m_best, "LogReg - validation",
                          REPORT_DIR / "figures" / "logreg_val_confusion.png")


if __name__ == "__main__":
    main()

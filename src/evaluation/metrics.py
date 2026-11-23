"""
metrics.py - Mesures d'évaluation COMMUNES aux trois modèles (LogReg, RF, DistilBERT).

Règle de la proposition : l'Accuracy n'est JAMAIS rapportée seule ; les mesures
prioritaires sont le Recall de la classe injection (label = 1) et le F1.

Convention : label 1 = injection (classe positive), label 0 = normal.
  TP : injection détectée          FN : injection MANQUÉE   (le pire cas)
  TN : normal laissé passer        FP : fausse alarme
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(y_true, y_pred, y_score=None) -> dict:
    """Retourne toutes les mesures dans un dictionnaire (facile à sauvegarder en JSON).

    y_true  : vraies étiquettes (0/1)
    y_pred  : étiquettes prédites (0/1)
    y_score : score/probabilité d'injection (optionnel) -> permet de calculer l'AUC
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # labels=[0, 1] force une matrice 2x2 même si une classe est absente
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    out = {
        "n": int(len(y_true)),
        # zero_division=0 : si le modèle ne prédit aucune injection, precision = 0 (pas d'erreur)
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        # taux de fausses alarmes = FP / (FP + TN)
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }
    if y_score is not None and len(np.unique(y_true)) == 2:
        out["roc_auc"] = float(roc_auc_score(y_true, y_score))
    return out


def format_report(metrics: dict, title: str = "") -> str:
    """Petit texte lisible pour les notebooks / logs."""
    lines = [f"=== {title} ===" if title else "=== Résultats ==="]
    lines.append(f"Precision (injection) : {metrics['precision']:.4f}")
    lines.append(f"Recall    (injection) : {metrics['recall']:.4f}   <- mesure prioritaire")
    lines.append(f"F1        (injection) : {metrics['f1']:.4f}")
    lines.append(f"Accuracy              : {metrics['accuracy']:.4f}   (jamais seule)")
    lines.append(f"Taux de fausses alarmes: {metrics['false_positive_rate']:.4f}")
    if "roc_auc" in metrics:
        lines.append(f"ROC-AUC               : {metrics['roc_auc']:.4f}")
    lines.append(
        f"Matrice : TN={metrics['tn']}  FP={metrics['fp']}  FN={metrics['fn']}  TP={metrics['tp']}"
    )
    return "\n".join(lines)


def best_threshold(y_true, y_score, min_recall: float = 0.0) -> dict:
    """Choisit le seuil de décision qui maximise le F1.

    IMPORTANT : à appeler sur la VALIDATION uniquement (jamais sur le test
    Juice Shop). Le seuil trouvé est ensuite figé et réutilisé tel quel.

    min_recall : si > 0, on ne considère que les seuils qui gardent au moins ce
                 Recall (utile quand rater une attaque coûte cher).
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    # precision/recall ont un point de plus que thresholds -> on l'enlève
    precision, recall = precision[:-1], recall[:-1]
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    f1 = np.where(recall >= min_recall, f1, -1.0)  # écarte les seuils trop laxistes
    i = int(np.argmax(f1))
    return {
        "threshold": float(thresholds[i]),
        "precision": float(precision[i]),
        "recall": float(recall[i]),
        "f1": float(f1[i]),
    }


def plot_confusion_matrix(metrics: dict, title: str = "Matrice de confusion", save_path=None):
    """Dessine la matrice de confusion (lignes = vrai, colonnes = prédit)."""
    import matplotlib.pyplot as plt  # import local : metrics.py reste utilisable sans matplotlib

    cm = np.array([[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]])
    fig, ax = plt.subplots(figsize=(4.2, 3.6))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], ["Normal (0)", "Injection (1)"])
    ax.set_yticks([0, 1], ["Normal (0)", "Injection (1)"])
    ax.set_xlabel("Prédit")
    ax.set_ylabel("Réel")
    ax.set_title(title)
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha="center", va="center",
                color="white" if v > cm.max() / 2 else "black", fontsize=13)
    fig.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    return fig


def save_metrics(metrics: dict, path) -> None:
    """Sauvegarde les mesures en JSON (ex. reports/logreg_val_metrics.json)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

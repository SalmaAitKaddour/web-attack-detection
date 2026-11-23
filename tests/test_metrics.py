"""Tests de metrics.py - lancer avec : pytest"""
import numpy as np
from src.evaluation.metrics import best_threshold, compute_metrics


def test_metrics_exemple_simple():
    y_true = [1, 1, 1, 1, 0, 0, 0, 0]
    y_pred = [1, 1, 1, 0, 0, 0, 0, 1]   # TP=3 FN=1 TN=3 FP=1
    m = compute_metrics(y_true, y_pred)
    assert (m["tp"], m["fn"], m["tn"], m["fp"]) == (3, 1, 3, 1)
    assert m["precision"] == 0.75 and m["recall"] == 0.75
    assert abs(m["f1"] - 0.75) < 1e-9 and m["accuracy"] == 0.75


def test_aucune_prediction_positive_ne_plante_pas():
    m = compute_metrics([1, 0, 1], [0, 0, 0])
    assert m["precision"] == 0.0 and m["recall"] == 0.0


def test_best_threshold_separe_parfaitement():
    y = np.array([0, 0, 1, 1])
    s = np.array([0.1, 0.2, 0.8, 0.9])
    assert best_threshold(y, s)["f1"] == 1.0

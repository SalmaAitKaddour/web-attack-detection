"""
build_csic.py - Construit le dataset d'entraînement à partir de CSIC 2010.


Entrée  : data/raw/csic2010/csic_database.csv
Sorties : data/processed/csic_clean.csv   (tout le jeu nettoyé)
          data/processed/train.csv        (80 %)
          data/processed/val.csv          (20 %)
          reports/csic_preprocessing_summary.json  (chiffres à citer dans le rapport)
          reports/csic_removed_anomalies_sample.csv (échantillon pour relecture manuelle)

Étapes (chacune compte les lignes avant/après pour qu'on puisse l'expliquer) :
  1. lecture + normalisation  -> colonne `text`
  2. filtre injection         -> on retire les anomalies qui ne sont pas des injections
  3. déduplication            -> sur le TEXTE normalisé (pas sur les 17 colonnes brutes)
  4. retrait des conflits     -> même texte étiqueté normal ET anormal = ambigu
  5. mélange + split 80/20 stratifié (random_state fixé = reproductible)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.preprocessing.normalize import injection_markers, normalize_request

SEED = 42            # même graine pour toute l'équipe -> mêmes résultats
VAL_SIZE = 0.20      # 80 % train / 20 % validation

ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "csic2010" / "csic_database.csv"
OUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"


def build(raw_csv: Path = RAW_CSV, out_dir: Path = OUT_DIR, report_dir: Path = REPORT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    summary: dict = {}

    # ---- 1. Lecture + normalisation --------------------------------------
    raw = pd.read_csv(raw_csv)
    summary["raw_rows"] = len(raw)
    summary["raw_normal"] = int((raw["classification"] == 0).sum())
    summary["raw_anomalous"] = int((raw["classification"] == 1).sum())

    df = pd.DataFrame(
        {
            # `text` = la seule feature d'entrée ; `label` = la cible (0/1)
            "text": [
                normalize_request(m, u, c)
                for m, u, c in zip(raw["Method"], raw["URL"], raw["content"])
            ],
            "label": raw["classification"].astype(int),
        }
    )

    # ---- 2. Filtre injection (anomalies uniquement) ----------------------
    # Les requêtes normales ne sont JAMAIS filtrées : même si elles contiennent
    # une apostrophe (ex. adresse), ce sont de bons "négatifs difficiles".
    df["markers"] = df["text"].map(lambda t: ",".join(injection_markers(t)))
    is_anomaly = df["label"] == 1
    has_marker = df["markers"] != ""
    removed = df[is_anomaly & ~has_marker]
    df = df[~is_anomaly | has_marker].copy()
    summary["removed_non_injection_anomalies"] = len(removed)
    summary["after_filter_rows"] = len(df)

    # échantillon (fixe) des anomalies écartées -> à relire à la main
    removed.sample(n=min(100, len(removed)), random_state=SEED)[["text"]].to_csv(
        report_dir / "csic_removed_anomalies_sample.csv", index=False
    )

    # ---- 3. Déduplication sur le texte normalisé -------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["text", "label"]).copy()
    summary["duplicates_removed"] = before - len(df)

    # ---- 4. Conflits : même texte, deux étiquettes -----------------------
    # keep=False marque TOUTES les copies ; on les supprime car on ne sait pas
    # quelle étiquette est correcte.
    conflict = df.duplicated(subset=["text"], keep=False)
    summary["conflicting_rows_removed"] = int(conflict.sum())
    df = df[~conflict].copy()

    # ---- 5. Mélange + split stratifié ------------------------------------
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    train, val = train_test_split(
        df, test_size=VAL_SIZE, stratify=df["label"], random_state=SEED, shuffle=True
    )

    cols = ["text", "label"]
    df[cols].to_csv(out_dir / "csic_clean.csv", index=False)
    train[cols].to_csv(out_dir / "train.csv", index=False)
    val[cols].to_csv(out_dir / "val.csv", index=False)

    for name, part in [("final", df), ("train", train), ("val", val)]:
        summary[f"{name}_rows"] = len(part)
        summary[f"{name}_normal"] = int((part["label"] == 0).sum())
        summary[f"{name}_injection"] = int((part["label"] == 1).sum())
        summary[f"{name}_injection_ratio"] = round(float(part["label"].mean()), 4)

    with open(report_dir / "csic_preprocessing_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


if __name__ == "__main__":
    for k, v in build().items():
        print(f"{k:35s} {v}")

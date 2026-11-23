import argparse
import csv
import glob
import json
import os
from collections import Counter
from urllib.parse import urlsplit

LOG_GLOB = "lab/juice_shop/logs/*.log"
OUT = "data/juiceshop_lab/raw_labeled.csv"
EXCLUDED_RUNS = ["test", "268ee2", "f28eec"]
FIELDS = ["id", "method", "path", "params", "body", "label", "scenario",
          "run", "status", "source"]


def read_logs(pattern):
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield name, json.loads(line)
                except json.JSONDecodeError:
                    yield name, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=LOG_GLOB)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--exclude", nargs="*", default=EXCLUDED_RUNS,
                    help="identifiants de lots (X-Run) à exclure")
    ap.add_argument("--keep-duplicates", action="store_true")
    args = ap.parse_args()

    n = Counter()
    rows, seen = [], set()

    for source, rec in read_logs(args.logs):
        n["lignes lues"] += 1
        if rec is None:
            n["lignes illisibles"] += 1
            continue
        if rec.get("label") not in ("0", "1"):
            n["sans étiquette (navigateur)"] += 1
            continue
        if rec.get("run") in args.exclude:
            n["lots exclus"] += 1
            continue

        u = urlsplit(rec.get("uri", ""))
        row = {
            "method": rec.get("method", ""),
            "path": u.path,
            "params": u.query,
            "body": rec.get("body", ""),
            "label": int(rec["label"]),
            "scenario": rec.get("scenario", ""),
            "run": rec.get("run", ""),
            "status": rec.get("status", ""),
            "source": source,
        }
        key = (row["method"], row["path"], row["params"], row["body"],
               row["label"])
        if not args.keep_duplicates:
            if key in seen:
                n["doublons exacts supprimés"] += 1
                continue
            seen.add(key)
        rows.append(row)

    if not rows:
        print("Aucune ligne retenue. Vérifie les chemins et les lots exclus.")
        for k, v in n.items():
            print(f"  {k:32} {v}")
        return

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, row in enumerate(rows):
            w.writerow({"id": i, **row})

    print("--- Bilan ---")
    for k, v in n.items():
        print(f"  {k:32} {v}")
    print(f"  {'LIGNES RETENUES':32} {len(rows)}  ->  {args.out}")
    print("\nPar étiquette :")
    for lab, c in sorted(Counter(r["label"] for r in rows).items()):
        print(f"  label {lab} : {c}")
    print("\nPar scénario :")
    for (lab, sc), c in sorted(Counter((r["label"], r["scenario"])
                                       for r in rows).items()):
        print(f"  label {lab}  {sc:24} {c}")
    print("\nPar lot :")
    for run, c in sorted(Counter(r["run"] for r in rows).items()):
        print(f"  {run:12} {c}")


if __name__ == "__main__":
    main()
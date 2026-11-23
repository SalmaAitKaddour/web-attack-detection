import argparse
import csv
import hashlib
import os
import random
from collections import Counter, defaultdict

SRC = "data/juiceshop_lab/raw_labeled.csv"
OUT = "data/juiceshop_lab/test_v1_draft.csv"
TEMPLATED = ["register", "login_valid", "login_wrong_password",
             "basket_add", "basket_view"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--cap", type=int, default=300,
                    help="max de lignes gardées par scénario « gabarit »")
    ap.add_argument("--capped", nargs="*", default=TEMPLATED,
                    help="scénarios dont on limite le nombre de lignes")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    with open(args.src, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    groups = defaultdict(list)
    for r in rows:
        groups[(r["label"], r["scenario"])].append(r)

    rng = random.Random(args.seed)
    kept = []
    for key in sorted(groups):
        g = groups[key]
        if key[1] in args.capped and len(g) > args.cap:
            g = rng.sample(g, args.cap)
        kept.extend(g)
    kept.sort(key=lambda r: int(r["id"]))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(kept)

    print(f"seed={args.seed}  cap={args.cap}")
    print(f"avant : {len(rows)} lignes   après : {len(kept)} lignes\n")
    print("label  scénario                  avant  après")
    after = Counter((r["label"], r["scenario"]) for r in kept)
    for key in sorted(groups):
        print(f"  {key[0]}    {key[1]:24} {len(groups[key]):5}  {after[key]:5}")
    print("\nPar étiquette (après) :")
    for lab, c in sorted(Counter(r["label"] for r in kept).items()):
        print(f"  label {lab} : {c}")
    with open(args.out, "rb") as f:
        print("\nsha256 :", hashlib.sha256(f.read()).hexdigest())
    print("fichier :", args.out)


if __name__ == "__main__":
    main()
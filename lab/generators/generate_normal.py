import argparse
import random
import time
import uuid
from collections import Counter

import requests

BASE = "http://127.0.0.1:8080"
RUN = uuid.uuid4().hex[:6]
TIMEOUT = 10

SEARCHES = [
    "apple", "juice", "banana", "lemon", "orange", "carrot", "melon",
    "Apple Juice", "GIFT CARD", "t-shirt", "mug", "sticker", "café",
    "o'brien juice", "kid's mug", "men's t-shirt", "l'orange", "what's new",
    "fruit & veg", "20% off", "50% juice", "juice - 1l", "fruit + veg",
    "apple, banana", "juice (1l)",
]

NAMES = ["salma", "youssef", "amine", "sara", "karim", "imane", "omar",
         "lina", "mehdi", "nora"]
PASSWORDS = ["Passw0rd!{i}", "Mon-Mot2Passe#{i}", "azerty_{i}!A",
             "It's-Mine{i}$", "P@ss w0rd {i}", "Résumé{i}&Co"]


def identity(i):
    name = random.choice(NAMES)
    sep = random.choice([".", "_", "+", ""])
    email = f"{name}{sep}{RUN}{i}@example.com"
    if random.random() < 0.3:
        email = email.capitalize()
    pwd = random.choice(PASSWORDS).format(i=i)
    return email, pwd


def random_query(words):
    w = random.choice(words)
    r = random.random()
    if r < 0.30:
        return w
    if r < 0.45:
        return f"{w} {random.choice(words)}"
    if r < 0.55:
        return w.capitalize()
    if r < 0.65:
        return f"{w}, {random.choice(words)}"
    if r < 0.75:
        return f"{random.choice([5, 10, 20, 50])}% {w}"
    if r < 0.85:
        return f"{w} & {random.choice(words)}"
    if r < 0.92:
        return f"{w}'s"
    return f"{w} {random.choice(['1l', '500ml', 'pack', 'new', 'cheap'])}"

stats = Counter()


def call(session, method, path, scenario, token=None, **kwargs):
    headers = {"X-Label": "0", "X-Scenario": scenario, "X-Run": RUN}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = session.request(method, BASE + path, headers=headers,
                            timeout=TIMEOUT, **kwargs)
        stats[(scenario, r.status_code)] += 1
        return r
    except requests.RequestException as e:
        stats[(scenario, "erreur")] += 1
        print("erreur réseau :", scenario, e)
        return None


def one_user(i):
    s = requests.Session()
    email, pwd = identity(i)

    r = call(s, "GET", "/api/Products", "catalogue")
    products = []
    if r is not None and r.status_code == 200:
        products = r.json().get("data", [])
    ids = [p["id"] for p in products] or list(range(1, 11))
    call(s, "GET", f"/api/Products/{random.choice(ids)}", "product_detail")

    call(s, "POST", "/api/Users", "register",
         json={"email": email, "password": pwd, "passwordRepeat": pwd})

    if random.random() < 0.3:
        call(s, "POST", "/rest/user/login", "login_wrong_password",
             json={"email": email, "password": pwd + "x"})

    r = call(s, "POST", "/rest/user/login", "login_valid",
             json={"email": email, "password": pwd})
    token = bid = None
    if r is not None and r.status_code == 200:
        auth = r.json().get("authentication", {})
        token, bid = auth.get("token"), auth.get("bid")

    if token and bid:
        for pid in random.sample(ids, random.randint(1, 3)):
            call(s, "POST", "/api/BasketItems", "basket_add", token=token,
                 json={"ProductId": pid, "BasketId": bid,
                       "quantity": random.randint(1, 3)})
        call(s, "GET", f"/rest/basket/{bid}", "basket_view", token=token)

    words = {w.lower() for p in products
             for w in p["name"].replace("(", " ").replace(")", " ").split()
             if len(w) > 3}

    words = sorted(words) or ["apple", "juice"]
    for _ in range(3):
        term = (random_query(words) if random.random() < 0.7
                else random.choice(SEARCHES))
        call(s, "GET", "/rest/products/search", "search", params={"q": term})
        time.sleep(random.uniform(0.05, 0.3))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=20, help="nombre d'utilisateurs")
    n = ap.parse_args().n
    for i in range(n):
        one_user(i)
    print(f"\nlot {RUN} terminé : {n} utilisateurs")
    for (scenario, code), count in sorted(stats.items(), key=str):
        print(f"  {scenario:22} {code}  x{count}")
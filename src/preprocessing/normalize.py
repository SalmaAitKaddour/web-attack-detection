
from __future__ import annotations

import re
from urllib.parse import unquote_plus

# --------------------------------------------------------------------------
# 1. NORMALISATION
# --------------------------------------------------------------------------

# Nombre maximum de "décodages URL" successifs. CSIC contient des payloads
# doublement encodés (%253C = "%3C" encodé une 2e fois = "<"). On décode
# jusqu'à ce que le texte ne change plus (ou 3 tours maximum, par sécurité).
MAX_DECODE_ROUNDS = 3

# Début d'URL absolue à supprimer : "http://localhost:8080"
_RE_SCHEME_HOST = re.compile(r"^https?://[^/]+", flags=re.IGNORECASE)
# Fin de ligne de requête à supprimer : " HTTP/1.1"
_RE_HTTP_VERSION = re.compile(r"\s+HTTP/\d(?:\.\d)?\s*$", flags=re.IGNORECASE)
# Espaces multiples (y compris retours à la ligne) -> un seul espace
_RE_SPACES = re.compile(r"\s+")


def url_decode_repeated(text: str, max_rounds: int = MAX_DECODE_ROUNDS) -> str:
    """Décode %XX et '+' plusieurs fois, jusqu'à stabilité.

    encoding="latin-1" : accepte n'importe quel octet (ex. %F1 = ñ) sans jamais
    lever d'erreur, ce qui rend la fonction robuste sur des données sales.
    """
    for _ in range(max_rounds):
        decoded = unquote_plus(text, encoding="latin-1")
        if decoded == text:  # plus rien à décoder -> on s'arrête
            break
        text = decoded
    return text


def normalize_method(method: str | None) -> str:
    """Méthode en minuscules ; PUT -> post (voir explication en tête de fichier)."""
    m = (method or "").strip().lower()
    return "post" if m == "put" else m


def normalize_request(method: str | None, url: str | None, body: str | None = None) -> str:
    """Construit le texte normalisé d'UNE requête.

    method : GET / POST / PUT ...
    url    : URL ou chemin (avec ou sans host, avec ou sans ' HTTP/1.1')
    body   : corps de la requête (formulaire ou JSON aplati), peut être vide/NaN
    """
    url = url if isinstance(url, str) else ""
    body = body if isinstance(body, str) else ""

    url = _RE_SCHEME_HOST.sub("", url.strip())   # enlève http://localhost:8080
    url = _RE_HTTP_VERSION.sub("", url)          # enlève " HTTP/1.1"

    # method + chemin/paramètres + corps, séparés par un espace
    text = f"{normalize_method(method)} {url} {body}"

    text = url_decode_repeated(text)             # %27 -> ' ; %253C -> <
    text = text.lower()                          # SELECT == select
    text = _RE_SPACES.sub(" ", text).strip()     # espaces propres
    return text


# --------------------------------------------------------------------------
# 2. FILTRE INJECTION (appliqué seulement aux ANOMALIES de CSIC)
# --------------------------------------------------------------------------
# CSIC "anomalous" = toutes les attaques (scan de fichiers, tampering de
# paramètres, buffer overflow...). Nous ne voulons que les injections :
# SQLi / XSS (voir proposition, section 3). Le texte est déjà en minuscules.

SQL_PATTERN = re.compile(
    r"\b(select|union|insert\s+into|update\s+\w+\s+set|delete\s+from|drop|alter|"
    r"exec|having|waitfor|sleep|benchmark|truncate|group\s+by|order\s+by|"
    r"information_schema)\b"
    r"|\b(or|and)\b\s+[\w'\"()]+\s*(=|like|>|<)"   # ... or 1=1 / and x like y
)
XSS_PATTERN = re.compile(
    r"<\s*/?\s*(script|img|iframe|svg|body)|javascript:|\bon\w+\s*=|alert\s*\("
)
# caractères spéciaux typiques : quotes, ;, --, commentaires /* */, < >
SPECIAL_PATTERN = re.compile(r"['\"`;<>]|--|/\*|\*/")

INJECTION_PATTERNS = {
    "sql": SQL_PATTERN,
    "xss": XSS_PATTERN,
    "special": SPECIAL_PATTERN,
}


def injection_markers(normalized_text: str) -> list[str]:
    """Liste des familles de marqueurs trouvées dans le texte (ex. ['sql','special'])."""
    return [name for name, pat in INJECTION_PATTERNS.items() if pat.search(normalized_text)]


def looks_like_injection(normalized_text: str) -> bool:
    """True si au moins un marqueur d'injection est présent."""
    return len(injection_markers(normalized_text)) > 0

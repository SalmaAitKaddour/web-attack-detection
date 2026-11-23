"""Tests de normalize.py - lancer avec : pytest"""
from src.preprocessing.normalize import (
    looks_like_injection, normalize_method, normalize_request, url_decode_repeated,
)


def test_put_devient_post():
    assert normalize_method("PUT") == "post"
    assert normalize_method("GET") == "get"


def test_decodage_double():
    # %253C -> %3C -> <
    assert url_decode_repeated("%253Cscript%253E") == "<script>"


def test_normalisation_complete():
    txt = normalize_request("GET", "http://localhost:8080/tienda1/index.jsp?id=1%27+OR+1%3D1 HTTP/1.1")
    assert txt == "get /tienda1/index.jsp?id=1' or 1=1"


def test_corps_nan_ignore():
    # content peut être NaN (float) pour les GET
    assert normalize_request("GET", "/a?b=1", float("nan")) == "get /a?b=1"


def test_filtre_injection():
    assert looks_like_injection("get /a?id=1' or 1=1 --")
    assert looks_like_injection("get /a?q=<script>alert(1)</script>")
    assert not looks_like_injection("get /tienda1/publico/vaciar.jsp?b2=vaciar carrito")
    assert not looks_like_injection("get /web-inf/web.xml")

#!/usr/bin/env python3
# fetch_fixtures.py

import requests
import os
from urllib.parse import urlparse

# 1. Liste des pages à capturer
URLS = [
    # CIRED
    "https://www.centre-cired.fr/chaires/",
    "https://www.centre-cired.fr/soutien-a-la-recherche/",
    # RePEc
    "https://edirc.repec.org/data/ciredfr.html",
    # HAL (exemple de facettes)
    "https://api.archives-ouvertes.fr/search/?q=*:*&rows=0&facet=true"
    "&facet.field=structHasAuthIdHal_fs&facet.prefix=1042364_",
    "https://api.archives-ouvertes.fr/search/?q=*:*&rows=0&facet=true"
    "&facet.field=structHasAuthIdHal_fs&facet.prefix=135977",
]

DEST_ROOT = os.path.join("tests", "fixtures", "html")

for url in URLS:
    print(f"→ Téléchargement de {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    parsed = urlparse(url)
    # Prépare un chemin comme tests/fixtures/html/{netloc}/{path}/index.html
    domain = parsed.netloc
    path = parsed.path.lstrip("/")

    if not path or path.endswith("/"):
        rel_dir = os.path.join(domain, path)
        filename = "index.html"
    else:
        rel_dir, name = os.path.split(path)
        # On ajoute toujours .html
        filename = name + ".html"

    full_dir = os.path.join(DEST_ROOT, rel_dir)
    os.makedirs(full_dir, exist_ok=True)

    out_path = os.path.join(full_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"  → Sauvé dans {out_path}\n")

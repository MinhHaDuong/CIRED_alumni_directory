#!/usr/bin/env python3
# fetch_fixtures.py

import requests
import os
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

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

HERE = os.path.dirname(__file__)
DEST_ROOT = os.path.join(HERE, "fixtures", "html")
visited_urls = set()

for url in URLS:
    print(f"→ Téléchargement de {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    parsed = urlparse(url)
    # Prépare un chemin comme tests/fixtures/html/{netloc}/{path}/[filename].html
    domain = parsed.netloc
    path = parsed.path.lstrip("/")

    # Gestion des requêtes contenant des query params
    if parsed.query:
        # Essayer d'extraire le paramètre facet.prefix pour nommage
        m = re.search(r"facet\\.prefix=([^&]+)", parsed.query)
        prefix = m.group(1) if m else parsed.query.replace("&", "_").replace("=", "-")
        rel_dir = os.path.join(domain, path)
        # Nom du fichier basé sur le chemin et le prefix
        filename = f"{path.replace('/', '_')}_{prefix}.html" if path else f"{domain}_{prefix}.html"
    else:
        if not path or path.endswith("/"):
            rel_dir = os.path.join(domain, path)
            filename = "index.html"
        else:
            rel_dir, name = os.path.split(path)
            filename = name + ".html"

    full_dir = os.path.join(DEST_ROOT, rel_dir)
    os.makedirs(full_dir, exist_ok=True)

    out_path = os.path.join(full_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"  → Sauvé dans {out_path}\n")

    # Télécharge aussi toutes les pages liées (niveau 1, même domaine)
    visited_urls.add(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    parsed_main = urlparse(url)
    for a in soup.find_all("a", href=True):
        link = urljoin(url, a["href"])
        parsed_link = urlparse(link)
        if parsed_link.scheme in ("http", "https") and parsed_link.netloc == parsed_main.netloc and link not in visited_urls:
            visited_urls.add(link)
            try:
                resp2 = requests.get(link, timeout=15)
                resp2.raise_for_status()
                # nommage du fichier lié
                p2 = urlparse(link)
                path2 = p2.path.lstrip("/")
                if not path2 or path2.endswith("/"):
                    rel_dir2 = os.path.join(p2.netloc, path2)
                    filename2 = "index.html"
                else:
                    rel_dir2, name2 = os.path.split(path2)
                    filename2 = name2 + ".html"
                full_dir2 = os.path.join(DEST_ROOT, rel_dir2)
                os.makedirs(full_dir2, exist_ok=True)
                out_path2 = os.path.join(full_dir2, filename2)
                with open(out_path2, "w", encoding="utf-8") as f2:
                    f2.write(resp2.text)
                print(f"    + Sauvé lié: {out_path2}")
            except Exception as e:
                print(f"    ! Erreur téléchargement lié {link}: {e}")

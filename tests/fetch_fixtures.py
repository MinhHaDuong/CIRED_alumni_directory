#!/usr/bin/env python3
# fetch_fixtures.py

import requests
import os
import re
from urllib.parse import urlparse
# Plus besoin de urljoin et BeautifulSoup pour ce script

# 1. Extraire les URL depuis les vCards générées (URL, SOURCE, PHOTO)
HERE = os.path.dirname(__file__)
VCF_DIR = os.path.join(HERE, os.pardir, "1_Scraping")
VCF_FILES = [os.path.join(VCF_DIR, name) for name in ["askCIRED.vcf", "askHAL.vcf", "askREPEC.vcf"]]
URLS = set()
for vcf in VCF_FILES:
    with open(vcf, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith(("URL", "SOURCE", "PHOTO")):
                parts = line.split(":", 1)
                if len(parts) == 2 and parts[1].strip().startswith("http"):
                    URLS.add(parts[1].strip())
URLS = list(URLS)

HERE = os.path.dirname(__file__)
DEST_ROOT = os.path.join(HERE, "fixtures", "html")
visited_urls = set()

for url in URLS:
    print(f"→ Téléchargement de {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"    ! Erreur téléchargement {url}: {e}")
        continue

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

    # Plus de téléchargement automatique des liens HTML

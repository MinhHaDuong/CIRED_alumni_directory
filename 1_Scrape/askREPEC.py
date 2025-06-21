from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass
import os
from datetime import datetime, UTC
import re
from typing import Optional


@dataclass
class Researcher:
    nom: str
    prenom: str
    profile_url: str
    is_alumni: bool
    org: list[str] | None = None
    personal_url: Optional[str] = None


BASE_URL = "https://edirc.repec.org/data/ciredfr.html"


def fetch_page(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_researchers(main_soup):
    researchers = []

    def parse_li(li, is_alumni=False):
        a = li.find("a", href=True)
        if not a:
            return None
        text = a.get_text(strip=True)
        parts = [p.strip() for p in text.split(",", 1)]
        nom, prenom = parts if len(parts) == 2 else (parts[0], "")
        return Researcher(
            nom=nom, prenom=prenom, profile_url=a["href"], is_alumni=is_alumni
        )

    for section_id, is_alumni in [("members", False), ("alumni", True)]:
        section = main_soup.find(id=section_id)
        if section:
            for li in section.find_all("li"):
                r = parse_li(li, is_alumni)
                if r:
                    researchers.append(r)
    return researchers


def enrich_with_profile(researcher: Researcher):
    try:
        soup = fetch_page(researcher.profile_url)
        researcher.org = []

        # Extract affiliations
        aff = soup.find(id="affiliation")
        if aff:
            for h3 in aff.find_all("h3"):
                text = h3.get_text(separator=" ", strip=True)
                percent_match = re.match(r"\((\d+%)\)\s+(.*)", text)
                if percent_match:
                    pct, name = percent_match.groups()
                    org = f"{name} {pct}"
                else:
                    org = text
                researcher.org.append(org)

        # Extract personal homepage
        links = soup.find_all("a", href=True)
        for a in links:
            href = a["href"]
            td = a.find_parent("td")
            if (
                td
                and td.previous_sibling
                and "homelabel" in td.previous_sibling.get("class", [])
            ):
                researcher.personal_url = href
                break

    except Exception as e:
        print(f"Warning: Failed to enrich {researcher.prenom} {researcher.nom}: {e}")


def export_to_vcard(researchers, filename="askREPEC.vcf"):
    with open(filename, "w", encoding="utf-8") as f:
        for r in researchers:
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:4.0\n")
            f.write(f"PRODID:-//{os.path.basename(__file__)}//\n")
            f.write(f"REV:{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}\n")
            f.write(f"FN:{r.prenom} {r.nom}\n")
            f.write(f"N:{r.nom};{r.prenom};;;\n")
            if r.org:
                for org in r.org:
                    clean_org = org.replace(",", "-")
                    f.write(f"ORG:{clean_org}\n")
            if r.profile_url:
                f.write(f"URL;TYPE=REPEC:{r.profile_url}\n")
                f.write(f"SOURCE:{r.profile_url}\n")
            if r.personal_url:
                f.write(f"URL;TYPE=HOME:{r.personal_url}\n")
            f.write(
                f"X-CIRED-HISTORY:Listed as CIRED {'Alumni' if r.is_alumni else 'Member'} in REPEC on 2025-06-11\n"
            )
            f.write("END:VCARD\n\n")
    print(f"✅ Fichier VCF exporté : {filename}")


def main():
    print("🔍 Téléchargement de la page CIRED depuis RePEc...")
    soup = fetch_page(BASE_URL)
    researchers = extract_researchers(soup)
    print(f"🔎 {len(researchers)} chercheurs trouvés. Enrichissement en cours...")

    for r in researchers:
        enrich_with_profile(r)

    export_to_vcard(researchers)


if __name__ == "__main__":
    main()

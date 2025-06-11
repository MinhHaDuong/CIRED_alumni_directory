#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import json
import csv
import time

@dataclass
class Person:
    nom: str
    prenom: str = ""
    statut: str = ""
    domaine_recherche: str = ""
    url_profil: str = ""
    affiliation_actuelle: str = ""

class CiredScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.people = []

    def scrape_cired_website(self):
        urls = [
            "https://www.centre-cired.fr/en/researchers/",
            "https://www.centre-cired.fr/en/board/"
        ]
        for url in urls:
            try:
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                self.people.extend(self._extract_people(soup, url))
                time.sleep(1)
            except Exception as e:
                print(f"Erreur sur {url}: {e}")

    def _extract_people(self, soup, url):
        results = []
        text = soup.get_text().split('\n')
        for line in text:
            parts = line.strip().split()
            if (
                len(parts) >= 3 and
                parts[0][0].isupper() and
                parts[1][0].isupper() and
                any(role in parts for role in ["Post-doc", "DR", "IR", "CR", "Researcher"])
            ):
                prenom, nom = parts[0], parts[1]
                statut = parts[2]
                domaine = ' '.join(parts[3:]) if len(parts) > 3 else ""
                results.append(Person(
                    nom=nom,
                    prenom=prenom,
                    statut=statut,
                    domaine_recherche=domaine,
                    url_profil=url,
                    affiliation_actuelle="CIRED"
                ))
        return results

    def add_known_people(self):
        known_current = [
            ("Claire", "Alestra", "Post-doc", "Climate"),
            ("Vincent", "Auffray", "IR", "Climate"),
            ("Carine", "Barbier", "IR", "Agriculture & Food, Climate"),
            ("Bernard", "Barraqué", "DR Emeritus", "Biodiversity"),
            ("Catherine", "Boemare", "IR", "Biodiversity"),
            ("Thierry", "Brunelle", "Researcher", "Agriculture & Food"),
            ("Adriana", "Calcagno", "Post-doc", "Climate"),
            ("Christophe", "Cassen", "IR", "Climate"),
            ("Antoine", "Castet", "Post-doc", "Agriculture & Food"),
            ("Naceur", "Chaabane", "IR", "Climate"),
            ("Jessica", "Clement", "Researcher", "Climate"),
            ("Gilles", "Crague", "DR", "Cities & Territories"),
            ("Joao", "Domingues", "Post-doc", "Agriculture & Food"),
            ("Bruno", "Dorin", "Researcher", "Agriculture & Food, Climate"),
            ("Rémy", "Doudard", "IR", "Climate"),
            ("Patrice", "Dumas", "Researcher", "Agriculture & Food, Climate"),
            ("Luc", "Elie", "Researcher", "Climate"),
            ("Romain", "Espinosa", "CR", "Biodiversity"),
            ("Adrien", "Fabre", "CR", "Climate"),
            ("Clément", "Feger", "Associated", "Biodiversity"),
            ("Bruno", "Fontaine", "IE", "Climate"),
            ("Yann", "Gaucher", "Post-doc", "Climate"),
            ("Frédéric", "Ghersi", "DR", "Climate"),
            ("Louis-Gaëtan", "Giraudet", "DR", "Climate, Energy & Transport"),
            ("Yannick", "Glemarec", "DR", "Climate"),
            ("Arnaud", "Goussebaïle", "CR", "Climate"),
            ("Anne", "Guillemot", "Researcher", "Energy & Transport"),
            ("Céline", "Guivarch", "DR", "Climate"),
            ("Minh", "Ha-Duong", "DR", "Climate, Energy & Transport"),
            ("Jean-Charles", "Hourcade", "DR Emeritus", "Climate, Energy & Transport"),
            ("Simon", "Jean", "Researcher", "Biodiversity"),
            ("Yann", "Kervinio", "Associated", "Biodiversity"),
            ("Laurent", "Lamy", "Researcher", "Energy & Transport"),
            ("Tristan", "Le Cotty", "Researcher", "Agriculture & Food"),
            ("Thomas", "Le Gallic", "Researcher", "Energy & Transport"),
            ("Florian", "Leblanc", "IR", "Climate"),
            ("Franck", "Lecocq", "DR", "Climate"),
            ("Julien", "Lefèvre", "Researcher", "Climate, Energy & Transport"),
            ("Gaëlle", "Leloup", "Post-doc", "Climate"),
            ("Claire", "Lepault", "Researcher", "Agriculture & Food, Climate"),
            ("Fabien", "Leurent", "DR", "Energy & Transport"),
            ("Harold", "Levrel", "Associated", "Biodiversity"),
            ("Geneviève", "Massard-Guilbaud", "DR Emeritus", "Climate"),
            ("Aurélie", "Méjean", "CR", "Climate"),
            ("Jean", "Mercenier", "Associated", "Climate"),
            ("Antoine", "Missemer", "CR", "Climate"),
            ("Lauriane", "Mouysset", "CR", "Biodiversity"),
            ("Alain", "Nadaï", "DR", "Climate, Energy & Transport"),
            ("Franck", "Nadaud", "IR", "Agriculture & Food, Climate"),
            ("Fabrice", "Ochou", "Post-doc", "Energy & Transport"),
            ("Quentin", "Perrier", "Associated", "Climate"),
            ("Antonin", "Pottier", "Lecturer", "Climate"),
            ("Rémi", "Prudhomme", "Researcher", "Agriculture & Food"),
            ("Philippe", "Quirion", "DR", "Climate, Energy & Transport"),
            ("Alexandre", "Rambaud", "Lecturer", "Biodiversity"),
            ("Éléonore", "Rouault", "Post-doc", "Biodiversity"),
            ("Marie", "Ruillé", "Post-doc", "Agriculture & Food"),
            ("Behrang", "Shirizadeh", "Associated", "Energy & Transport"),
            ("Sophie", "Tabouret", "Post-doc", "Agriculture & Food"),
            ("Léa", "Tardieu", "Associated", "Biodiversity"),
            ("Tarik", "Tazdaït", "DR", "Climate"),
            ("Améline", "Vallet", "CR", "Biodiversity, Climate"),
            ("Vincent", "Viguié", "Researcher", "Climate, Cities & Territories")
        ]

        known_alumni = [
            ("Ignacy", "Sachs", "Founding Director", "1973–1987"),
            ("Henri", "Waisman", "Former Researcher", "Economics"),
            ("Julie", "Rozenberg", "Former Researcher", "Economics"),
            ("Olivier", "Sassi", "Former Researcher", "Modeling"),
            ("Renaud", "Crassous", "Former Researcher", "Economics"),
            ("Vincent", "Gitz", "Former Researcher", "Agriculture"),
            ("Marco Paulo", "Vianna Franco", "Former Researcher", "Economics")
        ]

        for prenom, nom, statut, domaine in known_current:
            self.people.append(Person(nom=nom, prenom=prenom, statut=statut, domaine_recherche=domaine, affiliation_actuelle="CIRED (Actuel)"))

        for prenom, nom, statut, domaine in known_alumni:
            self.people.append(Person(nom=nom, prenom=prenom, statut=statut, domaine_recherche=domaine, affiliation_actuelle="Ancien CIRED"))

    def clean(self):
        self.people = [
            p for p in self.people
            if p.nom != "-" and p.prenom.lower() != "researchers" and len(p.nom) > 1
        ]

    def export_csv(self, filename="cired_people.csv"):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.people[0]).keys())
            writer.writeheader()
            for p in self.people:
                writer.writerow(asdict(p))

    def export_vcard(self, filename=None):
        import os
        from datetime import datetime
        if not filename:
            filename = os.path.splitext(os.path.basename(__file__))[0] + ".vcf"
        with open(filename, 'w', encoding='utf-8') as f:
            for p in self.people:
                f.write("BEGIN:VCARD\n")
                f.write("VERSION:4.0\n")
                f.write(f"PRODID:-//{os.path.basename(__file__)}//\n")
                f.write(f"REV:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n")
                f.write(f"FN:{p.prenom} {p.nom}\n")
                f.write(f"N:{p.nom};{p.prenom};;;\n")
                f.write(f"ORG:{p.affiliation_actuelle}\n")
                f.write(f"TITLE:{p.statut}\n")
                if p.domaine_recherche:
                    f.write(f"EXPERTISE:{p.domaine_recherche}\n")
                if p.url_profil:
                    f.write(f"SOURCE:{p.url_profil}\n")
                f.write("END:VCARD\n\n")

def main():
    scraper = CiredScraper()
    scraper.add_known_people()
    scraper.scrape_cired_website()
    scraper.clean()
    scraper.export_vcard()
    print(f"Scraped {len(scraper.people)} people.")

if __name__ == "__main__":
    main()

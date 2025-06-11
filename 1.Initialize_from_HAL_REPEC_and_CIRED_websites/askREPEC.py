#!/usr/bin/env python3
"""
Script simplifié pour rechercher les anciens du CIRED dans RePEc
Centre International de Recherche sur l'Environnement et le Développement
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from dataclasses import dataclass, asdict
from typing import List
import logging
import datetime
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Researcher:
    """Structure pour stocker les informations d'un chercheur"""
    nom: str
    prenom: str = ""
    status: str = ""
    email: str = ""
    profile_url: str = ""
    publications_count: int = 0
    is_alumni: bool = False

class RepecCiredLookup:
    """Classe pour rechercher les chercheurs CIRED dans RePEc"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://edirc.repec.org/data/ciredfr.html"
        
    def fetch_cired_page(self) -> BeautifulSoup:
        """Récupérer la page CIRED de RePEc"""
        logger.info("Récupération de la page RePEc CIRED...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info("Page récupérée avec succès")
            return soup
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération: {e}")
            raise
    
    def extract_researchers(self, soup: BeautifulSoup) -> List[Researcher]:
        """Extraire les chercheurs de la page RePEc"""
        logger.info("Extraction des chercheurs via sections membres et alumni...")
        
        # Extraction via section Members
        members = self._extract_members(soup)
        # Extraction via section Alumni
        alumni = self._extract_alumni(soup)
        researchers = members + alumni
        logger.info(f"Total de {len(researchers)} chercheurs extraits (membres et alumni)")
        return researchers
    
    
    def _extract_members(self, soup: BeautifulSoup) -> List[Researcher]:
        """Extraire les membres listés dans la section Members"""
        members = []
        # Trouver la section Members par titre (lien #members)
        section = soup.find(id='members') or soup.find(lambda tag: tag.name in ['h2','h3','h4'] 
                            and re.search(r'Members', tag.get_text(), re.IGNORECASE))
        if section:
            ol = section.find_next('ol')
            if ol:
                for li in ol.find_all('li'):
                    a = li.find('a', href=True)
                    text = a.get_text(strip=True)
                    parts = [p.strip() for p in text.split(',', 1)]
                    nom = parts[0]
                    prenom = parts[1] if len(parts) > 1 else ""
                    url = a['href']
                    members.append(Researcher(nom=nom, prenom=prenom, profile_url=url, status="RePEc Member"))
        return members

    def _extract_alumni(self, soup: BeautifulSoup) -> List[Researcher]:
        """Extraire les alumni listés dans la section Alumni"""
        alumni = []
        # Trouver la section Alumni par titre (lien #alumni)
        section = soup.find(id='alumni') or soup.find(lambda tag: tag.name in ['h2','h3','h4'] 
                            and re.search(r'Alumni', tag.get_text(), re.IGNORECASE))
        if section:
            ol = section.find_next('ol')
            if ol:
                for li in ol.find_all('li'):
                    a = li.find('a', href=True)
                    text = a.get_text(strip=True)
                    parts = [p.strip() for p in text.split(',', 1)]
                    nom = parts[0]
                    prenom = parts[1] if len(parts) > 1 else ""
                    url = a['href']
                    alumni.append(Researcher(nom=nom, prenom=prenom, profile_url=url, status="RePEc Alumni", is_alumni=True))
        return alumni
    
    def _parse_profile_link(self, link) -> Researcher:
        """Parser un lien de profil individuel avec filtrage"""
        try:
            link_text = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Filtrer les liens non-pertinents
            if any(word in link_text.lower() for word in ['service', 'registration', 'team', 'corrections', 'mailto', 'repec author']):
                return None
            
            # Nettoyer le nom
            clean_name = re.sub(r'[^\w\s\-\.]', '', link_text).strip()
            
            if not clean_name or len(clean_name) < 3:
                return None
                
            # Vérifier que c'est un format nom de personne
            if not re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', clean_name):
                return None
            
            # Séparer prénom et nom
            parts = clean_name.split()
            if len(parts) >= 2:
                prenom = parts[0]
                nom = ' '.join(parts[1:])
            else:
                return None
            
            return Researcher(
                nom=nom,
                prenom=prenom,
                profile_url=href,
                status="RePEc Profile"
            )
            
        except Exception as e:
            logger.debug(f"Erreur parsing lien: {e}")
            return None
    
    def _extract_from_text(self, soup: BeautifulSoup) -> List[Researcher]:
        """Extraire les noms depuis le texte brut avec filtrage intelligent"""
        researchers = []
#        text_content = soup.get_text()
        
        # Mots à exclure (pas des noms de personnes)
        excluded_words = {
            'centre', 'international', 'research', 'development', 'economics', 'energy',
            'environmental', 'papers', 'articles', 'authors', 'institutions', 'find',
            'search', 'legends', 'broken', 'service', 'genealogy', 'departments',
            'centers', 'world', 'coordinates', 'publications', 'members', 'alumni',
            'corrections', 'france', 'homepage', 'agronomie', 'tropicale', 'belle',
            'gabrielle', 'marne', 'cedex', 'handle', 'economic', 'repec', 'mailto',
            'https', 'email', 'team', 'public', 'profiles', 'additions', 'phone',
            'fax', 'postal', 'jardin', 'avenue', 'nogent', 'sur', 'areas', 'functions'
        }
        
        # Rechercher spécifiquement dans les sections pertinentes
        relevant_sections = soup.find_all(['p', 'div'], string=re.compile(r'(author|people|staff|researcher)', re.IGNORECASE))
        
        if not relevant_sections:
            # Fallback: chercher dans tout le texte mais avec filtrage strict
            relevant_sections = [soup]
        
        found_names = set()
        
        for section in relevant_sections:
            section_text = section.get_text() if hasattr(section, 'get_text') else str(section)
            
            # Pattern plus strict pour vrais noms académiques
            # Rechercher lignes avec noms suivis de titres/affiliations
            lines = section_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Rechercher des patterns comme "Prénom Nom (affiliation)" ou "Prénom Nom, titre"
                name_matches = re.findall(r'\b([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})(?:\s*[,\(]|\s*$)', line)
                
                for match in name_matches:
                    clean_name = re.sub(r'\s+', ' ', match).strip()
                    parts = clean_name.lower().split()
                    
                    # Filtrer si contient des mots exclus
                    if any(word in excluded_words for word in parts):
                        continue
                    
                    # Vérifier que c'est un vrai nom (pas de mots techniques)
                    if len(clean_name) < 6 or len(parts) != 2:
                        continue
                    
                    # Éviter les doublons
                    if clean_name.lower() in found_names:
                        continue
                    
                    found_names.add(clean_name.lower())
                    
                    prenom, nom = parts[0].title(), parts[1].title()
                    
                    researchers.append(Researcher(
                        nom=nom,
                        prenom=prenom,
                        status="Filtered Text Extract"
                    ))
        
        return researchers[:20]  # Limiter davantage
    
    
    def _extract_from_sections(self, soup: BeautifulSoup) -> List[Researcher]:
        """Extraire depuis les sections spécifiques avec filtrage amélioré"""
        researchers = []
        
        # Rechercher les sections "Authors", "Alumni", etc.
        section_keywords = ['author', 'alumni', 'researcher', 'staff', 'member']
        
        for keyword in section_keywords:
            sections = soup.find_all(['div', 'section', 'p'], 
                                   string=re.compile(keyword, re.IGNORECASE))
            
            for section in sections:
                # Chercher dans les éléments suivants
                next_elements = section.find_next_siblings()[:5]
                
                for element in next_elements:
                    text = element.get_text()
                    
                    # Pattern strict pour noms de personnes
                    names = re.findall(r'\b([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,20})\b', text)
                    
                    for name in names[:5]:  # Limite par section
                        parts = name.split()
                        if len(parts) == 2:
                            # Vérifier que ce n'est pas un mot technique
                            if not any(word.lower() in ['international', 'research', 'centre', 'development'] 
                                     for word in parts):
                                researchers.append(Researcher(
                                    nom=parts[1],
                                    prenom=parts[0],
                                    status=f"Section {keyword}",
                                    is_alumni=keyword.lower() == 'alumni'
                                ))
        
        return researchers
        """Extraire depuis les sections spécifiques"""
        researchers = []
        
        # Rechercher les sections "Authors", "Alumni", etc.
        section_keywords = ['author', 'alumni', 'researcher', 'staff', 'member']
        
        for keyword in section_keywords:
            sections = soup.find_all(['div', 'section', 'p'], 
                                   string=re.compile(keyword, re.IGNORECASE))
            
            for section in sections:
                # Chercher dans les éléments suivants
                next_elements = section.find_next_siblings()[:5]
                
                for element in next_elements:
                    text = element.get_text()
                    names = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
                    
                    for name in names[:10]:  # Limite par section
                        parts = name.split()
                        if len(parts) == 2:
                            researchers.append(Researcher(
                                nom=parts[1],
                                prenom=parts[0],
                                status=f"Section {keyword}",
                                is_alumni=keyword.lower() == 'alumni'
                            ))
        
        return researchers
    
    def get_additional_info(self, researchers: List[Researcher]) -> List[Researcher]:
        """Enrichir les informations des chercheurs"""
        logger.info("Enrichissement des informations...")
        
        enriched = []
        
        for researcher in researchers:
            # Tentative de récupération d'infos supplémentaires
            if researcher.profile_url:
                try:
                    # Simuler une recherche d'info supplémentaire
                    # (ici on pourrait faire des requêtes vers les profils individuels)
                    researcher.publications_count = self._estimate_publications(researcher)
                except Exception as e:
                    logger.debug(f"Erreur enrichissement {researcher.nom}: {e}")
            
            enriched.append(researcher)
        
        return enriched
    
    def _estimate_publications(self, researcher: Researcher) -> int:
        """Estimer le nombre de publications (placeholder)"""
        # Simulation basée sur le statut
        if "profile" in researcher.status.lower():
            return 10  # Estimation pour profils RePEc
        return 0
    
    def remove_duplicates(self, researchers: List[Researcher]) -> List[Researcher]:
        """Supprimer les doublons"""
        logger.info("Suppression des doublons...")
        
        seen = set()
        unique = []
        
        for researcher in researchers:
            key = f"{researcher.prenom.lower().strip()} {researcher.nom.lower().strip()}"
            
            if key not in seen and len(key.strip()) > 3:
                seen.add(key)
                unique.append(researcher)
            else:
                logger.debug(f"Doublon ignoré: {researcher.prenom} {researcher.nom}")
        
        logger.info(f"Après déduplication: {len(unique)} chercheurs uniques")
        return unique
    
    def export_to_csv(self, researchers: List[Researcher], filename: str = "repec_cired_researchers.csv"):
        """Exporter en CSV"""
        logger.info(f"Export CSV: {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['prenom', 'nom', 'status', 'email', 'profile_url', 
                         'publications_count', 'is_alumni']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for researcher in researchers:
                writer.writerow(asdict(researcher))
        
        print(f"✅ Fichier CSV créé: {filename}")
    
    def export_to_json(self, researchers: List[Researcher], filename: str = "repec_cired_researchers.json"):
        """Exporter en JSON"""
        logger.info(f"Export JSON: {filename}")
        
        data = [asdict(researcher) for researcher in researchers]
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"✅ Fichier JSON créé: {filename}")
    
    def export_to_vcard(self, researchers: List[Researcher], filename: str = None):
        """Exporter en VCard"""
        if not filename:
            filename = os.path.splitext(os.path.basename(__file__))[0] + ".vcf"
        with open(filename, 'w', encoding='utf-8') as f:
            for r in researchers:
                f.write("BEGIN:VCARD\n")
                f.write("VERSION:4.0\n")
                f.write(f"FN:{r.prenom} {r.nom}\n")
                f.write(f"N:{r.nom};{r.prenom};;;\n")
                if r.profile_url:
                    f.write(f"URL:{r.profile_url}\n")
                if r.email:
                    f.write(f"EMAIL:{r.email}\n")
                f.write(f"NOTE:Publications: {r.publications_count}\n")
                f.write("END:VCARD\n\n")
        print(f"✅ Fichier VCF créé: {filename}")
    
    def print_summary(self, researchers: List[Researcher]):
        """Afficher un résumé"""
        print(f"\n{'='*50}")
        print("📊 RÉSUMÉ RECHERCHE RePEc CIRED")
        print(f"{'='*50}")
        print(f"Total chercheurs trouvés: {len(researchers)}")
        
        # Statistiques par statut
        status_counts = {}
        alumni_count = 0
        
        for r in researchers:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
            if r.is_alumni:
                alumni_count += 1
        
        print(f"Anciens identifiés: {alumni_count}")
        print("\nRépartition par source:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        print("\n📋 Premiers résultats:")
        for i, researcher in enumerate(researchers[:10], 1):
            alumni_mark = " 🎓" if researcher.is_alumni else ""
            print(f"{i:2d}. {researcher.prenom} {researcher.nom}{alumni_mark}")
            if researcher.status:
                print(f"     Status: {researcher.status}")
    
    def run(self):
        """Exécuter la recherche complète"""
        print("🔍 Recherche RePEc CIRED - Démarrage...")
        
        try:
            # 1. Récupérer la page
            soup = self.fetch_cired_page()
            
            # 2. Extraire les chercheurs
            researchers = self.extract_researchers(soup)
            
            # 2.5 Suppression de l'ajout statique des chercheurs connus
            
            # 3. Enrichir les informations
            researchers = self.get_additional_info(researchers)
            
            # 4. Supprimer les doublons
            unique_researchers = self.remove_duplicates(researchers)
            
            # 5. Afficher le résumé
            self.print_summary(unique_researchers)
            
            # 6. Exporter
            self.export_to_vcard(unique_researchers)
            
            print("\n✅ Recherche terminée avec succès!")
            print("📁 Fichier généré:")
            print(f"   - {os.path.splitext(os.path.basename(__file__))[0]}.vcf")
            
            return unique_researchers
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution: {e}")
            print(f"❌ Erreur: {e}")
            raise

def main():
    """Fonction principale"""
    lookup = RepecCiredLookup()
    researchers = lookup.run()
    
    return researchers

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import csv
import time
import re
from urllib.parse import urljoin
import os
from datetime import datetime

@dataclass
class Person:
    nom: str
    prenom: str = ""
    statut: str = ""
    expertise: str = ""
    url_profil: str = ""
    photo_url: str = ""
    email: str = ""
    google_scholar_url: str = ""
    cv_url: str = ""
    hal_url: str = ""
    affiliation_actuelle: str = ""

class CiredScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.people = []
        self.base_url = "https://www.centre-cired.fr"
        self.processed_urls = set()  # Track processed profile URLs to avoid duplicates

    def scrape_cired_website(self):
        """Scrape the main CIRED pages to find person entries"""
        urls = [
#            "https://www.centre-cired.fr/groupes-de-recherche-equipes/",
            "https://www.centre-cired.fr/chaires/",
            "https://www.centre-cired.fr/soutien-a-la-recherche/",
#            "https://www.centre-cired.fr/doctorants/",
#            "https://www.centre-cired.fr/chercheurs/",
        ]
        
        for url in urls:
            print(f"Scraping directory: {url}")
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find person entries in the directory
                person_entries = self._find_person_entries(soup, url)
                print(f"Found {len(person_entries)} person entries on {url}")
                               
                for entry in person_entries:
                    person = self._extract_person_from_entry(entry, url)
                    if person:
                        # Check if we've already processed this person
                        person_key = (person.prenom.lower(), person.nom.lower()) if person.prenom and person.nom else None
                        profile_url = person.url_profil
                        
                        # Skip if we've already processed this person (by name or URL)
                        if profile_url and profile_url in self.processed_urls:
                            print(f"Skipping duplicate: {person.prenom} {person.nom} (already processed)")
                            continue
                            
                        # Check for name duplicates
                        if person_key:
                            existing_names = {(p.prenom.lower(), p.nom.lower()) for p in self.people}
                            if person_key in existing_names:
                                print(f"Skipping duplicate: {person.prenom} {person.nom} (name already exists)")
                                continue
                        
                        self.people.append(person)
                        print(f"Added: {person.prenom} {person.nom}")
                        
                        # Mark this profile URL as processed
                        if profile_url:
                            self.processed_urls.add(profile_url)
                        
                        # If we have a profile URL, scrape detailed info
                        if person.url_profil:
                            self._scrape_person_details(person)
                          
                time.sleep(2)  # Be respectful to the server
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")

    def _find_person_entries(self, soup, base_url):
        """Find HTML fragments describing each person entry"""
        person_entries = []
        
        # Look for common patterns in academic directories
        selectors = [
            # Cards or profile containers
            '.person-card', '.researcher-card', '.profile-card',
            '.person', '.researcher', '.member',
            # List items that might contain person info
            'li[class*="person"]', 'li[class*="researcher"]', 'li[class*="member"]',
            # Divs with person-related classes
            'div[class*="person"]', 'div[class*="researcher"]', 'div[class*="profile"]',
            # Sections
            'section[class*="person"]',
            # Generic containers that might have links to profiles
            '.entry-content a[href*="/chercheur/"]',
            '.entry-content a[href*="/researcher/"]',
            '.entry-content a[href*="/membre/"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                person_entries.extend(elements)
        
        # If no specific selectors work, look for links that seem to point to person pages
        if not person_entries:
            # Look for any links that might be person profiles
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                # Check if this looks like a person profile URL
                if any(keyword in href.lower() for keyword in ['/chercheur/', '/researcher/', '/membre/', '/people/', '/person/']):
                    person_entries.append(link)
        
        return person_entries

    def _extract_original_photo_url(self, url):
        """Extract original photo URL from ShortPixel or other optimization services"""
        if not url:
            return ""
        
        # Handle ShortPixel URLs like:
        # https://sp-ao.shortpixel.ai/client/to_webp,q_glossy,ret_img,w_510,h_510/https://www.centre-cired.fr/wp-content/uploads/2020/10/JLefevre_photo-510x510.jpg
        if 'shortpixel.ai' in url:
            # Find the actual URL after the ShortPixel parameters
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part.startswith('https:') and i > 0:
                    # Reconstruct the original URL
                    original_url = '/'.join(parts[i:])
                    return original_url
        
        # Handle other common CDN patterns
        if 'wp-content/uploads' in url and '/client/' in url:
            # Extract just the wp-content part
            wp_content_index = url.find('wp-content/uploads')
            if wp_content_index != -1:
                # Find the domain part before wp-content
                domain_part = url[:wp_content_index]
                if 'centre-cired.fr' in domain_part:
                    return f"https://www.centre-cired.fr/{url[wp_content_index:]}"
                else:
                    # Look for the original domain in the URL
                    if 'centre-cired.fr' in url:
                        start = url.find('centre-cired.fr')
                        domain_start = url.rfind('https:', 0, start)
                        if domain_start != -1:
                            return url

    def _select_best_email(self, emails, person):
        """Select the best email address, prioritizing personal emails over generic ones"""
        if not emails:
            return ""
        
        # Remove duplicates while preserving order
        unique_emails = []
        seen = set()
        for email in emails:
            email_clean = email.lower().strip()
            if email_clean not in seen:
                seen.add(email_clean)
                unique_emails.append(email)
        
        # Generic email patterns to avoid
        generic_patterns = [
            'communication',
            'contact',
            'info',
            'admin',
            'secretary',
            'secretariat',
            'webmaster',
            'support'
        ]
        
        # Create name variations to look for in email
        name_variations = []
        if person.prenom:
            name_variations.extend([
                person.prenom.lower(),
                person.prenom.lower()[:3],  # First 3 letters
                person.prenom.lower()[0]    # First initial
            ])
        if person.nom:
            name_variations.extend([
                person.nom.lower(),
                person.nom.lower()[:3],     # First 3 letters
            ])
        
        # Score emails based on how likely they are to be the person's email
        scored_emails = []
        for email in unique_emails:
            email_lower = email.lower()
            score = 0
            
            # Penalize generic emails heavily
            if any(pattern in email_lower for pattern in generic_patterns):
                score -= 100
            
            # Reward emails that contain the person's name
            for name_var in name_variations:
                if name_var and name_var in email_lower:
                    score += 50
                    # Extra points if it's at the beginning
                    if email_lower.startswith(name_var):
                        score += 25
            
            # Reward personal-looking patterns
            if '.' in email_lower.split('@')[0]:  # firstname.lastname pattern
                score += 20
            
            # Slight preference for shorter emails (less likely to be generic)
            if len(email) < 30:
                score += 5
            
            scored_emails.append((score, email))
        
        # Sort by score (highest first) and return the best one
        scored_emails.sort(key=lambda x: x[0], reverse=True)
        return scored_emails[0][1] if scored_emails else unique_emails[0]

    def _extract_hal_url(self, hal_url):
        """Extract HAL identifier and convert to canonical HAL URL"""
        if not hal_url:
            return ""
        
        # Extract the authIdHal parameter from URLs like:
        # https://hal.archives-ouvertes.fr/search/index/?qa%5BauthIdHal_s%5D%5B%5D=carine-barbier&authIdHal_s=carine-barbier
        
        # Look for authIdHal_s parameter
        hal_id_match = re.search(r'authIdHal_s=([^&]+)', hal_url)
        if hal_id_match:
            hal_id = hal_id_match.group(1)
            # URL decode if necessary
            hal_id = hal_id.replace('%5B', '[').replace('%5D', ']')
            return f"https://hal.science/{hal_id}"
        
        # Also check for the array format qa[authIdHal_s][]
        hal_id_match = re.search(r'qa%5BauthIdHal_s%5D%5B%5D=([^&]+)', hal_url)
        if hal_id_match:
            hal_id = hal_id_match.group(1)
            return f"https://hal.science/{hal_id}"
        
        # If we can't extract the ID, return the original URL
        return hal_url

    def _extract_person_from_entry(self, entry, base_url):
        """Extract person information from an HTML entry"""
        try:
            person = Person(nom="", affiliation_actuelle="CIRED")

            # Name and Job Title
            name_div = entry.select_one(".member-name")
            if name_div:
                raw_text = name_div.get_text(" ", strip=True)
                name_only = name_div.contents[0].strip() if name_div.contents else ""
                person.prenom, *rest = name_only.strip().split(" ", 1)
                person.nom = rest[0] if rest else ""

                title_span = name_div.find("span")
                if title_span:
                    person.statut = title_span.get_text(strip=True)

            # Photo
            img = entry.select_one(".member-image img")
            if img:
                data_src = img.get("data-src") or img.get("src")
                if data_src:
                    # Extract original URL from ShortPixel optimization service
                    photo_url = self._extract_original_photo_url(data_src)
                    person.photo_url = photo_url if photo_url.startswith("http") else urljoin(base_url, photo_url)

            # Link (if any)
            link_tag = entry.select_one(".member-image a[href]")
            if link_tag:
                person.url_profil = urljoin(base_url, link_tag.get("href"))

            # Only return if we have at least a name
            if person.nom or person.prenom:
                return person

        except Exception as e:
            print(f"Error extracting person from entry: {e}")

        return None

    def _scrape_person_details(self, person):
        """Scrape detailed information from person's profile page"""
        if not person.url_profil:
            return
            
        try:
            print(f"Scraping details for: {person.prenom} {person.nom}")
            response = self.session.get(person.url_profil, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract email - prioritize personal emails over generic ones
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, response.text)
            
            # Look for email in mailto links first (more reliable)
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            if mailto_links:
                mailto_emails = [link['href'].replace('mailto:', '') for link in mailto_links]
                emails.extend(mailto_emails)
            
            if emails:
                # Filter and prioritize emails
                person.email = self._select_best_email(emails, person)
            
            # Find Google Scholar link
            scholar_links = soup.find_all('a', href=re.compile(r'scholar\.google'))
            if scholar_links:
                person.google_scholar_url = scholar_links[0]['href']
            
            # Find HAL (Hyper Articles en Ligne) link
            hal_links = soup.find_all('a', href=re.compile(r'hal\.archives-ouvertes\.fr'))
            if hal_links:
                person.hal_url = self._extract_hal_url(hal_links[0]['href'])
            
            # Find CV link
            cv_keywords = ['cv', 'curriculum', 'vitae', 'resume']
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '').lower()
                text = link.get_text(strip=True).lower()
                
                # Check for "Télécharger le CV" text specifically
                if 'télécharger le cv' in text:
                    person.cv_url = urljoin(person.url_profil, link['href'])
                    break
                
                # Fallback to other CV patterns
                if any(keyword in href or keyword in text for keyword in cv_keywords):
                    if href.endswith(('.pdf', '.doc', '.docx')) or 'cv' in href:
                        person.cv_url = urljoin(person.url_profil, link['href'])
                        break
            
            # Update photo URL if we find a better one on the profile page
            if not person.photo_url:
                img = soup.find('img', alt=re.compile(person.nom, re.IGNORECASE))
                if img:
                    img_src = img.get('src', '')
                    original_url = self._extract_original_photo_url(img_src)
                    person.photo_url = urljoin(person.url_profil, original_url)
            
            time.sleep(1)  # Be respectful
            
        except Exception as e:
            print(f"Error scraping details for {person.prenom} {person.nom}: {e}")

    def add_known_people(self):
        """Add known alumni"""
        known_alumni = [
            ("Ignacy", "Sachs", "Founding Director", "1973–1987"),
            ("Henri", "Waisman", "Former Researcher", "Economics"),
            ("Julie", "Rozenberg", "Former Researcher", "Economics"),
            ("Olivier", "Sassi", "Former Researcher", "Modeling"),
            ("Renaud", "Crassous", "Former Researcher", "Economics"),
            ("Vincent", "Gitz", "Former Researcher", "Agriculture"),
            ("Marco Paulo", "Vianna Franco", "Former Researcher", "Economics")
        ]

        for prenom, nom, statut, expertise in known_alumni:
            self.people.append(Person(
                nom=nom, 
                prenom=prenom, 
                statut=statut, 
                expertise=expertise
            ))

    def clean(self):
        """Clean and deduplicate the people list"""
        # Remove invalid entries
        self.people = [
            p for p in self.people
            if p.nom and p.nom != "-" and p.prenom.lower() != "researchers" and len(p.nom) > 1
        ]
        
        # Remove duplicates based on name
        seen = set()
        unique_people = []
        for person in self.people:
            key = (person.prenom.lower(), person.nom.lower())
            if key not in seen:
                seen.add(key)
                unique_people.append(person)
        
        self.people = unique_people

    def export_csv(self, filename="cired_people.csv"):
        """Export to CSV"""
        if not self.people:
            print("No people to export")
            return
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.people[0]).keys())
            writer.writeheader()
            for p in self.people:
                writer.writerow(asdict(p))
        print(f"Exported {len(self.people)} people to {filename}")

    def export_vcard(self, filename=None):
        """Export to VCard format with all available information"""
        if not filename:
            filename = os.path.splitext(os.path.basename(__file__))[0] + ".vcf"
            
        if not self.people:
            print("No people to export")
            return
            
        with open(filename, 'w', encoding='utf-8') as f:
            for p in self.people:
                f.write("BEGIN:VCARD\n")
                f.write("VERSION:4.0\n")
                f.write(f"PRODID:-//{os.path.basename(__file__)}//\n")
                f.write(f"REV:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n")
                if p.url_profil:
                    f.write(f"SOURCE:{p.url_profil}\n")
                f.write(f"FN:{p.prenom} {p.nom}\n")
                f.write(f"N:{p.nom};{p.prenom};;;\n")
                f.write(f"ORG:{p.affiliation_actuelle}\n")
                
                if p.statut:
                    f.write(f"TITLE:{p.statut}\n")
                
                if p.email:
                    f.write(f"EMAIL:{p.email}\n")
                
                if p.url_profil:
                    f.write(f"URL;TYPE=INSTITUTIONAL:{p.url_profil}\n")
                
                if p.photo_url:
                    f.write(f"PHOTO:{p.photo_url}\n")
                
                if p.google_scholar_url:
                    f.write(f"X-GOOGLE-SCHOLAR:{p.google_scholar_url}\n")
                
                if p.hal_url:
                    f.write(f"URL;TYPE=HAL:{p.hal_url}\n")
                
                if p.cv_url:
                    f.write(f"URL;TYPE=CV:{p.cv_url}\n")
                
                if p.expertise:
                    f.write(f"EXPERTISE:{p.expertise}\n")
                
                f.write("END:VCARD\n\n")
                
        print(f"Exported {len(self.people)} people to {filename}")

def main():
    scraper = CiredScraper()
    
    print("Adding known alumni...")
    scraper.add_known_people()
    
    print("Scraping CIRED website...")
    scraper.scrape_cired_website()
    
    print("Cleaning data...")
    scraper.clean()
    
    print("Exporting results...")
    scraper.export_csv()
    scraper.export_vcard()
    
    print(f"\nCompleted! Found {len(scraper.people)} people total.")
    
    # Print summary
    current_count = sum(1 for p in scraper.people if p.affiliation_actuelle == "CIRED")
    alumni_count = sum(1 for p in scraper.people if p.affiliation_actuelle == "Ancien CIRED")
    with_email = sum(1 for p in scraper.people if p.email)
    with_photo = sum(1 for p in scraper.people if p.photo_url)
    
    print(f"- Current staff: {current_count}")
    print(f"- Alumni: {alumni_count}")
    print(f"- With email: {with_email}")
    print(f"- With photo: {with_photo}")

if __name__ == "__main__":
    main()

# CIRED Alumni Directory schema

## Overview
This document proposes a schema for the CIRED Alumni Directory.
It uses vCard 4.0 properties, ensuring compatibility with standard contact exchange formats.

## Core vCard 4.0 Structure
```
BEGIN:VCARD
VERSION:4.0
[properties]
END:VCARD
```

## Field Mappings

### 1. Identification

| vCard 4.0 Property | Format | Notes |
|-------------------|---------|-------|
| `FN` | `FN:FirstName LastName` | Full Name - Formatted name (required) |
| `N` | `N:LastName;FirstName;;;` | Full Name - Structured name property |
| `NICKNAME` | `NICKNAME:Nick` | Nickname - Informal name or alias used when at CIRED|
| `GENDER` | `GENDER:M/F/O/N/U` | Gender - M=Male, F=Female, O=Other, N=None, U=Unknown |
| `BDAY` | `BDAY:19901215` or `BDAY:--1215` | Birthday - Full date or month-day only (optional for age statistics) |
| `ADR` | `ADR:;;City;;;Country;` | Current City - Structured address, city component |
| `PHOTO` | `PHOTO:https://example.com/photo.jpg` | Alumni Picture - URL to image or embedded data |
| `DEATHDATE` | `DEATHDATE:20231215T143000Z` | Death Date - RFC 6474, ISO 8601 timestamp |
| `URL;TYPE=CV` | `URL;TYPE=CV:https://example.com/resume.pdf` | Résumé / CV - Typed URL for CV |

### 2. Professional Information

| vCard 4.0 Property | Format | Notes |
|-------------------|---------|-------|
| `EMAIL` | `EMAIL:user@example.com` | Email Address - Standard email property |
| `TEL` | `TEL:+33-1-23-45-67-89` | Phone Number - Professional phone number |
| `X-CONTACT-PREFERENCE` | `X-CONTACT-PREFERENCE:email/phone/linkedin` | Preferred Contact Method - How they prefer to be contacted |
| `ORG` | `ORG:Organization Name` | Current Affiliation - Organization name |
| `TITLE` | `TITLE:Job Title` | Job Title - Professional title |
| `X-POSITION-START` | `X-POSITION-START:2023-06` | Current Position Start Date - ISO date format |
| `URL;TYPE=INSTITUTIONAL` | `URL;TYPE=INSTITUTIONAL:https://www.centre-cired.fr/fabien-leurent/` | Institutional homepage - Typed URL |
| `URL;TYPE=ORCID` | `URL;TYPE=ORCID:https://orcid.org/0000-0000-0000-0000` | ORCID ID - Typed URL |
| `URL;TYPE=REPEC` | `URL;TYPE=REPEC:https://ideas.repec.org/f/ple796.html` | Repec Profile - Typed URL |
| `URL;TYPE=SCHOLAR` | `URL;TYPE=SCHOLAR:https://scholar.google.com/...` | Google Scholar Profile - Typed URL |
| `URL;TYPE=LINKEDIN` | `URL;TYPE=LINKEDIN:https://linkedin.com/in/...` | LinkedIn Profile - Typed URL |
| `URL;TYPE=HOME` | `URL;TYPE=HOME:https://example.com` | Personal Website - Personal website |
| `URL;TYPE=HAL` | `URL;TYPE=HAL:https://cv.hal.science/carine-barbier` | idHAL Author Identifier - Typed URL for HAL archive |
| `EXPERTISE` | `EXPERTISE;LEVEL=expert:Climate Economics` | Domains of Expertise - RFC 6715, Expertise with optional level |
| `X-SECTOR` | `X-SECTOR:Academic/Public/Private/NGO/IO` | Sector of Employment - Custom extension |

### 3. CIRED Involvement → Custom Extensions

| vCard 4.0 Property | Format | Notes |
|-------------------|---------|-------|
| `RELATED;TYPE=colleague` | `RELATED;TYPE=colleague:mailto:colleague@cired.fr` | Collaborators at CIRED - Related person as colleague |
| `RELATED;TYPE=supervisor` | `RELATED;TYPE=supervisor:mailto:supervisor@cired.fr` | Past Supervisor at CIRED - Related person as supervisor |
| `X-CIRED-STATUS` | `X-CIRED-STATUS:PhD/Postdoc/Intern/Engineer/IR/DR` | CIRED Status (when there) - Custom extension |
| `X-CIRED-START` | `X-CIRED-START:2020-09` | Date Joined CIRED - ISO date format |
| `X-CIRED-HISTORY` | `X-CIRED-HISTORY:Marie joined CIRED as a PhD student in 2019, working on carbon pricing mechanisms under Dr. Smith's supervision. She successfully defended her thesis in 2022 and continued as a postdoc focusing on EU ETS reform analysis.` | Past at CIRED - Free-form narrative text |
| `X-CIRED-PROJECTS` | `X-CIRED-PROJECTS:Project1\, Project2` | Notable Project(s) - Comma-separated, escaped |

### 4. Community Engagement → Custom Extensions

| CIRED Field | vCard 4.0 Property | Format | Notes |
|-------------|-------------------|---------|-------|
| Willing to Be Contacted | `X-OPEN-CONTACT` | `X-OPEN-CONTACT:TRUE/FALSE` | Boolean as text |
| Willing to Mentor | `X-MENTOR-AVAILABLE` | `X-MENTOR-AVAILABLE:TRUE/FALSE` | Boolean as text |
| Interested in Alumni Events | `X-ALUMNI-EVENTS` | `X-ALUMNI-EVENTS:TRUE/FALSE` | Boolean as text |
| Personal Message / Bio | `NOTE` | `NOTE:Personal bio text here...` | Standard note field |

### 5. Metadata & Admin

| vCard 4.0 Property | Format | Notes |
|-------------------|---------|-------|
| `UID` | `UID:123456790` | Long integer - Hash of the contents excluding section 5. |
| `REV` | `REV:20241101T120000Z` | Last Updated - Standard revision timestamp |
| `PRODID` | `PRODID:-//CIRED//Alumni Directory//EN` | Entry Created By - Product identifier |
| `SOURCE` | `SOURCE:https://minh.haduong.com` | Information source - URLs |
| `X-VERIFIED` | `X-VERIFIED:Verified/Unverified` | Verification Status - Custom extension |
| `X-DATA-RETENTION` | `X-DATA-RETENTION:10-years` | Data Retention Period - GDPR compliance |

### 6. GDPR Granular Consent Tracking

| vCard 4.0 Property | Format | Notes |
|-------------------|---------|-------|
| `X-CONSENT-VERSION` | `X-CONSENT-VERSION:1.2` | Privacy policy version - Semantic versioning |
| `X-CONSENT-PUBLIC` | `X-CONSENT-PUBLIC:FN\,ORG\,TITLE` | Public consent fields - Escaped comma list |
| `X-CONSENT-PUBLIC-DATE` | `X-CONSENT-PUBLIC-DATE:20241101T120000Z` | Public consent timestamp - ISO 8601 |
| `X-CONSENT-PUBLIC-METHOD` | `X-CONSENT-PUBLIC-METHOD:web_form/email/phone/paper` | Public consent method |
| `X-CONSENT-PUBLIC-IP` | `X-CONSENT-PUBLIC-IP:192.168.1.100` | Public consent IP address (if online) |
| `X-CONSENT-PUBLIC-WITHDRAWN` | `X-CONSENT-PUBLIC-WITHDRAWN:20241215T100000Z` | Public consent withdrawal (if applicable) |
| `X-CONSENT-MEMBERS` | `X-CONSENT-MEMBERS:FN\,ORG\,TITLE\,EMAIL\,NOTE` | Members consent fields - Escaped comma list |
| `X-CONSENT-MEMBERS-DATE` | `X-CONSENT-MEMBERS-DATE:20241101T120000Z` | Members consent timestamp - ISO 8601 |
| `X-CONSENT-MEMBERS-METHOD` | `X-CONSENT-MEMBERS-METHOD:web_form/email/phone/paper` | Members consent method |
| `X-CONSENT-MEMBERS-IP` | `X-CONSENT-MEMBERS-IP:192.168.1.100` | Members consent IP address (if online) |
| `X-CONSENT-MEMBERS-WITHDRAWN` | `X-CONSENT-MEMBERS-WITHDRAWN:20241215T100000Z` | Members consent withdrawal (if applicable) |
| `X-CONSENT-ADMIN` | `X-CONSENT-ADMIN:FN\,ORG\,TITLE\,EMAIL\,NOTE\,TEL\,ADR` | Admin consent fields - Escaped comma list |
| `X-CONSENT-ADMIN-DATE` | `X-CONSENT-ADMIN-DATE:20241101T120000Z` | Admin consent timestamp - ISO 8601 |
| `X-CONSENT-ADMIN-METHOD` | `X-CONSENT-ADMIN-METHOD:web_form/email/phone/paper` | Admin consent method |
| `X-CONSENT-ADMIN-IP` | `X-CONSENT-ADMIN-IP:192.168.1.100` | Admin consent IP address (if online) |
| `X-CONSENT-ADMIN-WITHDRAWN` | `X-CONSENT-ADMIN-WITHDRAWN:20241215T100000Z` | Admin consent withdrawal (if applicable) |
| `X-CONSENT-PURPOSES` | `X-CONSENT-PURPOSES:directory\,events\,newsletter` | Processing purposes - Escaped comma list |
| `X-CONSENT-REVIEW` | `X-CONSENT-REVIEW:20241101T120000Z` | Last consent confirmation - ISO 8601 timestamp |
| `X-CONSENT-EXPIRY` | `X-CONSENT-EXPIRY:20261101T120000Z` | Consent expiration (if applicable) |
| `X-CONSENT-NOTES` | `X-CONSENT-NOTES:Upgraded from public to members on user request` | Administrative notes |


## Implementation Notes

### Standards and Extensions Used
This schema is based on **[RFC 6350](https://tools.ietf.org/rfc/rfc6350.txt)**: vCard 4.0 specification - the core standard for electronic business cards and contact information exchange.

It uses extensions **[RFC 6715](https://tools.ietf.org/rfc/rfc6715.txt)** for Place of Work - adds workplace-related properties including EXPERTISE, and **[RFC 6474](https://tools.ietf.org/rfc/rfc6474.txt)** for Deceased Persons - adds DEATHDATE property for deceased alumni.

It uses custom extensions with the standard `X-` prefix.

### RELATED Property for Relationships
- `RELATED;TYPE=supervisor` identifies PhD/thesis supervisors
- `RELATED;TYPE=colleague` identifies collaborators and colleagues
- Format: `RELATED;TYPE=supervisor;VALUE=text:Dr. JC Hourcade`
- Let's use free text and not worry about relationship links integrity.

### HAL Archive Integration
- `URL;TYPE=HAL` provides direct link to author's HAL (Hyper Articles en Ligne) profile [idHAL](https://doc.hal.science/faq/?h=idhal#idhal-et-cv)
- HAL is the French national open archive for scholarly publications
- Format: `https://cv.hal.science/idHAL`

### CIRED History Field
- `X-CIRED-HISTORY` contains a free-form narrative about the person's time at CIRED
- Should include key milestones, supervisor relationships, thesis topics, career progression
- No fixed format - allows rich storytelling about the alumni's CIRED experience
- Limited to time at CIRED, for personal bio use the NOTE field.

### CATEGORIES for Alumni Status
- Use `CATEGORIES` to track alumni association membership status
- Examples: `CIRED-Alumni`, `Active-Member`, `Emeritus`, `Honorary-Member`
- Allows filtering and grouping by membership type

### Data Type Considerations
- **Dates**: Use ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM`)
- **URLs**: Must be complete URLs with protocol (https://)
- **Boolean Values**: Represent as `TRUE`/`FALSE` text strings
- **Lists**: Use comma separation with escaping (`\,`) when needed

### Compatibility
- Standard vCard properties ensure basic contact info works across all applications
- Custom extensions preserve institutional data for CIRED-aware systems
- Fallback behavior: Non-CIRED systems show standard contact info

### Versionning
- Scraping scripts should hash the contents and set the `UID` property accordingly.
- Scraping scripts include their name in `PRODID` property.
- Use repeated `SOURCE` property to link to original public pages scrapped.

### Privacy & Security
- Scraping scripts set visiblity to Admin-only
- Only merge vCard variants with the same visibility level.
- Respect visibility settings when exporting

### GDPR Article 7 Compliance
The consent tracking fields ensure compliance with GDPR Article 7 requirements:

**Demonstrating Consent (Art. 7.1)**: `X-CONSENT-TIMESTAMP`, `X-CONSENT-METHOD`, `X-CONSENT-IP`, and `X-CONSENT-VERSION` provide proof that consent was obtained and document the circumstances.

**Informed Consent (Art. 7.2)**: `X-CONSENT-VERSION` links to specific privacy policy version, ensuring we can prove what information was provided when consent was given.

**Withdrawal Rights (Art. 7.3)**: `X-CONSENT-WITHDRAWN` tracks when consent is withdrawn. When this field is populated, the contact should be moved to appropriate visibility level or removed from directories.

**Specific & Granular Consent**: `X-CONSENT-FIELDS` and `X-CONSENT-PURPOSES` document exactly what data processing was consented to, allowing granular control and compliance with data minimization principles.

### Single vCard with Multi-Level Consent Management
The schema uses a single vCard per person with granular consent tracking for each visibility level:

- **Public Level**: Basic professional information (name, organization, title)
- **Members Level**: Enhanced contact details (email, bio, etc.)  
- **Admin Level**: Complete information including private contacts and internal notes

Each consent level maintains its own complete audit trail with timestamp, method, and IP address tracking.

### Consent Evolution Tracking
The granular consent fields support real-world scenarios:
- **Consent Upgrades**: Alumni can move from public to members to admin level
- **Consent Downgrades**: Alumni can reduce their visibility level
- **Partial Withdrawal**: Alumni can withdraw specific consent levels while maintaining others
- **Complete Audit**: Each level change is tracked independently for GDPR compliance

### Export Generation Logic
Applications generate appropriate exports by filtering fields based on the highest active consent level:
1. Check if admin consent exists and is not withdrawn
2. If not, check members consent level
3. If not, check public consent level
4. Include only fields listed in the active consent level

### Export Strategy
Generate three separate vCard files based on active consent levels:
- **directory-admin.vcf**: Contacts with active admin-level consent
- **directory-members.vcf**: Contacts with active members-level consent or higher
- **directory-public.vcf**: Contacts with active public-level consent or higher

Each export includes only the fields consented to at that level. Consent tracking fields (Section 6) are included only in admin exports to protect privacy while maintaining compliance documentation.

## Complete Example vCards

### Single vCard Example with Multi-Level Consent
```vcf
BEGIN:VCARD
VERSION:4.0
FN:Marie Dubois
N:Dubois;Marie;;;
EMAIL:marie.dubois@example.com
TEL:+33-1-45-67-89-01
X-CONTACT-PREFERENCE:email
ORG:CNRS
TITLE:Research Director
X-POSITION-START:2020-03
ADR:;;Lyon;;;France;
NOTE:Climate economist specializing in carbon pricing. Former OECD advisor (2018-2020) focusing on climate policy in developing countries.
CATEGORIES:CIRED-Alumni,Active-Member
X-CIRED-STATUS:Postdoc
X-CIRED-START:2015-09
X-CIRED-HISTORY:Marie completed her postdoc at CIRED from 2015-2018, working on carbon market mechanisms under Dr. Guesnerie's supervision.
X-DATA-RETENTION:10-years
X-CONSENT-VERSION:1.2
X-CONSENT-PUBLIC:FN\,ORG\,TITLE
X-CONSENT-PUBLIC-DATE:20241101T120000Z
X-CONSENT-PUBLIC-METHOD:web_form
X-CONSENT-PUBLIC-IP:192.168.1.100
X-CONSENT-MEMBERS:FN\,ORG\,TITLE\,EMAIL\,NOTE
X-CONSENT-MEMBERS-DATE:20241201T140000Z
X-CONSENT-MEMBERS-METHOD:web_form
X-CONSENT-MEMBERS-IP:192.168.1.100
X-CONSENT-ADMIN:FN\,ORG\,TITLE\,EMAIL\,NOTE\,TEL\,ADR\,X-CIRED-HISTORY
X-CONSENT-ADMIN-DATE:20241201T140000Z
X-CONSENT-ADMIN-METHOD:web_form
X-CONSENT-ADMIN-IP:192.168.1.100
X-CONSENT-PURPOSES:directory\,events\,statistics
X-VERIFIED:Verified
REV:20241201T140000Z
END:VCARD
```

### Export Results from Single vCard

**Public Export (directory-public.vcf):**
```vcf
BEGIN:VCARD
VERSION:4.0
FN:Marie Dubois
ORG:CNRS
TITLE:Research Director
END:VCARD
```

**Members Export (directory-members.vcf):**
```vcf
BEGIN:VCARD
VERSION:4.0
FN:Marie Dubois
ORG:CNRS
TITLE:Research Director
EMAIL:marie.dubois@example.com
NOTE:Climate economist specializing in carbon pricing. Former OECD advisor (2018-2020) focusing on climate policy in developing countries.
END:VCARD
```

**Admin Export (directory-admin.vcf):**
```vcf
BEGIN:VCARD
VERSION:4.0
FN:Marie Dubois
ORG:CNRS
TITLE:Research Director
EMAIL:marie.dubois@example.com
TEL:+33-1-45-67-89-01
ADR:;;Lyon;;;France;
NOTE:Climate economist specializing in carbon pricing. Former OECD advisor (2018-2020) focusing on climate policy in developing countries.
X-CIRED-HISTORY:Marie completed her postdoc at CIRED from 2015-2018, working on carbon market mechanisms under Dr. Guesnerie's supervision.
[Plus all consent tracking fields]
END:VCARD
```

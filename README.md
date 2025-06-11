# CIRED Alumni Directory

This repository contains a set of Python scripts for building a contact directory of researchers currently or formely affiliated with **CIRED**. Each scraper collects data from a different source, exports the results as vCards, and a final merge step deduplicates the cards into a single file.

## Repository layout

```
1_Scraping/        scraping scripts
    askCIRED.py    - scrape cired.fr for staff and alumni
    askHAL.py      - query the HAL API for CIRED authors
    askREPEC.py    - scrape RePEc for member/alumni data
    merge.py       - merge the individual vCard files
requirements.txt   Python package requirements
schema.md          vCard schema and custom field documentation
```

## Quick start

1. Create a Python 3 environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run each scraper to generate `askCIRED.vcf`, `askHAL.vcf` and `askREPEC.vcf` (and accompanying CSV files where applicable):
   ```bash
   python 1_Scraping/askCIRED.py
   python 1_Scraping/askHAL.py
   python 1_Scraping/askREPEC.py
   ```
3. Merge the resulting cards into `merged.vcf`:
   ```bash
   python 1_Scraping/merge.py
   ```

See **schema.md** for the full list of vCard fields and custom extensions used in the directory.

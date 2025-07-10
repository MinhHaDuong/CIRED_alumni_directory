# CIRED Alumni Directory

This repository contains a set of Python scripts for building a directory of researchers currently or formely affiliated with **CIRED**.

1. Scrapers collects data from a different source, exports the results as vCards.
2. The merge step deduplicates the cards into a single file.
3. The enrich step search the web for emails, affiliations, homepages
4. The clean step removes obsolete emails, verifies URLs, deduplicates

GRPD Legitimate Use clause: There was a collective consensus at the 50 years anniversary conference that we, as the alumni community, should have a directory and an association.

GRPD Proportionality clause: See **schema.md** for the information collected, which is limited to what a professional alumni directory normally includes.

GRPD Opposition right: The merge step will not process entries for persons with FN listed in the `blacklist.txt` file.

Contact: <minh.ha-duong@cnrs.fr>
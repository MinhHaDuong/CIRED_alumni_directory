PY       := ./venv/bin/python3

SCRAPE_DIR := 1_Scrape
SCRAPERS := askCIRED.py askHAL.py askREPEC.py askEmail.py
SCRAPED_NAMES := askCIRED.vcf askHAL.vcf askREPEC.vcf askEmail.vcf others.vcf askNaceur.vcf
SCRAPED_FILES := $(addprefix $(SCRAPE_DIR)/, $(SCRAPED_NAMES))

MERGE_DIR := 2_Merge
MERGED_FILE := $(MERGE_DIR)/merged.vcf
MERGE_SCRIPT := $(MERGE_DIR)/merge.py

ENRICH_DIR:= 3_Enrich
ENRICHED_FILE := $(ENRICH_DIR)/cleaned.vcf
ENRICH_SCRIPT := $(ENRICH_DIR)/enrich.py

all: $(MERGED_FILE) $(ENRICHED_FILE)

$(SCRAPE_DIR)/%.vcf:
	$(PY) $(SCRAPE_DIR)/%.py

$(MERGED_FILE): $(MERGE_SCRIPT) $(SCRAPED_FILES)
	$(PY) $(MERGE_SCRIPT)

$(ENRICHED_FILE): $(MERGED_FILE) $(ENRICH_SCRIPT)
	cat $(MERGED_FILE) | $(PY) $(ENRICH_SCRIPT) > $@

# Lancer la suite de tests
.PHONY: test
test: $(MERGED_FILE)
	pytest -q

.PHONY: scrape
scrape: $(SCRAPED_FILES)
	@echo "Scraping completed. Files are located in $(SCRAPE_DIR)/"

.PRECIOUS: $(SCRAPED_FILES) $(MERGED_FILE) $(ENRICHED_FILE)

# Nettoyage
.PHONY: clean
clean:
	rm -f $(MERGED_FILE) $(ENRICHED_FILE)


PY       := ./venv/bin/python3

SCRAPE_DIR := 1_Scrape
SCRAPERS := askCIRED.py askHAL.py askREPEC.py askEmail.py
SCRAPED_NAMES := askCIRED.vcf askHAL.vcf askREPEC.vcf askEmail.vcf others.vcf askNaceur.vcf
SCRAPED_FILES := $(addprefix $(SCRAPE_DIR)/, $(SCRAPED_NAMES))

MERGE_DIR := 2_Merge
MERGED_FILE := $(MERGE_DIR)/merged.vcf
MERGE_SCRIPT := $(MERGE_DIR)/merge.py

ENRICH_DIR := 3_Enrich
ENRICHED_FILE := $(ENRICH_DIR)/enriched.vcf
ENRICH_SCRIPT := $(ENRICH_DIR)/enrich.py

CLEAN_DIR := 4_Clean
CLEANED_FILE := $(CLEAN_DIR)/cleaned.vcf
CLEAN_SCRIPT := $(CLEAN_DIR)/clean.py

REPORT_DIR := 5_Report
REPORT_SCRIPT := $(REPORT_DIR)/no_email.py

all: $(MERGED_FILE) $(ENRICHED_FILE) $(CLEANED_FILE)

$(SCRAPE_DIR)/%.vcf:
	$(PY) $(SCRAPE_DIR)/%.py

$(MERGED_FILE): $(SCRAPED_FILES)
	$(PY) $(MERGE_SCRIPT)

$(ENRICHED_FILE): $(MERGED_FILE)
	cat $(MERGED_FILE) | $(PY) $(ENRICH_SCRIPT) --exec > $@

$(CLEANED_FILE): $(ENRICHED_FILE)
	cat $(ENRICHED_FILE) | $(PY) $(CLEAN_SCRIPT) > $@

# Lancer la suite de tests
.PHONY: test
test: $(MERGED_FILE)
	pytest -q

.PHONY: scrape
scrape: $(SCRAPED_FILES)
	@echo "Scraping completed. Files are located in $(SCRAPE_DIR)/"

# Generate reports
.PHONY: report-no-email
report-no-email: $(CLEANED_FILE)
	cat $(CLEANED_FILE) | $(PY) $(REPORT_SCRIPT) --sort

.PHONY: report-no-email-count
report-no-email-count: $(CLEANED_FILE)
	cat $(CLEANED_FILE) | $(PY) $(REPORT_SCRIPT) --count-only

.PHONY: reports
reports: report-no-email
	@echo "Reports generated."

.PRECIOUS: $(SCRAPED_FILES) $(MERGED_FILE) $(ENRICHED_FILE) $(CLEANED_FILE)

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all                    - Run the full pipeline: scrape → merge → enrich → clean"
	@echo "  scrape                 - Run all scrapers to collect vCard data"
	@echo "  test                   - Run the test suite"
	@echo "  report-no-email        - List people without email addresses"
	@echo "  report-no-email-count  - Count people without email addresses"
	@echo "  reports                - Generate all reports"
	@echo "  clean                  - Remove cleaned.vcf"
	@echo "  cleaner                - Remove merged.vcf, enriched.vcf, and cleaned.vcf"
	@echo "  cleanest               - Remove all generated files including scraped data"

# Nettoyage
.PHONY: clean cleaner cleanest
clean:
	rm -f $(CLEANED_FILE)

cleaner: clean
	rm -f $(MERGED_FILE) $(ENRICHED_FILE)

cleanest: cleaner
	rm -f $(SCRAPED_FILES)

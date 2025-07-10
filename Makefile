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
UNWRAPPED_FILE := $(ENRICH_DIR)/unwrapped.vcf
UNWRAP_SCRIPT := $(ENRICH_DIR)/unwrap.awk

CLEAN_DIR := 4_Clean
CLEANED_FILE := $(CLEAN_DIR)/cleaned.vcf
CLEAN_SCRIPT := $(CLEAN_DIR)/clean.py
FIX_SCRIPT := $(CLEAN_DIR)/fix_emails.py
FIXED_FILE := $(CLEAN_DIR)/fixed.vcf

REPORT_DIR := 5_Report
REPORT_SCRIPT := $(REPORT_DIR)/no_email.py

all: $(MERGED_FILE) $(ENRICHED_FILE) $(UNWRAPPED_FILE) $(CLEANED_FILE) $(FIXED_FILE)

$(SCRAPE_DIR)/%.vcf:
	@echo "Scraping target $@ not implemented"

$(MERGED_FILE): $(SCRAPED_FILES)
	$(PY) $(MERGE_SCRIPT) < /dev/null > $@

$(ENRICHED_FILE): $(MERGED_FILE)
	$(PY) $(ENRICH_SCRIPT) --exec < $< > $@

$(UNWRAPPED_FILE): $(ENRICHED_FILE)
	awk -f $(UNWRAP_SCRIPT) < $< > $@

$(CLEANED_FILE): $(UNWRAPPED_FILE)
	$(PY) $(CLEAN_SCRIPT) < $< > $@

$(FIXED_FILE): $(CLEANED_FILE)
	$(PY) $(FIX_SCRIPT) < $< > $@ || cp $< $@

report: $(FIXED_FILE)
	$(PY) $(REPORT_SCRIPT) < $<

.PRECIOUS: $(MERGED_FILE) $(ENRICHED_FILE) $(UNWRAPPED_FILE) $(CLEANED_FILE)

clean:
	rm -f $(MERGED_FILE) $(ENRICHED_FILE) $(UNWRAPPED_FILE) $(CLEANED_FILE) $(FIXED_FILE)

.PHONY: all report clean

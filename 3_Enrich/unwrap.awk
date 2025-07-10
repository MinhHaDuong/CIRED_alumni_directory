#!/usr/bin/awk -f
# Simple script to remove [[ and ]] brackets anywhere in the file

{
    gsub(/\[\[/, "", $0)
    gsub(/\]\]/, "", $0)
    # Replace "," by "--"
    gsub(/,/, "--", $0)
    print
}
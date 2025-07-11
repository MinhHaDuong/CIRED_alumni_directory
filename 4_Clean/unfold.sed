# unfold.sed — Unfold VCARD lines and remove \r
# Per RFC 6350 §3.2

# Usage
# sed -f unfold.sed input.vcf > unfolded.vcf

# Load the whole file into pattern space
:a
N
$!ba

# Remove all \r characters (Windows line endings)
s/\r//g

# Unfold VCARD continuation lines (join newline + space/tab)
s/\n[ \t]/ /g


# unfold.sed — Unfold VCARD lines by removing line breaks followed by space or tab
# Per RFC 6350 §3.2

# Usage
# sed -f unfold.sed input.vcf > unfolded.vcf

# Load the whole file into pattern space
:a
N
$!ba

# Replace CRLF or LF followed by space or tab with a single space
s/\(\r\?\)\n[ \t]//g

import os
import re
import time
from scholarly import scholarly, ProxyGenerator

# Optional: Configure a proxy to avoid IP blocking during large batch pulls
# pg = ProxyGenerator()
# pg.FreeProxies()
# scholarly.use_proxy(pg)

# Resolve relative to this script's location so it works from any CWD
# (e.g. the CI runs `python scripts/download_pubs.py` from the repo root).
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_publications")
os.makedirs(output_dir, exist_ok=True)

def generate_slug(title):
    """Sanitizes the title to create a URL-safe slug for permalinks and filenames."""
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', title).lower()
    return re.sub(r'\s+', '-', clean)[:60]

print("Locating author profile...")
# Searching directly for the specified profile

# Replace with this (inserting your actual ID):
scholar_id = "9wRFbcEAAAAJ"  # e.g., 'aB1cDefAAAAJ'
print(f"Locating author profile by ID: {scholar_id}...")
author = scholarly.search_author_id(scholar_id)

author = scholarly.fill(author, sections=['publications'])

for pub in author['publications']:
    title = pub['bib'].get('title', 'Untitled')
    year_str = pub['bib'].get('pub_year', '0')
    
    # Safely convert the year string to an integer
    try:
        year = int(year_str)
    except ValueError:
        year = 0
        
    # Skip any publication prior to 2026
    if year < 2026:
        continue
    slug = generate_slug(title)
    
    # Fix 1: Ensure filename strictly follows YYYY-MM-DD
    filename = f"{year}-01-01-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"Skipping: {filename} (File already exists)")
        continue

    time.sleep(1)
    scholarly.fill(pub)
    bib = pub['bib']
    venue = bib.get('journal', bib.get('conference', bib.get('venue', 'Working Paper')))
    paper_url = pub.get('pub_url', pub.get('eprint_url', ''))
    authors = bib.get('author', 'Unknown Authors')
    
    # Fix 2: Use HTML entities instead of backslash escapes
    citation_string = f"{authors}. ({year}). &quot;{title}.&quot; <i>{venue}</i>."

    # Fix 3: Match the exact front matter fields expected by the template
    yaml_front_matter = f"""---
title: "{title}"
collection: publications
category: manuscripts
permalink: /publication/{year}-01-01-{slug}
excerpt: ''
date: {year}-01-01
venue: '{venue}'
paperurl: '{paper_url}'
citation: '{citation_string}'
---
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(yaml_front_matter)
    
    print(f"Generated: {filename}")


print("Sync complete.")

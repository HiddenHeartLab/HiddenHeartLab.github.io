import os
import re
import time
from scholarly import scholarly, ProxyGenerator

# Optional: Configure a proxy to avoid IP blocking during large batch pulls
# pg = ProxyGenerator()
# pg.FreeProxies()
# scholarly.use_proxy(pg)

output_dir = "_publications"
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
    year = pub['bib'].get('pub_year', '1900')
    slug = generate_slug(title)
    filename = f"{year}-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"Skipping: {filename} (File already exists)")
        continue

    # Fill individual publication details to retrieve full metadata
    time.sleep(1) # Basic throttle to respect Scholar's rate limits
    scholarly.fill(pub)
    bib = pub['bib']

    # Resolve publication venue
    venue = bib.get('journal', bib.get('conference', bib.get('venue', 'Preprint or Working Paper')))
    
    # Resolve URL
    paper_url = pub.get('pub_url', pub.get('eprint_url', ''))

    # Format authors for the citation string
    authors = bib.get('author', 'Unknown Authors')
    citation_string = f"{authors}. ({year}). \\\"{title}.\\\" <i>{venue}</i>."

    yaml_front_matter = f"""---
title: "{title}"
collection: publications
permalink: /publication/{year}-{slug}
excerpt: 'This paper is about...'
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

import requests
import yaml
import os

ORG_NAME = "HiddenHeartLab"
OUTPUT_FILE = "../_data/software.yml"

def fetch_repos():
    url = f"https://api.github.com/users/{ORG_NAME}/repos?sort=pushed&per_page=100"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"GitHub API returned {response.status_code}")
        
    repos = response.json()
    
    # Filter and format data
    software_list = []
    for repo in repos:
        if repo['fork']: continue # Skip forked repos
        if repo['archived']: continue # Skip archived repos
        if "github" in repo['name']: continue
        
        software_list.append({
            'name': repo['name'],
            'url': repo['html_url'],
            'description': repo['description'] or "",
            'stars': repo['stargazers_count'],
            'forks': repo['forks_count'],
            'language': repo['language'],
            'updated': repo['updated_at'].split('T')[0]
        })
        
    # Sort by stars (descending)
    software_list.sort(key=lambda x: x['stars'], reverse=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(software_list, f, sort_keys=False)
        
    print(f"Updated {len(software_list)} repositories.")

if __name__ == "__main__":
    fetch_repos()

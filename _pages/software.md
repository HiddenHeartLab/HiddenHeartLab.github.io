---
title: "software"
permalink: /software/
layout: single
author_profile: true
redirect_from: 
  - /software
  - /software.html
---

Here are the open-source projects developed by our lab.

<div class="software-grid">
  {% for repo in site.data.software %}
    <div class="software-card">
      <h3><a href="{{ repo.url }}">{{ repo.name }}</a></h3>
      <p>{{ repo.description }}</p>
      <div class="repo-stats">
        <span>⭐ {{ repo.stars }}</span>
        <span>🍴 {{ repo.forks }}</span>
        {% if repo.language %}<span>🟡 {{ repo.language }}</span>{% endif %}
      </div>
    </div>
  {% endfor %}
</div>

<style>
.software-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.software-card {
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 16px;
  background: white;
}
.repo-stats {
  margin-top: 10px;
  font-size: 0.85em;
  color: #666;
}
</style>

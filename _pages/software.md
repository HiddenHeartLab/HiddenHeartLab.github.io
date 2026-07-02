---
title: ""
permalink: /software/
layout: single
author_profile: false
redirect_from: 
  - /software
  - /software.html
---

<div class="hh-page-head">
  <h1>Software</h1>
  <p>Here are the open-source projects developed by our lab.</p>
</div>

<div class="software-grid">
  {% for repo in site.data.software %}
    <div class="software-card">
      <h3><a href="{{ repo.url }}">{{ repo.name }}</a></h3>
      <p>{{ repo.description }}</p>
      <div class="repo-stats">
        <span>★ {{ repo.stars }}</span>
        <span>⑂ {{ repo.forks }}</span>
        {% if repo.language %}<span>● {{ repo.language }}</span>{% endif %}
      </div>
    </div>
  {% endfor %}
</div>

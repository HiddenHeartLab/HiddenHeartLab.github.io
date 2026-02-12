---
permalink: /
title: ""
author_profile: false
redirect_from: 
  - /about/
  - /about.html
---
<img src="https://raw.githubusercontent.com/HiddenHeartLab/.github/refs/heads/main/profile/thhl_logo.png" alt="logo" width="300">

A collaboration between the research groups of [Francisco Sahli Costabal](https://fsahli.github.io) 🇨🇱 and [Simone Pezzuto](https://mbm.maths.unitn.it/faculty/simone_pezzuto.html) 🇮🇹

> Our mission is to unveil the cardiac structure and function from affordable an non-invasive data


## News

<div class="linkedin-feed">
  {% for post in site.data.linkedin %}
    <div class="linkedin-post-container">
      {% if post.caption %}
        <p class="post-caption">{{ post.caption | markdownify | remove: '<p>' | remove: '</p>' }}</p>
      {% endif %}
      
      <iframe 
        src="https://www.linkedin.com/embed/feed/update/{{ post.urn }}" 
        height="{{ post.height }}" 
        width="100%" 
        frameborder="0" 
        allowfullscreen="" 
        title="{{ post.title }}"
        loading="lazy">
      </iframe>
    </div>
  {% endfor %}
</div>

<style>
/* Optional: Makes the feed look neat */
.linkedin-feed {
  display: flex;
  flex-direction: column;
  align-items: center; /* Centers the posts */
  gap: 2rem; /* Adds space between posts */
}

.linkedin-post-container {
  width: 100%;
  max-width: 550px; /* Prevents them from getting too wide on desktop */
}

.post-caption {
  font-weight: bold;
  margin-bottom: 0.5rem;
}
</style>

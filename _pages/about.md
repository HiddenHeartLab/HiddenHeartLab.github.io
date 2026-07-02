---
permalink: /
title: ""
excerpt: "A collaboration between the research groups of Francisco Sahli Costabal and Simone Pezzuto."
author_profile: false
hero_banner: true
redirect_from: 
  - /about/
  - /about.html
---

<section class="hh-hero">
  <p class="hh-hero__pis">A collaboration between the research groups of <a href="https://fsahli.github.io">Francisco Sahli Costabal</a> 🇨🇱 and <a href="https://mbm.maths.unitn.it/faculty/simone_pezzuto.html">Simone Pezzuto</a> 🇮🇹</p>
  <blockquote class="hh-mission">Our mission is to unveil the cardiac structure and function from affordable an non-invasive data</blockquote>
</section>

<section class="hh-news" id="news">
  <div class="hh-section__head">
    <h2>News</h2>
  </div>

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
</section>

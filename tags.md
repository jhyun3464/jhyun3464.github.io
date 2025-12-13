---
layout: single
title: "태그"
permalink: /tags/
author_profile: true
---

<div class="tags-container">
  {% for tag in site.tags %}
    <a href="#{{ tag[0] | slugify }}" style="font-size: 1.2em; margin-right: 15px;">
      {{ tag[0] }} ({{ tag[1].size }})
    </a>
  {% endfor %}
</div>

<hr>

{% for tag in site.tags %}
  <h2 id="{{ tag[0] | slugify }}">{{ tag[0] }}</h2>
  <ul>
    {% for post in tag[1] %}
      <li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <small>({{ post.date | date_to_string }})</small></li>
    {% endfor %}
  </ul>
{% endfor %}

---
layout: page
permalink: /cv/
title: cv
description:
nav: false # hidden from the menu; the CV button on the home page opens pdf/CV.pdf
nav_order: 6
---

<p class="cv-actions">
  <a class="btn-cv" href="{{ '/pdf/CV.pdf' | relative_url }}">Download CV (PDF)</a>
</p>

<object class="cv-embed" data="{{ '/pdf/CV.pdf' | relative_url }}" type="application/pdf">
  <p>Your browser cannot show the PDF here. <a href="{{ '/pdf/CV.pdf' | relative_url }}">Open the CV</a>.</p>
</object>

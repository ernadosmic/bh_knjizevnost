---
layout: default
title: "Pretraga"
description: "Pretražite puni tekst arhiva."
permalink: /pretraga/
---
<section class="page-heading">
  <p class="eyebrow">Istraživanje</p>
  <h1>Pretraga arhiva</h1>
  <p class="lede">Pretražite naslove, autore i puni tekst djela.</p>
</section>
<div id="search" class="search-interface"></div>
<noscript><p>Pretraga zahtijeva JavaScript. Djela možete pregledati na stranici <a href="{{ '/djela/' | relative_url }}">Djela</a>.</p></noscript>
<link href="{{ '/pagefind/pagefind-ui.css' | relative_url }}" rel="stylesheet">
<script src="{{ '/pagefind/pagefind-ui.js' | relative_url }}"></script>
<script>window.addEventListener('DOMContentLoaded', function () { if (window.PagefindUI) new PagefindUI({ element: '#search', showSubResults: true }); });</script>

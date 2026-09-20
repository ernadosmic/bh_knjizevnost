---
layout: default
title: "Pretraga"
description: "Pretražite puni tekst arhiva."
permalink: /pretraga/
---

<header class="page-heading">
  <h1>Pretraga</h1>
  <p class="lede">Pretražuje naslove, autore i puni tekst svih djela.</p>
</header>
<div id="search" class="search-interface"></div>
<noscript><p class="empty-state">Pretraga zahtijeva JavaScript. Djela možete pregledati na stranici <a href="{{ '/djela/' | relative_url }}">Djela</a>.</p></noscript>
<link href="{{ '/pagefind/pagefind-ui.css' | relative_url }}" rel="stylesheet">
<script src="{{ '/pagefind/pagefind-ui.js' | relative_url }}"></script>
<script>window.addEventListener('DOMContentLoaded', function () { if (window.PagefindUI) new PagefindUI({ element: '#search', showSubResults: true, translations: { placeholder: 'Pretražite arhiv', zero_results: 'Nema rezultata za [SEARCH_TERM]' } }); });</script>

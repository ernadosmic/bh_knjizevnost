(function () {
  var list = document.getElementById('work-list');
  if (!list) return;
  var filter = document.getElementById('work-filter');
  var type = document.getElementById('type-filter');
  var sort = document.getElementById('sort-works');
  var empty = document.getElementById('work-empty');
  function update() {
    var query = (filter.value || '').toLowerCase().trim();
    var selectedType = type.value;
    var cards = Array.prototype.slice.call(list.querySelectorAll('.work-card'));
    cards.sort(function (a, b) {
      var key = sort.value;
      return (a.dataset[key] || '').localeCompare(b.dataset[key] || '', 'bs', { numeric: true });
    });
    var visible = 0;
    cards.forEach(function (card) {
      var matches = (!query || card.dataset.title.indexOf(query) >= 0 || card.dataset.author.indexOf(query) >= 0) && (!selectedType || card.dataset.type === selectedType);
      card.hidden = !matches;
      if (matches) visible += 1;
      list.appendChild(card);
    });
    empty.hidden = visible !== 0;
  }
  [filter, type, sort].forEach(function (control) { control.addEventListener('input', update); control.addEventListener('change', update); });
  update();
}());

(function () {
    var root = document.querySelector('[data-reader-root]');
    if (!root) return;
    var saved = JSON.parse(localStorage.getItem('bhknj-reader') || '{}');
    function apply() {
        root.dataset.readerSize = saved.size || 'default';
        root.dataset.readerTheme = saved.theme || 'light';
    }
    document.querySelectorAll('[data-reader-size]').forEach(function (button) {
        button.addEventListener('click', function () { saved.size = button.dataset.readerSize; localStorage.setItem('bhknj-reader', JSON.stringify(saved)); apply(); });
    });
    document.querySelectorAll('[data-reader-theme]').forEach(function (button) {
        button.addEventListener('click', function () { saved.theme = button.dataset.readerTheme; localStorage.setItem('bhknj-reader', JSON.stringify(saved)); apply(); });
    });
    apply();
}());

(function () {
    var root = document.documentElement;
    var STORE = 'bhknj-reader';
    var pref = {};
    try { pref = JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { pref = {}; }

    function mark(attribute, value) {
        document.querySelectorAll('[' + attribute + ']').forEach(function (button) {
            button.setAttribute('aria-pressed', button.getAttribute(attribute) === value ? 'true' : 'false');
        });
    }

    function apply() {
        var size = pref.size || 'default';
        var theme = pref.theme || 'light';
        root.setAttribute('data-reader-size', size);
        root.setAttribute('data-reader-theme', theme);
        mark('data-reader-size', size);
        mark('data-reader-theme', theme);
    }

    function bind(attribute, key) {
        document.querySelectorAll('[' + attribute + ']').forEach(function (button) {
            button.addEventListener('click', function () {
                pref[key] = button.getAttribute(attribute);
                try { localStorage.setItem(STORE, JSON.stringify(pref)); } catch (e) { }
                apply();
            });
        });
    }

    bind('data-reader-size', 'size');
    bind('data-reader-theme', 'theme');
    apply();

    // The settings popover is a <details>, so it opens without JS; JS only
    // adds the conveniences people expect from a popover.
    var panel = document.querySelector('[data-reader]');
    if (panel) {
        document.addEventListener('click', function (event) {
            if (panel.open && !panel.contains(event.target)) panel.open = false;
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && panel.open) {
                panel.open = false;
                panel.querySelector('summary').focus();
            }
        });
    }

    var progress = document.querySelector('[data-progress]');
    var text = document.querySelector('.work-text');
    if (progress && text) {
        var ticking = false;
        var update = function () {
            ticking = false;
            var start = text.offsetTop;
            var span = text.offsetHeight - window.innerHeight + 120;
            var read = window.scrollY - start + 120;
            var ratio = span > 0 ? read / span : (window.scrollY > start ? 1 : 0);
            progress.style.width = Math.max(0, Math.min(1, ratio)) * 100 + '%';
        };
        var schedule = function () {
            if (ticking) return;
            ticking = true;
            window.requestAnimationFrame(update);
        };
        window.addEventListener('scroll', schedule, { passive: true });
        window.addEventListener('resize', schedule);
        update();
    }
}());

document.addEventListener('DOMContentLoaded', function () {
    var checkbox = document.getElementById('completed');
    var fields = document.getElementById('completed-fields');
    if (!checkbox || !fields) return;

    function toggle() {
        fields.style.display = checkbox.checked ? '' : 'none';
    }

    checkbox.addEventListener('change', toggle);
    toggle();
});

document.addEventListener('DOMContentLoaded', function () {
    var select = document.getElementById('category');
    var input = document.getElementById('new-category');
    if (!select || !input) return;

    function toggle() {
        var creating = select.value === '__new__';
        input.classList.toggle('d-none', !creating);
        input.required = creating;
    }

    select.addEventListener('change', toggle);
    toggle();
});

document.addEventListener('DOMContentLoaded', function () {
    var container = document.getElementById('categories');
    if (!container) return;

    var STORAGE_KEY = 'bucketlist.collapsed';

    function load() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch (e) {
            return {};
        }
    }

    function save(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
        }
    }

    var panels = container.querySelectorAll('.category-body');
    var state = load();

    Array.prototype.forEach.call(panels, function (panel) {
        if (!state[panel.getAttribute('data-key')]) return;

        panel.classList.remove('show');
        var toggle = container.querySelector('[data-target="#' + panel.id + '"]');
        if (toggle) {
            toggle.classList.add('collapsed');
            toggle.setAttribute('aria-expanded', 'false');
        }
    });

    if (window.jQuery) {
        window.jQuery(panels).on('shown.bs.collapse', function () {
            var current = load();
            delete current[this.getAttribute('data-key')];
            save(current);
        }).on('hidden.bs.collapse', function () {
            var current = load();
            current[this.getAttribute('data-key')] = 1;
            save(current);
        });
    }
});

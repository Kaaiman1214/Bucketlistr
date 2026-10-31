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
    var searching = container.hasAttribute('data-searching');

    Array.prototype.forEach.call(panels, function (panel) {
        if (searching) return;
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

document.addEventListener('DOMContentLoaded', function () {
    var checkbox = document.getElementById('is-country');
    var fields = document.getElementById('country-fields');
    var select = document.getElementById('country');
    var title = document.getElementById('title');
    if (!checkbox || !fields || !select) return;

    function toggle() {
        fields.style.display = checkbox.checked ? '' : 'none';
        select.required = checkbox.checked;
    }

    select.addEventListener('change', function () {
        if (title && !title.value.trim() && select.value) {
            title.value = select.options[select.selectedIndex].text;
        }
    });

    checkbox.addEventListener('change', toggle);
    toggle();
});

document.addEventListener('change', function (event) {
    var box = event.target;
    if (!box.classList || !box.classList.contains('checklist-box')) return;

    var wanted = box.checked;
    box.disabled = true;

    fetch(box.getAttribute('data-url'), {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ done: wanted })
    }).then(function (res) {
        if (!res.ok || res.redirected) throw new Error('not saved');
        return res.json();
    }).then(function (data) {
        var bar = document.getElementById('progress-bar');
        var text = document.getElementById('progress-text');
        if (bar) {
            bar.setAttribute('data-percent', data.percent);
            bar.style.width = data.percent + '%';
            bar.setAttribute('aria-valuenow', data.percent);
        }
        if (text) {
            text.textContent = data.checked + '/' + data.total + ' \u00b7 ' + data.percent + '%';
        }
    }).catch(function () {
        box.checked = !wanted;
        alert('Could not save that change. Are you still logged in?');
    }).then(function () {
        box.disabled = false;
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var bars = document.querySelectorAll('.progress-bar[data-percent]');
    Array.prototype.forEach.call(bars, function (bar) {
        bar.style.width = bar.getAttribute('data-percent') + '%';
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var checkbox = document.getElementById('has-checklist');
    var fields = document.getElementById('checklist-fields');
    var rows = document.getElementById('checklist-rows');
    var template = document.getElementById('checklist-template');
    if (!checkbox || !fields || !rows || !template) return;

    function lastKey() {
        var keys = rows.querySelectorAll('input[name="entry_keys"]');
        return keys[keys.length - 1].value;
    }

    var counter = parseInt(lastKey().slice(1), 10) || 0;

    function addRow() {
        counter += 1;
        rows.insertAdjacentHTML('beforeend', template.innerHTML.replace(/__KEY__/g, 'n' + counter));
    }

    function ensureBlankRow() {
        var texts = rows.querySelectorAll('.checklist-text');
        if (!texts.length || texts[texts.length - 1].value.trim() !== '') addRow();
    }

    function toggle() {
        fields.style.display = checkbox.checked ? '' : 'none';
        if (checkbox.checked) ensureBlankRow();
    }

    rows.addEventListener('input', ensureBlankRow);
    checkbox.addEventListener('change', toggle);
    toggle();
});

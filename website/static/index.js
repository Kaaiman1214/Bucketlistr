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

document.addEventListener('DOMContentLoaded', function () {
    var carousel = document.getElementById('photo-carousel');
    if (!carousel || !window.jQuery) return;

    var slides = carousel.querySelectorAll('.carousel-item');
    var counter = document.getElementById('photo-counter');
    if (slides.length < 2) return;

    window.jQuery(carousel).on('slid.bs.carousel', function () {
        var active = carousel.querySelector('.carousel-item.active');
        var index = Array.prototype.indexOf.call(slides, active);
        if (counter) counter.textContent = (index + 1) + ' / ' + slides.length;
    });

    var startX = null;
    carousel.addEventListener('touchstart', function (event) {
        startX = event.touches[0].clientX;
    }, { passive: true });
    carousel.addEventListener('touchend', function (event) {
        if (startX === null) return;
        var distance = event.changedTouches[0].clientX - startX;
        startX = null;
        if (Math.abs(distance) < 40) return;
        window.jQuery(carousel).carousel(distance < 0 ? 'next' : 'prev');
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var list = document.getElementById('photo-list');
    var removed = document.getElementById('removed-photos');
    if (!list || !removed) return;

    list.addEventListener('click', function (event) {
        var button = event.target.closest('button');
        var card = button && button.closest('.photo-card');
        if (!card) return;

        if (button.classList.contains('photo-left')) {
            if (card.previousElementSibling) list.insertBefore(card, card.previousElementSibling);
        } else if (button.classList.contains('photo-right')) {
            if (card.nextElementSibling) list.insertBefore(card.nextElementSibling, card);
        } else if (button.classList.contains('photo-remove')) {
            var photoId = card.getAttribute('data-photo-id');
            if (photoId) {
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'remove_photos';
                input.value = photoId;
                removed.appendChild(input);
            }
            list.removeChild(card);
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var input = document.getElementById('photos');
    var list = document.getElementById('photo-list');
    var template = document.getElementById('photo-card-template');
    var status = document.getElementById('photo-status');
    if (!input || !list || !template || !status) return;

    var form = input.form;
    var hint = status.textContent;
    var busy = 0;

    function setBusy(change) {
        busy += change;
        var buttons = form.querySelectorAll('button[type="submit"]');
        Array.prototype.forEach.call(buttons, function (button) {
            button.disabled = busy > 0;
        });
    }

    function addCard(photo) {
        var html = template.innerHTML
            .split('__TOKEN__').join('new:' + photo.filename)
            .split('__URL__').join(photo.url);
        list.insertAdjacentHTML('beforeend', html);
    }

    function uploadOne(file) {
        var data = new FormData();
        data.append('photos', file);
        return fetch(input.getAttribute('data-url'), {
            method: 'POST',
            credentials: 'same-origin',
            body: data
        }).then(function (res) {
            return res.json().catch(function () { return {}; }).then(function (body) {
                if (!res.ok || res.redirected || !body.photos) {
                    throw new Error(body.error || 'Upload failed. Are you still logged in?');
                }
                body.photos.forEach(addCard);
            });
        });
    }

    input.addEventListener('change', function () {
        var files = Array.prototype.slice.call(input.files);
        input.value = '';
        if (!files.length) return;

        var errors = [];
        var finished = 0;
        status.className = 'form-text text-muted';
        setBusy(1);

        files.reduce(function (chain, file) {
            return chain.then(function () {
                status.textContent = 'Uploading ' + (finished + 1) + ' of ' + files.length + '...';
                return uploadOne(file).catch(function (error) {
                    errors.push(file.name + ': ' + error.message);
                }).then(function () {
                    finished += 1;
                });
            });
        }, Promise.resolve()).then(function () {
            if (errors.length) {
                status.className = 'form-text text-danger';
                status.textContent = errors.join(' ');
            } else {
                status.textContent = hint;
            }
            setBusy(-1);
        });
    });
});

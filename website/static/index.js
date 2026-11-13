document.addEventListener('DOMContentLoaded', function () {
    var select = document.getElementById('status');
    var fields = document.getElementById('completed-fields');
    if (!select || !fields) return;

    function toggle() {
        fields.style.display = select.value === 'completed' ? '' : 'none';
    }

    select.addEventListener('change', toggle);
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

document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('sidebar-toggle');
    var backdrop = document.getElementById('sidebar-backdrop');
    if (!toggle) return;

    var STORAGE_KEY = 'bucketlist.sidebar';
    var desktop = window.matchMedia('(min-width: 992px)');

    toggle.addEventListener('click', function () {
        if (desktop.matches) {
            var collapsed = document.body.classList.toggle('sidebar-collapsed');
            try {
                localStorage.setItem(STORAGE_KEY, collapsed ? 'collapsed' : 'open');
            } catch (e) {
            }
        } else {
            document.body.classList.toggle('sidebar-open');
        }
    });

    if (backdrop) {
        backdrop.addEventListener('click', function () {
            document.body.classList.remove('sidebar-open');
        });
    }

    function expand(key) {
        var panel = document.getElementById('category-' + key);
        if (panel && !panel.classList.contains('show') && window.jQuery) {
            window.jQuery(panel).collapse('show');
        }
    }

    var links = document.querySelectorAll('.sidebar-link[data-key]');
    Array.prototype.forEach.call(links, function (link) {
        link.addEventListener('click', function () {
            expand(link.getAttribute('data-key'));
            document.body.classList.remove('sidebar-open');
        });
    });

    if (window.location.hash.indexOf('#section-') === 0) {
        expand(window.location.hash.slice('#section-'.length));
    }

    var sections = document.querySelectorAll('section[id^="section-"]');
    if (!sections.length) return;

    var waiting = false;

    function highlight() {
        waiting = false;
        var current = sections[0];
        Array.prototype.forEach.call(sections, function (section) {
            if (section.getBoundingClientRect().top <= 90) current = section;
        });
        var key = current.id.slice('section-'.length);
        Array.prototype.forEach.call(links, function (link) {
            link.classList.toggle('active', link.getAttribute('data-key') === key);
        });
    }

    window.addEventListener('scroll', function () {
        if (!waiting) {
            waiting = true;
            window.requestAnimationFrame(highlight);
        }
    });

    if (window.jQuery) {
        window.jQuery('.category-body').on('shown.bs.collapse hidden.bs.collapse', highlight);
    }
    highlight();
});

document.addEventListener('DOMContentLoaded', function () {
    var list = document.getElementById('category-list');
    var status = document.getElementById('category-status');
    if (!list || !status) return;

    var hint = status.textContent;
    var url = list.getAttribute('data-url');
    var dragging = null;
    var changed = false;
    var timer = null;

    function currentOrder() {
        return Array.prototype.map.call(list.children, function (row) {
            return parseInt(row.getAttribute('data-id'), 10);
        });
    }

    function save() {
        status.className = 'form-text text-muted mt-2';
        status.textContent = 'Saving...';
        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: currentOrder() })
        }).then(function (res) {
            if (!res.ok || res.redirected) throw new Error('not saved');
            status.textContent = 'Saved.';
        }).catch(function () {
            status.className = 'form-text text-danger mt-2';
            status.textContent = 'Could not save the order. Reload the page and try again.';
        }).then(function () {
            clearTimeout(timer);
            timer = setTimeout(function () {
                if (status.textContent === 'Saved.') status.textContent = hint;
            }, 2000);
        });
    }

    function onMove(event) {
        var rows = Array.prototype.slice.call(list.children);
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            if (row === dragging) continue;
            var box = row.getBoundingClientRect();
            if (event.clientY > box.top && event.clientY < box.bottom) {
                if (i < rows.indexOf(dragging)) {
                    list.insertBefore(dragging, row);
                } else {
                    list.insertBefore(dragging, row.nextSibling);
                }
                changed = true;
                break;
            }
        }
    }

    function onEnd() {
        document.removeEventListener('pointermove', onMove);
        document.removeEventListener('pointerup', onEnd);
        document.removeEventListener('pointercancel', onEnd);
        if (dragging) dragging.classList.remove('dragging');
        document.body.classList.remove('is-dragging');
        dragging = null;
        if (changed) save();
        changed = false;
    }

    list.addEventListener('pointerdown', function (event) {
        var handle = event.target.closest('.drag-handle');
        if (!handle || (event.pointerType === 'mouse' && event.button !== 0)) return;
        event.preventDefault();
        dragging = handle.closest('.category-row');
        dragging.classList.add('dragging');
        document.body.classList.add('is-dragging');
        document.addEventListener('pointermove', onMove);
        document.addEventListener('pointerup', onEnd);
        document.addEventListener('pointercancel', onEnd);
    });

    list.addEventListener('keydown', function (event) {
        var handle = event.target.closest('.drag-handle');
        if (!handle || (event.key !== 'ArrowUp' && event.key !== 'ArrowDown')) return;
        event.preventDefault();
        var row = handle.closest('.category-row');
        var up = event.key === 'ArrowUp';
        var neighbour = up ? row.previousElementSibling : row.nextElementSibling;
        if (!neighbour) return;
        list.insertBefore(row, up ? neighbour : neighbour.nextSibling);
        handle.focus();
        save();
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('bulk-form');
    if (!form) return;

    var count = document.getElementById('bulk-count');
    var deleteButton = document.getElementById('bulk-delete');
    var editButton = document.getElementById('bulk-edit');
    var selectAll = document.getElementById('bulk-all');

    function boxes() {
        return Array.prototype.slice.call(form.querySelectorAll('.tile-select'));
    }

    function update() {
        var checked = 0;
        boxes().forEach(function (box) {
            var tile = box.closest('.tile');
            if (tile) tile.classList.toggle('selected', box.checked);
            if (box.checked) checked += 1;
        });
        Array.prototype.forEach.call(form.querySelectorAll('.category-select'), function (box) {
            var tiles = box.closest('section').querySelectorAll('.tile-select');
            var ticked = Array.prototype.filter.call(tiles, function (tile) { return tile.checked; }).length;
            box.checked = tiles.length > 0 && ticked === tiles.length;
            box.indeterminate = ticked > 0 && ticked < tiles.length;
        });
        count.textContent = checked + ' selected';
        deleteButton.disabled = checked === 0;
        editButton.disabled = checked === 0;
        selectAll.textContent = checked > 0 && checked === boxes().length ? 'Unselect all' : 'Select all';
        return checked;
    }

    function setSelecting(on) {
        form.classList.toggle('selecting', on);
        if (!on) {
            boxes().forEach(function (box) { box.checked = false; });
            update();
        }
        try {
            var url = new URL(window.location.href);
            if (on) {
                url.searchParams.set('select', '1');
            } else {
                url.searchParams.delete('select');
            }
            window.history.replaceState(null, '', url);
        } catch (e) {
        }
    }

    form.addEventListener('click', function (event) {
        if (!form.classList.contains('selecting')) return;
        var tile = event.target.closest('.tile');
        if (!tile || event.target.classList.contains('tile-select')) return;
        event.preventDefault();
        var box = tile.querySelector('.tile-select');
        if (box) {
            box.checked = !box.checked;
            update();
        }
    });

    form.addEventListener('change', function (event) {
        var target = event.target;
        if (target.classList.contains('category-select')) {
            Array.prototype.forEach.call(target.closest('section').querySelectorAll('.tile-select'), function (tile) {
                tile.checked = target.checked;
            });
            update();
        } else if (target.classList.contains('tile-select')) {
            update();
        }
    });

    selectAll.addEventListener('click', function () {
        var everything = boxes();
        var allSelected = everything.length > 0 && everything.every(function (box) { return box.checked; });
        everything.forEach(function (box) { box.checked = !allSelected; });
        update();
    });

    document.getElementById('bulk-cancel').addEventListener('click', function () {
        setSelecting(false);
    });

    form.addEventListener('submit', function (event) {
        var checked = update();
        var editing = event.submitter && event.submitter.id === 'bulk-edit';
        var question = 'Delete ' + checked + ' item' + (checked === 1 ? '' : 's') + '? This cannot be undone.';
        if (!checked || (!editing && !window.confirm(question))) event.preventDefault();
    });

    if (new URLSearchParams(window.location.search).get('select') === '1') {
        setSelecting(true);
    }
    update();
});

document.addEventListener('DOMContentLoaded', function () {
    var box = document.getElementById('bulk-mode');
    if (!box) return;

    var title = document.getElementById('title');
    var titles = document.getElementById('titles');
    var button = document.getElementById('save-button');

    function toggle() {
        var on = box.checked;
        Array.prototype.forEach.call(document.querySelectorAll('.single-only'), function (element) {
            element.classList.toggle('d-none', on);
        });
        Array.prototype.forEach.call(document.querySelectorAll('.bulk-only'), function (element) {
            element.classList.toggle('d-none', !on);
        });
        title.required = !on;
        titles.required = on;
        button.textContent = on ? 'Add items' : 'Add item';
    }

    box.addEventListener('change', toggle);
    toggle();
});

document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('template-form');
    var toggle = document.getElementById('template-select-toggle');
    if (!form || !toggle) return;

    var count = document.getElementById('template-count');
    var addButton = document.getElementById('template-add-selected');
    var removeButton = document.getElementById('template-remove-selected');
    var addCount = document.getElementById('template-add-count');
    var removeCount = document.getElementById('template-remove-count');
    var selectAll = document.getElementById('template-all');

    function boxes() {
        return Array.prototype.slice.call(form.querySelectorAll('.tile-select'));
    }

    function update() {
        var checked = 0;
        var addable = 0;
        var removable = 0;
        boxes().forEach(function (box) {
            var tile = box.closest('.tile');
            if (tile) tile.classList.toggle('selected', box.checked);
            if (box.checked) {
                checked += 1;
                if (box.getAttribute('data-added') === '1') {
                    removable += 1;
                } else {
                    addable += 1;
                }
            }
        });
        Array.prototype.forEach.call(form.querySelectorAll('.category-select'), function (box) {
            var tiles = box.closest('section').querySelectorAll('.tile-select');
            var ticked = Array.prototype.filter.call(tiles, function (tile) { return tile.checked; }).length;
            box.disabled = tiles.length === 0;
            box.checked = tiles.length > 0 && ticked === tiles.length;
            box.indeterminate = ticked > 0 && ticked < tiles.length;
        });
        count.textContent = checked + ' selected';
        addButton.disabled = addable === 0;
        removeButton.disabled = removable === 0;
        addCount.textContent = addable ? '(' + addable + ')' : '';
        removeCount.textContent = removable ? '(' + removable + ')' : '';
        selectAll.textContent = checked > 0 && checked === boxes().length ? 'Unselect all' : 'Select all';
        return { checked: checked, addable: addable, removable: removable };
    }

    function setSelecting(on) {
        form.classList.toggle('selecting', on);
        toggle.textContent = on ? 'Stop selecting' : 'Select';
        if (!on) {
            boxes().forEach(function (box) { box.checked = false; });
        }
        update();
    }

    toggle.addEventListener('click', function () {
        setSelecting(!form.classList.contains('selecting'));
    });

    form.addEventListener('click', function (event) {
        if (!form.classList.contains('selecting')) return;
        var tile = event.target.closest('.tile');
        if (!tile || event.target.closest('summary, details, a, .tile-select')) return;
        var box = tile.querySelector('.tile-select');
        if (box) {
            box.checked = !box.checked;
            update();
        }
    });

    form.addEventListener('change', function (event) {
        var target = event.target;
        if (target.classList.contains('category-select')) {
            Array.prototype.forEach.call(target.closest('section').querySelectorAll('.tile-select'), function (tile) {
                tile.checked = target.checked;
            });
            update();
        } else if (target.classList.contains('tile-select')) {
            update();
        }
    });

    selectAll.addEventListener('click', function () {
        var everything = boxes();
        var allSelected = everything.length > 0 && everything.every(function (box) { return box.checked; });
        everything.forEach(function (box) { box.checked = !allSelected; });
        update();
    });

    document.getElementById('template-cancel').addEventListener('click', function () {
        setSelecting(false);
    });

    form.addEventListener('submit', function (event) {
        var submitter = event.submitter;
        if (!submitter) return;
        if (submitter.classList.contains('tile-remove')) {
            var question = 'Remove "' + submitter.getAttribute('data-title') + '" from your list? Its progress, photos and notes are deleted.';
            if (!window.confirm(question)) event.preventDefault();
            return;
        }
        var state = update();
        if (submitter.id === 'template-add-selected' && state.addable === 0) {
            event.preventDefault();
        } else if (submitter.id === 'template-remove-selected') {
            var many = state.removable + ' item' + (state.removable === 1 ? '' : 's');
            if (!state.removable || !window.confirm('Remove ' + many + ' from your list? Their progress, photos and notes are deleted.')) {
                event.preventDefault();
            }
        }
    });

    update();
});

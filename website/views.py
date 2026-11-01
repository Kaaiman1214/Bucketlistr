import os
import re
import secrets

from flask import (Blueprint, render_template, request, flash, redirect, url_for, abort,
                   jsonify, send_from_directory)
from flask_login import login_required, current_user
from sqlalchemy.orm import selectinload

from . import db, IMAGE_DIR, PENDING_DIR
from .countries import COUNTRIES, COUNTRY_GROUPS
from .models import (BucketItem, Category, ChecklistEntry, Photo, User, MONTH_NAMES,
                     ordered_categories)
from .images import (IMAGE_NAME, delete_image_files, image_extension, move_pending_image,
                     pending_exists)
from .utils import fold

views = Blueprint('views', __name__)

NEW_CATEGORY = '__new__'
ENTRY_KEY = re.compile(r'[en]\d+')


def get_owned_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    return item


def item_back_url(item):
    if item.has_details:
        return url_for('views.item', item_id=item.id)
    return url_for('views.home')


def item_sort_key(item):
    name = (fold(item.country_name or item.title), fold(item.title))
    if not item.completed:
        return (0, 0, 0) + name
    if item.completed_year is None:
        return (2, 0, 0) + name
    return (1, -item.completed_year, -(item.completed_month or 0)) + name


def find_category(name):
    for category in Category.query.all():
        if fold(category.name) == fold(name):
            return category
    return None


def build_sections(items):
    grouped = {}
    for item in items:
        grouped.setdefault(item.category_id, []).append(item)

    sections = []
    for category in ordered_categories():
        if category.id in grouped:
            sections.append({
                'key': str(category.id),
                'name': category.name,
                'bucket_items': sorted(grouped[category.id], key=item_sort_key),
            })
    if None in grouped:
        sections.append({
            'key': 'none',
            'name': 'Uncategorized',
            'bucket_items': sorted(grouped[None], key=item_sort_key),
        })
    return sections


def prune_empty_categories():
    for category in Category.query.filter(~Category.items.any()).all():
        db.session.delete(category)


def matches_search(item, terms):
    parts = [
        item.title,
        item.description,
        item.category.name if item.category else '',
        item.country_name,
        ' '.join(entry.text for entry in item.checklist),
    ]
    haystack = fold(' '.join(part for part in parts if part))
    return all(term in haystack for term in terms)


def blank_values():
    return {
        'title': '',
        'description': '',
        'category': '',
        'new_category': '',
        'is_country': False,
        'country': '',
        'completed': False,
        'year': '',
        'month': '',
        'has_checklist': False,
        'entries': [],
        'next_key': 'n0',
        'photo_slots': [],
        'removed_photos': [],
    }


def item_values(item):
    return {
        'title': item.title,
        'description': item.description or '',
        'category': str(item.category_id or ''),
        'new_category': '',
        'is_country': bool(item.country_code),
        'country': item.country_code or '',
        'completed': item.completed,
        'year': item.completed_year or '',
        'month': item.completed_month or '',
        'has_checklist': bool(item.checklist),
        'entries': [{'key': f'e{entry.id}', 'id': entry.id,
                     'text': entry.text, 'done': entry.done}
                    for entry in item.checklist],
        'next_key': 'n0',
        'photo_slots': [{'id': photo.id, 'name': None} for photo in item.sorted_photos],
        'removed_photos': [],
    }


def unique_ids(raw):
    ids = []
    for value in raw:
        if value.isdigit() and int(value) not in ids:
            ids.append(int(value))
    return ids


def read_entries(form, item):
    existing = {entry.id for entry in item.checklist} if item is not None else set()
    entries = []
    new_count = 0
    for key in form.getlist('entry_keys'):
        if not ENTRY_KEY.fullmatch(key):
            continue
        text = form.get(f'text_{key}', '').strip()
        done = form.get(f'done_{key}') == 'on'
        if key[0] == 'e':
            if int(key[1:]) in existing:
                entries.append({'key': key, 'id': int(key[1:]), 'text': text, 'done': done})
        elif text:
            entries.append({'key': f'n{new_count}', 'id': None, 'text': text, 'done': done})
            new_count += 1
    return entries, f'n{new_count}'


def read_photo_slots(form, item):
    existing = {photo.id for photo in item.photos} if item is not None else set()
    removed = [photo_id for photo_id in unique_ids(form.getlist('remove_photos'))
               if photo_id in existing]
    slots = []
    taken = set()
    for token in form.getlist('photo_order'):
        if token.isdigit():
            photo_id = int(token)
            if photo_id in existing and photo_id not in removed and photo_id not in taken:
                taken.add(photo_id)
                slots.append({'id': photo_id, 'name': None})
        elif token.startswith('new:'):
            name = token[4:]
            if IMAGE_NAME.fullmatch(name) and pending_exists(name) and name not in taken:
                taken.add(name)
                slots.append({'id': None, 'name': name})
    if item is not None:
        for photo in item.sorted_photos:
            if photo.id not in taken and photo.id not in removed:
                slots.append({'id': photo.id, 'name': None})
    return slots, removed


def read_item_form(form, item=None):
    entries, next_key = read_entries(form, item)
    slots, removed = read_photo_slots(form, item)
    return {
        'title': form.get('title', '').strip(),
        'description': form.get('description', '').strip(),
        'category': form.get('category', '').strip(),
        'new_category': form.get('new_category', '').strip(),
        'is_country': form.get('is_country') == 'on',
        'country': form.get('country', '').strip(),
        'completed': form.get('completed') == 'on',
        'year': form.get('completed_year', '').strip(),
        'month': form.get('completed_month', '').strip(),
        'has_checklist': form.get('has_checklist') == 'on',
        'entries': entries,
        'next_key': next_key,
        'photo_slots': slots,
        'removed_photos': removed,
    }


def validate_item(values):
    cleaned = {'year': None, 'month': None}
    cleaned.update(category=None, new_category=None)
    cleaned['country_code'] = None
    cleaned['entries'] = []

    if not values['title']:
        return 'Give the item a title.', cleaned
    if len(values['title']) > 200:
        return 'Title can be at most 200 characters.', cleaned

    choice = values['category']
    if choice and choice != NEW_CATEGORY:
        category = Category.query.get(int(choice)) if choice.isdigit() else None
        if category is None:
            return 'Choose a category.', cleaned
        cleaned['category'] = category
    else:
        name = values['new_category']
        if not name:
            return 'Choose a category or enter a name for a new one.', cleaned
        if len(name) > 100:
            return 'Category names can be at most 100 characters.', cleaned
        existing = find_category(name)
        cleaned['category'] = existing
        cleaned['new_category'] = None if existing else name

    if values['is_country']:
        if values['country'] not in COUNTRIES:
            return 'Pick a country from the list.', cleaned
        cleaned['country_code'] = values['country']

    if values['completed']:
        try:
            if values['year']:
                cleaned['year'] = int(values['year'])
                if not 1900 <= cleaned['year'] <= 2100:
                    raise ValueError
            if values['month']:
                cleaned['month'] = int(values['month'])
                if not 1 <= cleaned['month'] <= 12:
                    raise ValueError
        except ValueError:
            return 'Enter a valid year (1900-2100) and month.', cleaned
        if cleaned['month'] and not cleaned['year']:
            return 'Enter a year when you pick a month.', cleaned

    if values['has_checklist']:
        entries = [entry for entry in values['entries'] if entry['text']]
        if any(len(entry['text']) > 200 for entry in entries):
            return 'Checklist entries can be at most 200 characters.', cleaned
        if len(entries) > 1000:
            return 'A checklist can have at most 1000 entries.', cleaned
        cleaned['entries'] = entries

    return None, cleaned


def apply_item(item, values, cleaned):
    item.title = values['title']
    item.description = values['description'] or None
    category = cleaned['category']
    if category is None:
        category = Category(name=cleaned['new_category'])
        db.session.add(category)
    item.category = category
    item.country_code = cleaned['country_code']
    item.completed = values['completed']
    item.completed_year = cleaned['year'] if values['completed'] else None
    item.completed_month = cleaned['month'] if values['completed'] else None

    existing = {entry.id: entry for entry in item.checklist}
    kept = {entry['id'] for entry in cleaned['entries'] if entry['id'] is not None}
    for entry_id, entry in existing.items():
        if entry_id not in kept:
            item.checklist.remove(entry)
    for entry_values in cleaned['entries']:
        entry = existing.get(entry_values['id'])
        if entry is None:
            item.checklist.append(ChecklistEntry(text=entry_values['text'],
                                                 done=entry_values['done']))
        else:
            entry.text = entry_values['text']
            entry.done = entry_values['done']

    by_id = {photo.id: photo for photo in item.photos}
    stale = []
    for photo_id in values['removed_photos']:
        photo = by_id.pop(photo_id, None)
        if photo is not None:
            stale.append(photo.filename)
            item.photos.remove(photo)
    ordered = []
    for slot in values['photo_slots']:
        if slot['id'] is not None:
            photo = by_id.get(slot['id'])
        else:
            try:
                move_pending_image(slot['name'])
            except OSError:
                continue
            photo = Photo(filename=slot['name'])
            item.photos.append(photo)
        if photo is not None:
            ordered.append(photo)
    for position, photo in enumerate(ordered):
        photo.position = position
    return stale


def form_context():
    return {
        'months': MONTH_NAMES,
        'categories': ordered_categories(),
        'country_groups': COUNTRY_GROUPS,
    }


@views.route('/')
def home():
    if User.query.first() is None:
        return redirect(url_for('auth.sign_up'))

    items = BucketItem.query.options(selectinload(BucketItem.checklist),
                                     selectinload(BucketItem.photos)).all()
    query = request.args.get('q', '').strip()
    if query:
        terms = fold(query).split()
        items = [item for item in items if matches_search(item, terms)]
    return render_template("home.html", user=current_user,
                           sections=build_sections(items),
                           query=query, result_count=len(items))


@views.route('/new', methods=['GET', 'POST'])
@login_required
def new_item():
    values = blank_values()

    if request.method == 'POST':
        values = read_item_form(request.form)
        error, cleaned = validate_item(values)
        if error:
            flash(error, category='error')
        else:
            item = BucketItem(user_id=current_user.id)
            apply_item(item, values, cleaned)
            db.session.add(item)
            db.session.commit()
            flash('Item added!', category='success')
            return redirect(url_for('views.home'))

    return render_template("new_item.html", user=current_user, values=values,
                           back_url=url_for('views.home'), **form_context())


@views.route('/item/<int:item_id>')
def item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    return render_template("item.html", user=current_user, item=item)


@views.route('/photo/<int:photo_id>')
def photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    return send_from_directory(IMAGE_DIR, photo.filename)


@views.route('/photos/upload', methods=['POST'])
@login_required
def upload_photos():
    uploads = [storage for storage in request.files.getlist('photos')
               if storage and storage.filename]
    checked = []
    for storage in uploads:
        extension = image_extension(storage)
        if extension is None:
            return jsonify(error='Photos must be JPG, PNG, GIF or WebP images.'), 400
        checked.append((storage, extension))

    saved = []
    for storage, extension in checked:
        filename = secrets.token_hex(16) + extension
        storage.save(os.path.join(PENDING_DIR, filename))
        saved.append({'filename': filename,
                      'url': url_for('views.pending_photo', name=filename)})
    return jsonify(photos=saved)


@views.route('/photos/pending/<name>')
@login_required
def pending_photo(name):
    if not IMAGE_NAME.fullmatch(name):
        abort(404)
    return send_from_directory(PENDING_DIR, name)


@views.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = get_owned_item(item_id)
    values = item_values(item)

    if request.method == 'POST':
        values = read_item_form(request.form, item)
        error, cleaned = validate_item(values)
        if error:
            flash(error, category='error')
        else:
            stale = apply_item(item, values, cleaned)
            prune_empty_categories()
            db.session.commit()
            delete_image_files(stale)
            flash('Changes saved!', category='success')
            return redirect(item_back_url(item))

    return render_template("edit_item.html", user=current_user, item=item, values=values,
                           back_url=item_back_url(item), **form_context())


@views.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_owned_item(item_id)
    stale = [photo.filename for photo in item.photos]
    db.session.delete(item)
    prune_empty_categories()
    db.session.commit()
    delete_image_files(stale)
    flash('Item deleted.', category='success')
    return redirect(url_for('views.home'))


@views.route('/item/<int:item_id>/entry/<int:entry_id>/toggle', methods=['POST'])
@login_required
def toggle_entry(item_id, entry_id):
    item = get_owned_item(item_id)
    entry = ChecklistEntry.query.filter_by(id=entry_id, item_id=item.id).first_or_404()
    payload = request.get_json(silent=True) or {}
    entry.done = bool(payload.get('done', not entry.done))
    db.session.commit()
    return jsonify(done=entry.done, checked=item.checklist_done,
                   total=item.checklist_total, percent=item.progress_percent)

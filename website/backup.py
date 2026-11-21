import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from os import path

from . import DATA_DIR, DB_PATH, db
from .models import BucketItem, Category, ChecklistEntry, Photo, Setting, User, get_site_name

BACKUP_FORMAT = 'bucketlistr-backup'
BACKUP_VERSION = 1
REQUIRED_TABLES = {'user', 'category', 'bucket_item', 'checklist_entry', 'photo', 'setting'}


def timestamp_for_filename():
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def export_db_snapshot():
    """Return the path to a consistent, point-in-time copy of the live database.

    Safe to call while the app is handling other requests: SQLite's backup API
    takes a proper snapshot rather than a raw file copy, so a write in progress
    elsewhere can never produce a half-copied or corrupt file."""
    descriptor, temp_path = tempfile.mkstemp(suffix='.db', dir=DATA_DIR)
    os.close(descriptor)
    source = sqlite3.connect(DB_PATH)
    try:
        destination = sqlite3.connect(temp_path)
        try:
            with destination:
                source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()
    return temp_path


def validate_backup_db(file_path):
    """Return an error message, or None if the file looks like one of our databases."""
    try:
        connection = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
    except sqlite3.OperationalError:
        return 'That file could not be opened as a database.'
    try:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            return 'That database did not pass an integrity check.'
        tables = {row[0] for row in
                  connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        missing = REQUIRED_TABLES - tables
        if missing:
            return 'That does not look like a Bucketlistr database (missing: ' + \
                   ', '.join(sorted(missing)) + ').'
    except sqlite3.DatabaseError:
        return 'That file could not be read as a database.'
    finally:
        connection.close()
    return None


def replace_live_database(uploaded_path):
    """Swap in an uploaded database file, after backing up the current one.

    Returns the file name of the safety copy of the database being replaced."""
    backup_name = f'database.db.before-import-{timestamp_for_filename()}'
    backup_path = path.join(DATA_DIR, backup_name)
    shutil.copy2(DB_PATH, backup_path)

    db.session.remove()
    db.engine.dispose()
    os.replace(uploaded_path, DB_PATH)
    return backup_name


def export_json():
    categories = Category.query.order_by(Category.position).all()
    items = BucketItem.query.all()
    return {
        'format': BACKUP_FORMAT,
        'version': BACKUP_VERSION,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'site_name': get_site_name(),
        'categories': [
            {'name': category.name, 'position': category.position}
            for category in categories
        ],
        'items': [
            {
                'title': item.title,
                'description': item.description,
                'completed': item.completed,
                'in_progress': item.in_progress,
                'completed_year': item.completed_year,
                'completed_month': item.completed_month,
                'country_code': item.country_code,
                'template_id': item.template_id,
                'category': item.category.name if item.category else None,
                'checklist': [
                    {'text': entry.text, 'done': entry.done} for entry in item.checklist
                ],
                'photos': [
                    {'filename': photo.filename, 'position': photo.position}
                    for photo in item.photos
                ],
            }
            for item in items
        ],
    }


def validate_backup_json(data):
    if not isinstance(data, dict) or data.get('format') != BACKUP_FORMAT:
        return 'That file is not a Bucketlistr JSON backup.'
    if not isinstance(data.get('version'), int) or data['version'] > BACKUP_VERSION:
        return 'That backup was made by a newer version of Bucketlistr.'
    if not isinstance(data.get('categories'), list) or not isinstance(data.get('items'), list):
        return 'That backup file is missing its categories or items.'
    return None


def restore_from_json(data):
    """Replace all categories and items with the ones in data. Never touches the
    user account; only applies the stored site name as an extra setting."""
    for item in BucketItem.query.all():
        db.session.delete(item)
    for category in Category.query.all():
        db.session.delete(category)
    db.session.flush()

    by_name = {}
    for entry in data['categories']:
        name = str(entry.get('name', '')).strip()
        if not name or name in by_name:
            continue
        position = entry.get('position')
        category = Category(name=name,
                            position=position if isinstance(position, int) else None)
        db.session.add(category)
        by_name[name] = category

    for entry in data['items']:
        title = str(entry.get('title', '')).strip()
        if not title:
            continue
        category_name = entry.get('category')
        category = by_name.get(category_name) if category_name else None
        item = BucketItem(
            title=title[:200],
            description=entry.get('description') or None,
            completed=bool(entry.get('completed')),
            in_progress=bool(entry.get('in_progress')),
            completed_year=entry.get('completed_year'),
            completed_month=entry.get('completed_month'),
            country_code=entry.get('country_code'),
            template_id=entry.get('template_id'),
            category=category,
        )
        for checklist_entry in entry.get('checklist') or []:
            text = str(checklist_entry.get('text', '')).strip()
            if text:
                item.checklist.append(
                    ChecklistEntry(text=text[:200], done=bool(checklist_entry.get('done'))))
        for photo_entry in entry.get('photos') or []:
            filename = photo_entry.get('filename')
            if filename:
                item.photos.append(Photo(filename=str(filename)[:100],
                                         position=photo_entry.get('position')))
        db.session.add(item)

    site_name = str(data.get('site_name') or '').strip()
    if site_name:
        setting = Setting.query.get('site_name')
        if setting is None:
            db.session.add(Setting(key='site_name', value=site_name[:200]))
        else:
            setting.value = site_name[:200]

    db.session.commit()
    return len(by_name), len([i for i in data['items'] if str(i.get('title', '')).strip()])

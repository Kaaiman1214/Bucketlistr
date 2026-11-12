import json
import os
import re
from os import path

from .countries import COUNTRIES

CATALOG_DIR = path.join(path.dirname(path.abspath(__file__)), 'catalog')
AUTHOR_MARKER = path.join(path.dirname(path.dirname(path.abspath(__file__))), '.template-author')
ID_PATTERN = re.compile(r'[a-z0-9][a-z0-9-]{0,62}')
MAX_FILE_BYTES = 100000
MAX_CHECKLIST_ENTRIES = 200

_warned = set()


def clean_template(data):
    if not isinstance(data, dict):
        return None, 'A template must be a JSON object.'

    def text(key, limit, required=False):
        value = data.get(key)
        if value is None:
            value = ''
        if not isinstance(value, str):
            raise ValueError(f'"{key}" must be text.')
        value = value.strip()
        if required and not value:
            raise ValueError(f'"{key}" is required.')
        if len(value) > limit:
            raise ValueError(f'"{key}" can be at most {limit} characters.')
        return value

    try:
        template_id = text('id', 63, required=True)
        if not ID_PATTERN.fullmatch(template_id):
            raise ValueError('"id" may only contain lowercase letters, digits and hyphens.')
        title = text('title', 200, required=True)
        category = text('category', 100, required=True)
        description = text('description', 5000)
        country = text('country', 32)
        if country and country not in COUNTRIES:
            raise ValueError(f'Unknown country code "{country}".')

        checklist = data.get('checklist') or []
        if not isinstance(checklist, list):
            raise ValueError('"checklist" must be a list of text entries.')
        entries = []
        for entry in checklist:
            if not isinstance(entry, str):
                raise ValueError('Every checklist entry must be text.')
            entry = entry.strip()
            if len(entry) > 200:
                raise ValueError('Checklist entries can be at most 200 characters.')
            if entry:
                entries.append(entry)
        if len(entries) > MAX_CHECKLIST_ENTRIES:
            raise ValueError(f'A checklist can have at most {MAX_CHECKLIST_ENTRIES} entries.')
    except ValueError as error:
        return None, str(error)

    return {'id': template_id, 'title': title, 'category': category,
            'description': description, 'country': country, 'checklist': entries}, None


def _warn_once(name, message):
    if name not in _warned:
        _warned.add(name)
        print(f'WARNING: skipped catalog/{name}: {message}')


def load_catalog():
    templates = []
    if not path.isdir(CATALOG_DIR):
        return templates
    for name in sorted(os.listdir(CATALOG_DIR)):
        if not name.endswith('.json'):
            continue
        file_path = path.join(CATALOG_DIR, name)
        template = None
        try:
            if path.getsize(file_path) > MAX_FILE_BYTES:
                raise ValueError('The file is too large.')
            with open(file_path, encoding='utf-8') as template_file:
                template, error = clean_template(json.load(template_file))
            if error is None and template['id'] + '.json' != name:
                error = 'The id must match the file name.'
        except (OSError, ValueError) as exc:
            error = str(exc)
        if error:
            _warn_once(name, error)
            continue
        templates.append(template)
    return templates


def author_mode():
    return path.isfile(AUTHOR_MARKER)


def template_path(template_id):
    if not ID_PATTERN.fullmatch(template_id or ''):
        raise ValueError('Invalid template id.')
    return path.join(CATALOG_DIR, template_id + '.json')


def get_template(template_id):
    for template in load_catalog():
        if template['id'] == template_id:
            return template
    return None


def write_template(template):
    data = {'id': template['id'], 'title': template['title'], 'category': template['category']}
    if template['description']:
        data['description'] = template['description']
    if template['country']:
        data['country'] = template['country']
    if template['checklist']:
        data['checklist'] = template['checklist']

    target = template_path(template['id'])
    os.makedirs(CATALOG_DIR, exist_ok=True)
    temp = target + '.tmp'
    with open(temp, 'w', encoding='utf-8', newline='\n') as template_file:
        json.dump(data, template_file, indent=2, ensure_ascii=False)
        template_file.write('\n')
    os.replace(temp, target)


def delete_template(template_id):
    try:
        os.remove(template_path(template_id))
    except FileNotFoundError:
        pass

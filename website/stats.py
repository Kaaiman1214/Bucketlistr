import re
from collections import Counter

from .countries import CONTINENT_NAMES, COUNTRIES, continent_of, flag_url
from .utils import fold


def is_country(code):
    return re.fullmatch(r'[a-z]{2}', code) is not None and code != 'cq'


def percent(part, whole):
    return int(100 * part / whole + 0.5) if whole else 0


def summarize(items):
    completed = sum(1 for item in items if item.completed)
    in_progress = sum(1 for item in items if item.status == 'in_progress')
    return {
        'total': len(items),
        'completed': completed,
        'in_progress': in_progress,
        'planned': len(items) - completed - in_progress,
        'percent': percent(completed, len(items)),
    }


def build_stats(items, categories):
    completed = [item for item in items if item.completed]

    years = Counter(item.completed_year for item in completed)
    per_year = [{'label': str(year), 'count': years[year]}
                for year in sorted((year for year in years if year is not None), reverse=True)]
    if None in years:
        per_year.append({'label': 'No year', 'count': years[None]})
    most = max((row['count'] for row in per_year), default=0)
    for row in per_year:
        row['percent'] = percent(row['count'], most)

    grouped = {}
    for item in items:
        grouped.setdefault(item.category_id, []).append(item)
    per_category = []
    names = [(category.id, category.name) for category in categories]
    if None in grouped:
        names.append((None, 'Uncategorized'))
    for category_id, name in names:
        members = grouped.get(category_id, [])
        if not members:
            continue
        done = sum(1 for item in members if item.completed)
        per_category.append({'name': name, 'done': done, 'total': len(members),
                             'percent': percent(done, len(members))})

    visited = {item.country_code for item in completed if item.country_code in COUNTRIES}
    listed = {item.country_code for item in items if item.country_code in COUNTRIES}
    places = [{'name': COUNTRIES[code], 'flag': flag_url(code)}
              for code in sorted(visited, key=lambda code: fold(COUNTRIES[code]))]

    return {
        **summarize(items),
        'per_year': per_year,
        'per_category': per_category,
        'places': places,
        'countries_visited': sum(1 for code in visited if is_country(code)),
        'countries_listed': sum(1 for code in listed if is_country(code)),
        'other_visited': sum(1 for code in visited if not is_country(code)),
        'continents_visited': len({continent_of(code) for code in visited}),
        'continents_total': len(CONTINENT_NAMES),
    }

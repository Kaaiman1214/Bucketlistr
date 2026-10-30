from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user

from . import db
from .models import BucketItem, Category, User, MONTH_NAMES
from .utils import fold

views = Blueprint('views', __name__)

NEW_CATEGORY = '__new__'


def get_owned_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    return item


def item_back_url(item):
    """Where Back, Cancel and Save go from the edit page: the item page, or the
    list when the item has nothing to show on its own page."""
    if item.has_details:
        return url_for('views.item', item_id=item.id)
    return url_for('views.home')


def item_sort_key(item):
    """Alphabetical by title."""
    return fold(item.title)


def find_category(name):
    """Return the category with this name (ignoring case), or None."""
    for category in Category.query.all():
        if fold(category.name) == fold(name):
            return category
    return None


def build_sections(items):
    """Group items by category. Categories are sorted by name and the items
    inside a category by item_sort_key. Items without a category come last."""
    grouped = {}
    for item in items:
        grouped.setdefault(item.category_id, []).append(item)

    sections = []
    for category in sorted(Category.query.all(), key=lambda c: fold(c.name)):
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
    """Remove categories that no longer contain any item."""
    for category in Category.query.filter(~Category.items.any()).all():
        db.session.delete(category)


def blank_values():
    """Form values for the New item page."""
    return {
        'title': '',
        'description': '',
        'category': '',
        'new_category': '',
        'completed': False,
        'year': '',
        'month': '',
    }


def item_values(item):
    """Form values for the Edit item page."""
    return {
        'title': item.title,
        'description': item.description or '',
        'category': str(item.category_id or ''),
        'new_category': '',
        'completed': item.completed,
        'year': item.completed_year or '',
        'month': item.completed_month or '',
    }


def read_item_form(form):
    """Read the submitted form into the same shape as blank_values()."""
    values = {
        'title': form.get('title', '').strip(),
        'description': form.get('description', '').strip(),
        'category': form.get('category', '').strip(),
        'new_category': form.get('new_category', '').strip(),
        'completed': form.get('completed') == 'on',
        'year': form.get('completed_year', '').strip(),
        'month': form.get('completed_month', '').strip(),
    }
    return values


def validate_item(values):
    """Check the submitted values. Returns (error message or None, cleaned values)."""
    cleaned = {'year': None, 'month': None}
    cleaned.update(category=None, new_category=None)

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

    return None, cleaned


def apply_item(item, values, cleaned):
    """Copy validated form values onto an item. The caller commits."""
    item.title = values['title']
    item.description = values['description'] or None
    category = cleaned['category']
    if category is None:
        category = Category(name=cleaned['new_category'])
        db.session.add(category)
    item.category = category
    item.completed = values['completed']
    item.completed_year = cleaned['year'] if values['completed'] else None
    item.completed_month = cleaned['month'] if values['completed'] else None


def form_context():
    """Extra template variables needed by the item form."""
    return {
        'months': MONTH_NAMES,
        'categories': sorted(Category.query.all(), key=lambda c: fold(c.name)),
    }


@views.route('/')
def home():
    if User.query.first() is None:
        return redirect(url_for('auth.sign_up'))

    items = BucketItem.query.all()
    return render_template("home.html", user=current_user,
                           sections=build_sections(items))


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


@views.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = get_owned_item(item_id)
    values = item_values(item)

    if request.method == 'POST':
        values = read_item_form(request.form)
        error, cleaned = validate_item(values)
        if error:
            flash(error, category='error')
        else:
            apply_item(item, values, cleaned)
            prune_empty_categories()
            db.session.commit()
            flash('Changes saved!', category='success')
            return redirect(item_back_url(item))

    return render_template("edit_item.html", user=current_user, item=item, values=values,
                           back_url=item_back_url(item), **form_context())


@views.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_owned_item(item_id)
    db.session.delete(item)
    prune_empty_categories()
    db.session.commit()
    flash('Item deleted.', category='success')
    return redirect(url_for('views.home'))

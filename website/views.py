from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user

from . import db
from .models import BucketItem, User, MONTH_NAMES

views = Blueprint('views', __name__)


def completed_sort_key(item):
    """Newest completion first. Items with a year but no month come after the
    dated months of that year; items with no date at all come last."""
    if item.completed_year is None:
        return (0, 0, 0)
    return (1, item.completed_year, item.completed_month or 0)


def get_owned_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    return item


def blank_values():
    """Form values for the New item page."""
    return {
        'title': '',
        'description': '',
        'completed': False,
        'year': '',
        'month': '',
    }


def item_values(item):
    """Form values for the Edit item page."""
    return {
        'title': item.title,
        'description': item.description or '',
        'completed': item.completed,
        'year': item.completed_year or '',
        'month': item.completed_month or '',
    }


def read_item_form(form):
    """Read the submitted form into the same shape as blank_values()."""
    values = {
        'title': form.get('title', '').strip(),
        'description': form.get('description', '').strip(),
        'completed': form.get('completed') == 'on',
        'year': form.get('completed_year', '').strip(),
        'month': form.get('completed_month', '').strip(),
    }
    return values


def validate_item(values):
    """Check the submitted values. Returns (error message or None, cleaned values)."""
    cleaned = {'year': None, 'month': None}

    if not values['title']:
        return 'Give the item a title.', cleaned
    if len(values['title']) > 200:
        return 'Title can be at most 200 characters.', cleaned

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
    item.completed = values['completed']
    item.completed_year = cleaned['year'] if values['completed'] else None
    item.completed_month = cleaned['month'] if values['completed'] else None


def form_context():
    """Extra template variables needed by the item form."""
    return {'months': MONTH_NAMES}


@views.route('/')
def home():
    if User.query.first() is None:
        return redirect(url_for('auth.sign_up'))

    items = BucketItem.query.order_by(BucketItem.id).all()
    todo_items = [i for i in items if not i.completed]
    done_items = sorted((i for i in items if i.completed),
                        key=completed_sort_key, reverse=True)
    return render_template("home.html", user=current_user,
                           todo_items=todo_items, done_items=done_items)


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
            db.session.commit()
            flash('Changes saved!', category='success')
            return redirect(url_for('views.item', item_id=item.id))

    return render_template("edit_item.html", user=current_user, item=item, values=values,
                           back_url=url_for('views.item', item_id=item.id), **form_context())


@views.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_owned_item(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', category='success')
    return redirect(url_for('views.home'))

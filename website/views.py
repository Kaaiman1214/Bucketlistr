from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user

from . import db
from .models import BucketItem, MONTH_NAMES

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


@views.route('/')
@login_required
def home():
    items = BucketItem.query.order_by(BucketItem.id).all()
    todo_items = [i for i in items if not i.completed]
    done_items = sorted((i for i in items if i.completed),
                        key=completed_sort_key, reverse=True)
    return render_template("home.html", user=current_user,
                           todo_items=todo_items, done_items=done_items)


@views.route('/add', methods=['POST'])
@login_required
def add_item():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Give the item a title.', category='error')
    elif len(title) > 200:
        flash('Title can be at most 200 characters.', category='error')
    else:
        db.session.add(BucketItem(title=title, user_id=current_user.id))
        db.session.commit()
        flash('Item added!', category='success')
    return redirect(url_for('views.home'))


@views.route('/item/<int:item_id>')
@login_required
def item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    return render_template("item.html", user=current_user, item=item)


@views.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = get_owned_item(item_id)
    values = {
        'title': item.title,
        'description': item.description or '',
        'completed': item.completed,
        'year': item.completed_year or '',
        'month': item.completed_month or '',
    }

    if request.method == 'POST':
        values = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'completed': request.form.get('completed') == 'on',
            'year': request.form.get('completed_year', '').strip(),
            'month': request.form.get('completed_month', '').strip(),
        }

        error = None
        year = month = None
        if not values['title']:
            error = 'Give the item a title.'
        elif len(values['title']) > 200:
            error = 'Title can be at most 200 characters.'
        elif values['completed']:
            try:
                if values['year']:
                    year = int(values['year'])
                    if not 1900 <= year <= 2100:
                        raise ValueError
                if values['month']:
                    month = int(values['month'])
                    if not 1 <= month <= 12:
                        raise ValueError
            except ValueError:
                error = 'Enter a valid year (1900-2100) and month.'
            else:
                if month and not year:
                    error = 'Enter a year when you pick a month.'

        if error:
            flash(error, category='error')
        else:
            item.title = values['title']
            item.description = values['description'] or None
            item.completed = values['completed']
            # Date is only kept for completed items.
            item.completed_year = year if values['completed'] else None
            item.completed_month = month if values['completed'] else None
            db.session.commit()
            flash('Changes saved!', category='success')
            return redirect(url_for('views.item', item_id=item.id))

    return render_template("edit_item.html", user=current_user, item=item,
                           values=values, months=MONTH_NAMES)


@views.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_owned_item(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', category='success')
    return redirect(url_for('views.home'))

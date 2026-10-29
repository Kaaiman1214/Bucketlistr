from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user

from . import db
from .models import BucketItem

views = Blueprint('views', __name__)


def get_owned_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    return item


@views.route('/')
@login_required
def home():
    items = BucketItem.query.order_by(BucketItem.id).all()
    return render_template("home.html", user=current_user, items=items)


@views.route('/add', methods=['POST'])
@login_required
def add_item():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Give the item a title.', category='error')
    elif len(title) > 200:
        flash('Title cannot be more than 200 characters.', category='error')
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
    }

    if request.method == 'POST':
        values = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
        }

        error = None
        if not values['title']:
            error = 'Give the item a title.'
        elif len(values['title']) > 200:
            error = 'Title can be at most 200 characters.'

        if error:
            flash(error, category='error')
        else:
            item.title = values['title']
            item.description = values['description'] or None
            db.session.commit()
            flash('Changes saved!', category='success')
            return redirect(url_for('views.item', item_id=item.id))

    return render_template("edit_item.html", user=current_user, item=item, values=values)


@views.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_owned_item(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', category='success')
    return redirect(url_for('views.home'))

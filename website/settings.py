from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .auth import SPECIAL_CHARS
from .models import Setting, ordered_categories
from .security import password_limiter, wait_message

settings = Blueprint('settings', __name__)


@settings.route('/settings')
@login_required
def settings_page():
    return render_template("settings.html", user=current_user,
                           categories=ordered_categories())


@settings.route('/settings/site-name', methods=['POST'])
@login_required
def change_site_name():
    name = request.form.get('site_name', '').strip()

    if not name:
        flash('Give your bucketlist a name.', category='error')
    elif len(name) > 100:
        flash('The bucketlist name can be at most 100 characters.', category='error')
    else:
        setting = Setting.query.get('site_name')
        if setting is None:
            db.session.add(Setting(key='site_name', value=name))
        else:
            setting.value = name
        db.session.commit()
        flash('The name has been changed.', category='success')

    return redirect(url_for('settings.settings_page', _anchor='site-name'))


@settings.route('/settings/categories/order', methods=['POST'])
@login_required
def order_categories():
    payload = request.get_json(silent=True) or {}
    ids = payload.get('order')
    if not isinstance(ids, list) or not all(isinstance(category_id, int) for category_id in ids):
        abort(400)

    current = ordered_categories()
    remaining = {category.id: category for category in current}
    chosen = []
    for category_id in ids:
        category = remaining.pop(category_id, None)
        if category is not None:
            chosen.append(category)
    chosen.extend(category for category in current if category.id in remaining)

    for position, category in enumerate(chosen):
        category.position = position
    db.session.commit()
    return jsonify(ok=True)


@settings.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    current = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    wait = password_limiter.retry_after(current_user.id)
    if wait:
        flash(wait_message(wait), category='error')
    elif not check_password_hash(current_user.password, current):
        password_limiter.record(current_user.id)
        flash('Your current password is not correct.', category='error')
    elif new_password != confirm:
        flash('The new passwords don\'t match.', category='error')
    elif len(new_password) < 8:
        flash('Password must be at least 8 characters.', category='error')
    elif not any(char in new_password for char in SPECIAL_CHARS):
        flash('Password must contain at least one special character', category='error')
    else:
        password_limiter.reset(current_user.id)
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Your password has been changed.', category='success')

    return redirect(url_for('settings.settings_page', _anchor='password'))

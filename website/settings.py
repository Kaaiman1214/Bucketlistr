from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .auth import SPECIAL_CHARS

settings = Blueprint('settings', __name__)


@settings.route('/settings')
@login_required
def settings_page():
    return render_template("settings.html", user=current_user)


@settings.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    current = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    if not check_password_hash(current_user.password, current):
        flash('Your current password is not correct.', category='error')
    elif new_password != confirm:
        flash('The new passwords don\'t match.', category='error')
    elif len(new_password) < 8:
        flash('Password must be at least 8 characters.', category='error')
    elif not any(char in new_password for char in SPECIAL_CHARS):
        flash('Password must contain at least one special character', category='error')
    else:
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Your password has been changed.', category='success')

    return redirect(url_for('settings.settings_page', _anchor='password'))

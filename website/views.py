from flask import Blueprint, jsonify, render_template, request, flash 
from flask_login import login_required, current_user
from .models import BLItem
from .import db
import json 

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        blitem_text = request.form.get('blitem')
        if len(blitem_text) < 1:
            flash('Item is too short!', category='error')
        else:
            new_blitem = BLItem(text=blitem_text, user_id=current_user.id)
            db.session.add(new_blitem)
            db.session.commit()
            flash('Item added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-item', methods=['POST'])

@views.route('/delete-item', methods=['POST'])
@login_required
def delete_item():
    note = json.loads(request.data)
    itemId = note['itemId']
    note = BLItem.query.get(itemId)

    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

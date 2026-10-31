from flask_login import UserMixin

from . import db
from .countries import COUNTRIES, flag_url as country_flag_url

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    items = db.relationship('BucketItem', backref='category')


class BucketItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_year = db.Column(db.Integer)
    completed_month = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    country_code = db.Column(db.String(32))
    checklist = db.relationship('ChecklistEntry', cascade='all, delete-orphan',
                                order_by='ChecklistEntry.id')

    @property
    def completed_label(self):
        if not self.completed:
            return ''
        if self.completed_year is None:
            return 'Completed'
        if self.completed_month:
            month = MONTH_NAMES[self.completed_month - 1][:3]
            return f'Completed, {month} {self.completed_year}'
        return f'Completed, {self.completed_year}'

    @property
    def has_details(self):
        return bool(self.description) or bool(self.checklist)

    @property
    def country_name(self):
        return COUNTRIES.get(self.country_code) if self.country_code else None

    @property
    def flag_url(self):
        return country_flag_url(self.country_code)

    @property
    def checklist_total(self):
        return len(self.checklist)

    @property
    def checklist_done(self):
        return sum(1 for entry in self.checklist if entry.done)

    @property
    def progress_percent(self):
        if not self.checklist:
            return 0
        return int(100 * self.checklist_done / self.checklist_total + 0.5)


class ChecklistEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('bucket_item.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    Username = db.Column(db.String(150))
    items = db.relationship('BucketItem')

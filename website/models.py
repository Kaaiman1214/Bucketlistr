from flask_login import UserMixin

from . import db

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


class BucketItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_year = db.Column(db.Integer)
    completed_month = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def completed_label(self):
        """'Completed, Jan 2026', 'Completed, 2026' or just 'Completed'."""
        if not self.completed:
            return ''
        if self.completed_year is None:
            return 'Completed'
        if self.completed_month:
            month = MONTH_NAMES[self.completed_month - 1][:3]
            return f'Completed, {month} {self.completed_year}'
        return f'Completed, {self.completed_year}'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    Username = db.Column(db.String(150))
    items = db.relationship('BucketItem')

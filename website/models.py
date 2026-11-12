from flask_login import UserMixin

from . import db
from .countries import COUNTRIES, flag_url as country_flag_url
from .utils import fold

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

STATUS_CHOICES = [
    ('planned', 'Planned'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
]

DEFAULT_SITE_NAME = 'Bucketlist'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    position = db.Column(db.Integer)
    items = db.relationship('BucketItem', backref='category')


class BucketItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_year = db.Column(db.Integer)
    completed_month = db.Column(db.Integer)
    in_progress = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    country_code = db.Column(db.String(32))
    template_id = db.Column(db.String(64))
    checklist = db.relationship('ChecklistEntry', cascade='all, delete-orphan',
                                order_by='ChecklistEntry.id')
    photos = db.relationship('Photo', cascade='all, delete-orphan', order_by='Photo.id')

    @property
    def status(self):
        if self.completed:
            return 'completed'
        if self.in_progress:
            return 'in_progress'
        return 'planned'

    @property
    def completed_label(self):
        if not self.completed:
            return ''
        if self.completed_year is None:
            return 'Completed'
        return f'Completed, {self.completed_year}'

    @property
    def has_details(self):
        return bool(self.description) or bool(self.checklist) or bool(self.photos)

    @property
    def sorted_photos(self):
        return sorted(self.photos,
                      key=lambda photo: (photo.position if photo.position is not None else 0,
                                         photo.id))

    @property
    def first_photo(self):
        photos = self.sorted_photos
        return photos[0] if photos else None

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


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('bucket_item.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(150))
    Username = db.Column(db.String(150))
    items = db.relationship('BucketItem')


class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(200))


def get_site_name():
    setting = Setting.query.get('site_name')
    if setting and setting.value:
        return setting.value
    return DEFAULT_SITE_NAME


def ordered_categories():
    return sorted(Category.query.all(),
                  key=lambda category: (category.position is None, category.position or 0,
                                        fold(category.name)))


def next_category_position():
    positions = [category.position for category in Category.query.all()
                 if category.position is not None]
    return max(positions) + 1 if positions else None


def get_sidebar_categories():
    links = [{'key': str(category.id), 'name': category.name}
             for category in ordered_categories() if category.items]
    if BucketItem.query.filter_by(category_id=None).first() is not None:
        links.append({'key': 'none', 'name': 'Uncategorized'})
    return links

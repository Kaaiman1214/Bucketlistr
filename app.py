from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-bucketlist-key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bucketlist.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

RAW_COUNTRIES = {
    'ad': 'Andorra', 'ae': 'United Arab Emirates', 'af': 'Afghanistan', 'ag': 'Antigua and Barbuda', 
    'ai': 'Anguilla', 'al': 'Albania', 'am': 'Armenia', 'ao': 'Angola', 'aq': 'Antarctica', 
    'ar': 'Argentina', 'as': 'American Samoa', 'at': 'Austria', 'au': 'Australia', 'aw': 'Aruba', 
    'ax': 'Åland Islands', 'az': 'Azerbaijan', 'ba': 'Bosnia and Herzegovina', 'bb': 'Barbados', 
    'bd': 'Bangladesh', 'be': 'Belgium', 'bf': 'Burkina Faso', 'bg': 'Bulgaria', 'bh': 'Bahrain', 
    'bi': 'Burundi', 'bj': 'Benin', 'bl': 'Saint Barthélemy', 'bm': 'Bermuda', 'bn': 'Brunei', 
    'bo': 'Bolivia', 'bq': 'Caribbean Netherlands', 'br': 'Brazil', 'bs': 'Bahamas', 'bt': 'Bhutan', 
    'bv': 'Bouvet Island', 'bw': 'Botswana', 'by': 'Belarus', 'bz': 'Belize', 'ca': 'Canada', 
    'cc': 'Cocos Islands', 'cd': 'DR Congo', 'cf': 'Central African Republic', 'cg': 'Republic of the Congo', 
    'ch': 'Switzerland', 'ci': 'Côte d\'Ivoire', 'ck': 'Cook Islands', 'cl': 'Chile', 'cm': 'Cameroon', 
    'cn': 'China', 'co': 'Colombia', 'cr': 'Costa Rica', 'cu': 'Cuba', 'cv': 'Cape Verde', 
    'cw': 'Curaçao', 'cx': 'Christmas Island', 'cy': 'Cyprus', 'cz': 'Czechia', 'de': 'Germany', 
    'dj': 'Djibouti', 'dk': 'Denmark', 'dm': 'Dominica', 'do': 'Dominican Republic', 'dz': 'Algeria', 
    'ec': 'Ecuador', 'ee': 'Estonia', 'eg': 'Egypt', 'eh': 'Western Sahara', 'er': 'Eritrea', 
    'es': 'Spain', 'et': 'Ethiopia', 'eu': 'European Union', 'fi': 'Finland', 'fj': 'Fiji', 'fk': 'Falkland Islands', 
    'fm': 'Micronesia', 'fo': 'Faroe Islands', 'fr': 'France', 'ga': 'Gabon', 'gb': 'United Kingdom', 
    'gb-eng': 'England', 'gb-nir': 'Northern Ireland', 'gb-sct': 'Scotland', 'gb-wls': 'Wales', 
    'gb-con': 'Cornwall', 'gd': 'Grenada', 'ge': 'Georgia', 'gf': 'French Guiana', 'gg': 'Guernsey', 
    'gh': 'Ghana', 'gi': 'Gibraltar', 'gl': 'Greenland', 'gm': 'Gambia', 'gn': 'Guinea', 
    'gp': 'Guadeloupe', 'gq': 'Equatorial Guinea', 'gr': 'Greece', 'gs': 'South Georgia', 
    'gt': 'Guatemala', 'gu': 'Guam', 'gw': 'Guinea-Bissau', 'gy': 'Guyana', 'hk': 'Hong Kong', 
    'hm': 'Heard Island', 'hn': 'Honduras', 'hr': 'Croatia', 'ht': 'Haiti', 'hu': 'Hungary', 
    'id': 'Indonesia', 'ie': 'Ireland', 'il': 'Israel', 'im': 'Isle of Man', 'in': 'India', 
    'io': 'British Indian Ocean Territory', 'iq': 'Iraq', 'ir': 'Iran', 'is': 'Iceland', 'it': 'Italy', 
    'je': 'Jersey', 'jm': 'Jamaica', 'jo': 'Jordan', 'jp': 'Japan', 'ke': 'Kenya', 'kg': 'Kyrgyzstan', 
    'kh': 'Cambodia', 'ki': 'Kiribati', 'km': 'Comoros', 'kn': 'Saint Kitts and Nevis', 'kp': 'North Korea', 
    'kr': 'South Korea', 'kw': 'Kuwait', 'ky': 'Cayman Islands', 'kz': 'Kazakhstan', 'la': 'Laos', 
    'lb': 'Lebanon', 'lc': 'Saint Lucia', 'li': 'Liechtenstein', 'lk': 'Sri Lanka', 'lr': 'Liberia', 
    'ls': 'Lesotho', 'lt': 'Lithuania', 'lu': 'Luxembourg', 'lv': 'Latvia', 'ly': 'Libya', 
    'ma': 'Morocco', 'mc': 'Monaco', 'md': 'Moldova', 'me': 'Montenegro', 'mf': 'Saint Martin', 
    'mg': 'Madagascar', 'mh': 'Marshall Islands', 'mk': 'North Macedonia', 'ml': 'Mali', 'mm': 'Myanmar', 
    'mn': 'Mongolia', 'mo': 'Macau', 'mp': 'Northern Mariana Islands', 'mq': 'Martinique', 
    'mr': 'Mauritania', 'ms': 'Montserrat', 'mt': 'Malta', 'mu': 'Mauritius', 'mv': 'Maldives', 
    'mw': 'Malawi', 'mx': 'Mexico', 'my': 'Malaysia', 'mz': 'Mozambique', 'na': 'Namibia', 
    'nc': 'New Caledonia', 'ne': 'Niger', 'nf': 'Norfolk Island', 'ng': 'Nigeria', 'ni': 'Nicaragua', 
    'nl': 'Netherlands', 'no': 'Norway', 'np': 'Nepal', 'nr': 'Nauru', 'nu': 'Niue', 'nz': 'New Zealand', 
    'om': 'Oman', 'pa': 'Panama', 'pe': 'Peru', 'pf': 'French Polynesia', 'pg': 'Papua New Guinea', 
    'ph': 'Philippines', 'pk': 'Pakistan', 'pl': 'Poland', 'pm': 'Saint Pierre and Miquelon', 
    'pn': 'Pitcairn Islands', 'pr': 'Puerto Rico', 'ps': 'Palestine', 'pt': 'Portugal', 'pw': 'Palau', 
    'py': 'Paraguay', 'qa': 'Qatar', 're': 'Réunion', 'ro': 'Romania', 'rs': 'Serbia', 'ru': 'Russia', 
    'rw': 'Rwanda', 'sa': 'Saudi Arabia', 'sb': 'Solomon Islands', 'sc': 'Seychelles', 'sd': 'Sudan', 
    'se': 'Sweden', 'sg': 'Singapore', 'sh': 'Saint Helena', 'si': 'Slovenia', 'sj': 'Svalbard', 
    'sk': 'Slovakia', 'sl': 'Sierra Leone', 'sm': 'San Marino', 'sn': 'Senegal', 'so': 'Somalia', 
    'sr': 'Suriname', 'ss': 'South Sudan', 'st': 'São Tomé and Príncipe', 'sv': 'El Salvador', 
    'sx': 'Sint Maarten', 'sy': 'Syria', 'sz': 'Eswatini', 'tc': 'Turks and Caicos Islands', 
    'td': 'Chad', 'tf': 'French Southern Territories', 'tg': 'Togo', 'th': 'Thailand', 'tj': 'Tajikistan', 
    'tk': 'Tokelau', 'tl': 'Timor-Leste', 'tm': 'Turkmenistan', 'tn': 'Tunisia', 'to': 'Tonga', 
    'tr': 'Turkey', 'tt': 'Trinidad and Tobago', 'tv': 'Tuvalu', 'tw': 'Taiwan', 'tz': 'Tanzania', 
    'ua': 'Ukraine', 'ug': 'Uganda', 'um': 'U.S. Minor Outlying Islands', 'us': 'United States', 
    'uy': 'Uruguay', 'uz': 'Uzbekistan', 'va': 'Vatican City', 'vc': 'St. Vincent & Grenadines', 
    've': 'Venezuela', 'vg': 'British Virgin Islands', 'vi': 'U.S. Virgin Islands', 'vn': 'Vietnam', 
    'vu': 'Vanuatu', 'wf': 'Wallis and Futuna', 'ws': 'Samoa', 'xk': 'Kosovo', 'ye': 'Yemen', 
    'yt': 'Mayotte', 'za': 'South Africa', 'zm': 'Zambia', 'zw': 'Zimbabwe'
}

COUNTRIES = {}
for code, name in RAW_COUNTRIES.items():
    if code == 'gb-con':
        url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Flag_of_Cornwall.svg/40px-Flag_of_Cornwall.svg.png'
    else:
        url = f'https://flagcdn.com/w40/{code}.png'
    COUNTRIES[code] = {'name': name, 'url': url}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(150), default="My Bucket List")
    site_quote = db.Column(db.String(300), nullable=True)
    favicon = db.Column(db.String(255), nullable=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Planned')
    image = db.Column(db.Text, nullable=True) 
    completion_date = db.Column(db.String(50), nullable=True) 
    completion_month = db.Column(db.String(2), nullable=True)
    description = db.Column(db.Text, nullable=True) 
    has_blog = db.Column(db.Boolean, default=False)
    has_text = db.Column(db.Boolean, default=False)
    has_checklist = db.Column(db.Boolean, default=False)
    has_music = db.Column(db.Boolean, default=False)
    music_title = db.Column(db.String(255), nullable=True)
    music_artist = db.Column(db.String(255), nullable=True)
    music_cover = db.Column(db.Text, nullable=True)
    music_preview = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_location = db.Column(db.Boolean, default=False)
    country = db.Column(db.String(10), nullable=True)

class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    item = db.relationship('Item', backref=db.backref('checklist_items', cascade='all, delete-orphan'))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.before_request
def check_setup():
    if request.endpoint in ['setup', 'static']:
        return
    try:
        if User.query.count() == 0:
            return redirect(url_for('setup'))
    except Exception:
        pass

with app.app_context():
    db.create_all()

def process_multiple_images(files):
    filenames = []
    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
    return ",".join(filenames) if filenames else None

def ensure_category_exists(cat_name):
    cat_obj = Category.query.filter_by(name=cat_name).first()
    if not cat_obj:
        max_order = db.session.query(db.func.max(Category.sort_order)).scalar()
        next_order = (max_order + 1) if max_order is not None else 0
        new_cat = Category(name=cat_name, sort_order=next_order)
        db.session.add(new_cat)
        db.session.commit()

def calculate_progress(item):
    if not item.has_checklist or not item.checklist_items:
        return None
    total = len(item.checklist_items)
    if total == 0:
        return 0
    completed = sum(1 for c in item.checklist_items if c.is_completed)
    return int((completed / total) * 100)

@app.route('/')
def home():
    settings = SiteSettings.query.first()
    categories = Category.query.order_by(Category.sort_order.asc(), Category.name.asc()).all()
    
    search_query = request.args.get('q', '').strip().lower()
    sort_by = request.args.get('sort', 'default')
    country_filter = request.args.get('country', 'all')
    
    query = Item.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Item.title.ilike(f'%{search_query}%'),
                Item.category.ilike(f'%{search_query}%'),
                Item.completion_date.ilike(f'%{search_query}%'),
                Item.description.ilike(f'%{search_query}%')
            )
        )
        
    if country_filter != 'all':
        query = query.filter(Item.is_location == True, Item.country == country_filter)
    
    all_items = query.order_by(Item.sort_order.asc()).all()
    
    active_country_codes = [r[0] for r in db.session.query(Item.country).filter(Item.is_location==True).distinct().all() if r[0]]
    active_countries = {code: COUNTRIES[code] for code in active_country_codes if code in COUNTRIES}
    
    sorted_groups = []
    for cat in categories:
        cat_items = [i for i in all_items if i.category == cat.name]
        if cat_items:
            if sort_by == 'status':
                status_priority = {'Completed': 0, 'In Progress': 1, 'Planned': 2}
                cat_items.sort(key=lambda x: (status_priority.get(x.status, 3), x.sort_order))
            elif sort_by == 'alpha_asc':
                cat_items.sort(key=lambda x: x.title.lower())
            elif sort_by == 'alpha_desc':
                cat_items.sort(key=lambda x: x.title.lower(), reverse=True)
            elif sort_by == 'progress_desc':
                cat_items.sort(key=lambda x: calculate_progress(x) if calculate_progress(x) is not None else -1, reverse=True)
            elif sort_by == 'progress_asc':
                cat_items.sort(key=lambda x: calculate_progress(x) if calculate_progress(x) is not None else 101)
            else:
                cat_items.sort(key=lambda x: x.sort_order)
                
            sorted_groups.append((cat.name, cat_items))
            
    handled_cats = [c.name for c in categories]
    other_items = [i for i in all_items if i.category not in handled_cats]
    if other_items:
        other_cats = set(i.category for i in other_items)
        for oc in other_cats:
            oc_items = [i for i in other_items if i.category == oc]
            if sort_by == 'status':
                status_priority = {'Completed': 0, 'In Progress': 1, 'Planned': 2}
                oc_items.sort(key=lambda x: (status_priority.get(x.status, 3), x.sort_order))
            elif sort_by == 'alpha_asc':
                oc_items.sort(key=lambda x: x.title.lower())
            elif sort_by == 'alpha_desc':
                oc_items.sort(key=lambda x: x.title.lower(), reverse=True)
            elif sort_by == 'progress_desc':
                oc_items.sort(key=lambda x: calculate_progress(x) if calculate_progress(x) is not None else -1, reverse=True)
            elif sort_by == 'progress_asc':
                oc_items.sort(key=lambda x: calculate_progress(x) if calculate_progress(x) is not None else 101)
            sorted_groups.append((oc, oc_items))

    return render_template('index.html', sorted_groups=sorted_groups, categories=categories, 
                           settings=settings, search_query=search_query, current_sort=sort_by, 
                           current_country=country_filter, active_countries=active_countries, 
                           COUNTRIES=COUNTRIES, calculate_progress=calculate_progress)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    settings = SiteSettings.query.first()
    item = db.session.get(Item, item_id)
    if not item or not item.has_blog:
        return redirect(url_for('home'))
        
    images = item.image.split(',') if item.image else []
    progress = calculate_progress(item)
    return render_template('item_detail.html', item=item, images=images, settings=settings, progress=progress, COUNTRIES=COUNTRIES)

@app.route('/item/<int:item_id>/toggle_check/<int:check_id>', methods=['POST'])
@login_required
def toggle_checklist(item_id, check_id):
    check_item = db.session.get(ChecklistItem, check_id)
    if check_item and check_item.item_id == item_id:
        check_item.is_completed = not check_item.is_completed
        db.session.commit()
    return redirect(url_for('item_detail', item_id=item_id))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if User.query.count() > 0:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)
        new_admin = User(username=username, password=hashed_pw)
        db.session.add(new_admin)
        
        site_name = request.form.get('site_name', 'My Bucket List')
        site_quote = request.form.get('site_quote', '')
        
        favicon_file = request.files.get('favicon')
        favicon_filename = None
        if favicon_file and favicon_file.filename != '':
            favicon_filename = secure_filename(favicon_file.filename)
            favicon_file.save(os.path.join(app.config['UPLOAD_FOLDER'], favicon_filename))
            
        new_settings = SiteSettings(site_name=site_name, site_quote=site_quote, favicon=favicon_filename)
        db.session.add(new_settings)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute") 
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login failed. Check username and password.')
    return render_template('login.html')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    settings = SiteSettings.query.first()
    categories = Category.query.order_by(Category.sort_order.asc(), Category.name.asc()).all()
    all_items = Item.query.order_by(Item.sort_order.asc()).all()
    
    admin_groups = []
    for cat in categories:
        cat_items = [i for i in all_items if i.category == cat.name]
        admin_groups.append((cat.name, cat_items))
        
    handled_cats = [c.name for c in categories]
    other_items = [i for i in all_items if i.category not in handled_cats]
    if other_items:
        other_cats = set(i.category for i in other_items)
        for oc in other_cats:
            admin_groups.append((oc, [i for i in other_items if i.category == oc]))

    return render_template('admin_dashboard.html', admin_groups=admin_groups, categories=categories, settings=settings, COUNTRIES=COUNTRIES)

@app.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        
    settings.site_name = request.form.get('site_name', 'My Bucket List')
    settings.site_quote = request.form.get('site_quote', '')
    
    favicon_file = request.files.get('favicon')
    if favicon_file and favicon_file.filename != '':
        favicon_filename = secure_filename(favicon_file.filename)
        favicon_file.save(os.path.join(app.config['UPLOAD_FOLDER'], favicon_filename))
        settings.favicon = favicon_filename
        
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/export')
@login_required
def export_data():
    categories = Category.query.all()
    items = Item.query.all()
    
    data = {
        'categories': [{'name': c.name, 'sort_order': c.sort_order} for c in categories],
        'items': []
    }
    
    for item in items:
        item_data = {
            'title': item.title,
            'category': item.category,
            'status': item.status,
            'image': item.image,
            'completion_date': item.completion_date,
            'completion_month': item.completion_month,
            'description': item.description,
            'has_blog': item.has_blog,
            'has_text': item.has_text,
            'has_checklist': item.has_checklist,
            'has_music': item.has_music,
            'music_title': item.music_title,
            'music_artist': item.music_artist,
            'music_cover': item.music_cover,
            'music_preview': item.music_preview,
            'sort_order': item.sort_order,
            'is_location': item.is_location,
            'country': item.country,
            'checklist_items': [{'text': check.text, 'is_completed': check.is_completed} for check in item.checklist_items]
        }
        data['items'].append(item_data)
        
    json_data = json.dumps(data, indent=4)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=bucketlist_backup_{date_str}.json"}
    )

@app.route('/admin/import', methods=['POST'])
@login_required
def import_data():
    file = request.files.get('backup_file')
    if file and file.filename.endswith('.json'):
        try:
            data = json.load(file)
            
            for cat_data in data.get('categories', []):
                if not Category.query.filter_by(name=cat_data['name']).first():
                    new_cat = Category(name=cat_data['name'], sort_order=cat_data.get('sort_order', 0))
                    db.session.add(new_cat)
                    
            for item_data in data.get('items', []):
                new_item = Item(
                    title=item_data.get('title'),
                    category=item_data.get('category'),
                    status=item_data.get('status', 'Planned'),
                    image=item_data.get('image'),
                    completion_date=item_data.get('completion_date'),
                    completion_month=item_data.get('completion_month'),
                    description=item_data.get('description'),
                    has_blog=item_data.get('has_blog', False),
                    has_text=item_data.get('has_text', False),
                    has_checklist=item_data.get('has_checklist', False),
                    has_music=item_data.get('has_music', False),
                    music_title=item_data.get('music_title'),
                    music_artist=item_data.get('music_artist'),
                    music_cover=item_data.get('music_cover'),
                    music_preview=item_data.get('music_preview'),
                    sort_order=item_data.get('sort_order', 0),
                    is_location=item_data.get('is_location', False),
                    country=item_data.get('country')
                )
                db.session.add(new_item)
                db.session.flush() 
                
                for check_data in item_data.get('checklist_items', []):
                    new_check = ChecklistItem(
                        item_id=new_item.id,
                        text=check_data.get('text'),
                        is_completed=check_data.get('is_completed', False)
                    )
                    db.session.add(new_check)
                    
            db.session.commit()
        except Exception:
            pass
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/categories/reorder', methods=['POST'])
@login_required
def reorder_categories():
    for key, value in request.form.items():
        if key.startswith('order_'):
            cat_id = key.split('_')[1]
            cat = db.session.get(Category, int(cat_id))
            if cat:
                try:
                    cat.sort_order = int(value)
                except ValueError:
                    pass
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/categories/delete/<int:cat_id>', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if cat:
        Item.query.filter_by(category=cat.name).delete()
        db.session.delete(cat)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/items/reorder', methods=['POST'])
@login_required
def reorder_items():
    for key, value in request.form.items():
        if key.startswith('item_order_'):
            item_id = key.split('_')[2]
            item = db.session.get(Item, int(item_id))
            if item:
                try:
                    item.sort_order = int(value)
                except ValueError:
                    pass
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/new', methods=['GET', 'POST'])
@login_required 
def new_item():
    if request.method == 'POST':
        title = request.form.get('title')
        existing_category = request.form.get('existing_category')
        new_category = request.form.get('new_category')
        category = new_category.strip() if (new_category and new_category.strip() != "") else existing_category
        status = request.form.get('status')
        completion_date = request.form.get('completion_date')
        completion_month = request.form.get('completion_month')
        
        is_location = request.form.get('is_location') == 'on'
        country = request.form.get('country').lower() if request.form.get('country') else None
        
        has_blog = request.form.get('has_blog') == 'on'
        has_text = request.form.get('has_text') == 'on' if has_blog else False
        has_checklist = request.form.get('has_checklist') == 'on' if has_blog else False
        has_music = request.form.get('has_music') == 'on' if has_blog else False
        
        description = request.form.get('description') if has_text else None
        music_title = request.form.get('music_title') if has_music else None
        music_artist = request.form.get('music_artist') if has_music else None
        music_cover = request.form.get('music_cover') if has_music else None
        music_preview = request.form.get('music_preview') if has_music else None
        
        ensure_category_exists(category)
        
        max_item_order = db.session.query(db.func.max(Item.sort_order)).filter_by(category=category).scalar()
        next_item_order = (max_item_order + 1) if max_item_order is not None else 0
        
        files = request.files.getlist('images')
        image_str = process_multiple_images(files)
        
        new_entry = Item(title=title, category=category, status=status, image=image_str, 
                        completion_date=completion_date, completion_month=completion_month, 
                        description=description, has_blog=has_blog, has_text=has_text, 
                        has_checklist=has_checklist, has_music=has_music, 
                        music_title=music_title, music_artist=music_artist, 
                        music_cover=music_cover, music_preview=music_preview,
                        sort_order=next_item_order, is_location=is_location, country=country)
        db.session.add(new_entry)
        db.session.flush()
        
        if has_checklist:
            checklist_texts = request.form.getlist('checklist_texts[]')
            for text in checklist_texts:
                if text.strip():
                    check_entry = ChecklistItem(item_id=new_entry.id, text=text.strip(), is_completed=False)
                    db.session.add(check_entry)
                    
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
        
    categories = Category.query.order_by(Category.sort_order.asc(), Category.name.asc()).all()
    sorted_countries = sorted(COUNTRIES.items(), key=lambda x: x[1]['name'])
    return render_template('new_item.html', categories=categories, COUNTRIES=sorted_countries)

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = db.session.get(Item, item_id)
    if request.method == 'POST':
        item.title = request.form.get('title')
        existing_category = request.form.get('existing_category')
        new_category = request.form.get('new_category')
        item.category = new_category.strip() if (new_category and new_category.strip() != "") else existing_category
        item.status = request.form.get('status')
        item.completion_date = request.form.get('completion_date')
        item.completion_month = request.form.get('completion_month')
        
        item.is_location = request.form.get('is_location') == 'on'
        item.country = request.form.get('country').lower() if request.form.get('country') else None
        
        item.has_blog = request.form.get('has_blog') == 'on'
        item.has_text = request.form.get('has_text') == 'on' if item.has_blog else False
        item.has_checklist = request.form.get('has_checklist') == 'on' if item.has_blog else False
        item.has_music = request.form.get('has_music') == 'on' if item.has_blog else False
        
        item.description = request.form.get('description') if item.has_text else None
        item.music_title = request.form.get('music_title') if item.has_music else None
        item.music_artist = request.form.get('music_artist') if item.has_music else None
        item.music_cover = request.form.get('music_cover') if item.has_music else None
        item.music_preview = request.form.get('music_preview') if item.has_music else None
        
        ensure_category_exists(item.category)
        
        ChecklistItem.query.filter_by(item_id=item.id).delete()
        if item.has_checklist:
            checklist_texts = request.form.getlist('checklist_texts[]')
            for text in checklist_texts:
                if text.strip():
                    check_entry = ChecklistItem(item_id=item.id, text=text.strip(), is_completed=False)
                    db.session.add(check_entry)
        
        kept_images = request.form.getlist('keep_images')
        new_files = request.files.getlist('images')
        new_filenames = []
        for file in new_files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_filenames.append(filename)
                
        combined_images = kept_images + new_filenames
        item.image = ",".join(combined_images) if combined_images else None
            
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
        
    categories = Category.query.order_by(Category.sort_order.asc(), Category.name.asc()).all()
    existing_images = item.image.split(',') if item.image else []
    sorted_countries = sorted(COUNTRIES.items(), key=lambda x: x[1]['name'])
    return render_template('edit_item.html', item=item, categories=categories, existing_images=existing_images, COUNTRIES=sorted_countries)

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
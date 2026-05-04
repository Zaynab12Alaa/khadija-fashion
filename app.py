from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os, json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'khadija-fashion-secret-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///khadija.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ── Models ─────────────────────────────────────────────
class Product(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(120), nullable=False)
    category  = db.Column(db.String(80))
    price     = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image     = db.Column(db.String(200), default='')
    badge     = db.Column(db.String(40), default='')
    in_stock  = db.Column(db.Boolean, default=True)
    created   = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(200), nullable=False)
    content   = db.Column(db.Text, nullable=False)
    excerpt   = db.Column(db.String(300))
    image     = db.Column(db.String(200), default='')
    created   = db.Column(db.DateTime, default=datetime.utcnow)

class LookbookItem(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(120))
    season    = db.Column(db.String(60))
    image     = db.Column(db.String(200), default='')
    created   = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100))
    email     = db.Column(db.String(120))
    message   = db.Column(db.Text)
    read      = db.Column(db.Boolean, default=False)
    created   = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))

# ── Helpers ────────────────────────────────────────────
def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def cart_count():
    return sum(item['qty'] for item in session.get('cart', {}).values())

app.jinja_env.globals['cart_count'] = cart_count

# ── Public Routes ──────────────────────────────────────
@app.route('/')
def index():
    featured   = Product.query.filter_by(in_stock=True).order_by(Product.created.desc()).limit(6).all()
    blog_posts = BlogPost.query.order_by(BlogPost.created.desc()).limit(3).all()
    lookbook   = LookbookItem.query.order_by(LookbookItem.created.desc()).limit(4).all()
    return render_template('index.html', featured=featured, blog_posts=blog_posts, lookbook=lookbook)

@app.route('/shop')
def shop():
    category = request.args.get('category', '')
    q = Product.query.filter_by(in_stock=True)
    if category:
        q = q.filter_by(category=category)
    products   = q.order_by(Product.created.desc()).all()
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('shop.html', products=products, categories=categories, selected=category)

@app.route('/product/<int:pid>')
def product_detail(pid):
    product = Product.query.get_or_404(pid)
    related = Product.query.filter(Product.category==product.category, Product.id!=pid).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)

@app.route('/blog')
def blog():
    posts = BlogPost.query.order_by(BlogPost.created.desc()).all()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:pid>')
def blog_post(pid):
    post = BlogPost.query.get_or_404(pid)
    return render_template('blog_post.html', post=post)

@app.route('/lookbook')
def lookbook():
    items = LookbookItem.query.order_by(LookbookItem.created.desc()).all()
    return render_template('lookbook.html', items=items)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        msg = ContactMessage(
            name=request.form['name'],
            email=request.form['email'],
            message=request.form['message']
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message sent! We\'ll get back to you soon. ✨', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ── Cart ───────────────────────────────────────────────
@app.route('/cart')
def cart():
    cart  = session.get('cart', {})
    items = []
    total = 0
    for pid, item in cart.items():
        p = Product.query.get(int(pid))
        if p:
            subtotal = p.price * item['qty']
            total   += subtotal
            items.append({'product': p, 'qty': item['qty'], 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add/<int:pid>', methods=['POST'])
def cart_add(pid):
    cart = session.get('cart', {})
    key  = str(pid)
    qty  = int(request.form.get('qty', 1))
    cart[key] = {'qty': cart.get(key, {}).get('qty', 0) + qty}
    session['cart'] = cart
    flash('Added to cart! 🛍️', 'success')
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart/remove/<int:pid>')
def cart_remove(pid):
    cart = session.get('cart', {})
    cart.pop(str(pid), None)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart/count')
def cart_count_api():
    return jsonify({'count': cart_count()})

# ── Admin Auth ─────────────────────────────────────────
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(username=request.form['username']).first()
        if admin and check_password_hash(admin.password, request.form['password']):
            session['admin'] = admin.username
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# ── Admin Dashboard ────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = {
        'products':  Product.query.count(),
        'posts':     BlogPost.query.count(),
        'lookbook':  LookbookItem.query.count(),
        'messages':  ContactMessage.query.filter_by(read=False).count(),
    }
    messages = ContactMessage.query.order_by(ContactMessage.created.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, messages=messages)

# ── Admin Products ─────────────────────────────────────
@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.order_by(Product.created.desc()).all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/new', methods=['GET','POST'])
@admin_required
def admin_product_new():
    if request.method == 'POST':
        img = ''
        if 'image' in request.files:
            f = request.files['image']
            if f and allowed_file(f.filename):
                fn = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                img = fn
        p = Product(
            name=request.form['name'],
            category=request.form['category'],
            price=float(request.form['price']),
            description=request.form['description'],
            badge=request.form.get('badge',''),
            image=img,
            in_stock='in_stock' in request.form
        )
        db.session.add(p)
        db.session.commit()
        flash('Product added! ✨', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=None)

@app.route('/admin/products/edit/<int:pid>', methods=['GET','POST'])
@admin_required
def admin_product_edit(pid):
    p = Product.query.get_or_404(pid)
    if request.method == 'POST':
        p.name        = request.form['name']
        p.category    = request.form['category']
        p.price       = float(request.form['price'])
        p.description = request.form['description']
        p.badge       = request.form.get('badge','')
        p.in_stock    = 'in_stock' in request.form
        if 'image' in request.files:
            f = request.files['image']
            if f and allowed_file(f.filename):
                fn = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                p.image = fn
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=p)

@app.route('/admin/products/delete/<int:pid>')
@admin_required
def admin_product_delete(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))

# ── Admin Blog ─────────────────────────────────────────
@app.route('/admin/blog')
@admin_required
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.created.desc()).all()
    return render_template('admin/blog.html', posts=posts)

@app.route('/admin/blog/new', methods=['GET','POST'])
@admin_required
def admin_blog_new():
    if request.method == 'POST':
        post = BlogPost(
            title=request.form['title'],
            content=request.form['content'],
            excerpt=request.form.get('excerpt',''),
        )
        if 'image' in request.files:
            f = request.files['image']
            if f and allowed_file(f.filename):
                fn = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                post.image = fn
        db.session.add(post)
        db.session.commit()
        flash('Blog post published! 📝', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog_form.html', post=None)

@app.route('/admin/blog/edit/<int:pid>', methods=['GET','POST'])
@admin_required
def admin_blog_edit(pid):
    post = BlogPost.query.get_or_404(pid)
    if request.method == 'POST':
        post.title   = request.form['title']
        post.content = request.form['content']
        post.excerpt = request.form.get('excerpt','')
        if 'image' in request.files:
            f = request.files['image']
            if f and allowed_file(f.filename):
                fn = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                post.image = fn
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog_form.html', post=post)

@app.route('/admin/blog/delete/<int:pid>')
@admin_required
def admin_blog_delete(pid):
    post = BlogPost.query.get_or_404(pid)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('admin_blog'))

# ── Admin Lookbook ─────────────────────────────────────
@app.route('/admin/lookbook')
@admin_required
def admin_lookbook():
    items = LookbookItem.query.order_by(LookbookItem.created.desc()).all()
    return render_template('admin/lookbook.html', items=items)

@app.route('/admin/lookbook/new', methods=['GET','POST'])
@admin_required
def admin_lookbook_new():
    if request.method == 'POST':
        item = LookbookItem(
            title=request.form['title'],
            season=request.form['season'],
        )
        if 'image' in request.files:
            f = request.files['image']
            if f and allowed_file(f.filename):
                fn = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                item.image = fn
        db.session.add(item)
        db.session.commit()
        flash('Lookbook item added!', 'success')
        return redirect(url_for('admin_lookbook'))
    return render_template('admin/lookbook_form.html', item=None)

@app.route('/admin/lookbook/delete/<int:lid>')
@admin_required
def admin_lookbook_delete(lid):
    item = LookbookItem.query.get_or_404(lid)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin_lookbook'))

# ── Admin Messages ─────────────────────────────────────
@app.route('/admin/messages')
@admin_required
def admin_messages():
    msgs = ContactMessage.query.order_by(ContactMessage.created.desc()).all()
    for m in msgs:
        m.read = True
    db.session.commit()
    return render_template('admin/messages.html', messages=msgs)

# ── Init DB ────────────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            db.session.add(Admin(
                username='khadija',
                password=generate_password_hash('fashion2025')
            ))
            # Seed sample products
            samples = [
                Product(name='Silk Reverie Dress', category='Evening Wear', price=120, description='Elegant evening piece with a luxurious silk finish.', badge='New'),
                Product(name='Golden Hour Coat',   category='Outerwear',    price=180, description='Structured coat with gold-tone buttons.', badge='Bestseller'),
                Product(name='Desert Bloom Set',   category='Accessories',  price=65,  description='Handcrafted accessories inspired by desert florals.'),
                Product(name='Statement Heels',    category='Footwear',     price=95,  description='Bold heels that make every step a statement.'),
                Product(name='Lunar Jewel Set',    category='Jewelry',      price=75,  description='Limited edition fine jewelry set.', badge='Limited'),
                Product(name='Structured Tote',    category='Bags',         price=110, description='Clean lines, premium leather tote.'),
            ]
            db.session.add_all(samples)
            db.session.add(BlogPost(
                title='Welcome to Khadija Fashion',
                content='This is the beginning of something beautiful. Our first collection is live!',
                excerpt='The beginning of something beautiful...'
            ))
            db.session.commit()

# Always initialize DB on startup (required for Railway)
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

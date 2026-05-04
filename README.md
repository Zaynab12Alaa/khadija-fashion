# KHADIJA Fashion Website

A full-stack fashion brand website built with Python (Flask) + HTML/CSS/JS.

## Features
- 🛍️ **Shop** — product catalog with category filters
- 👗 **Product pages** — detail view + add to cart
- 🛒 **Shopping cart** — session-based cart
- 📸 **Lookbook** — seasonal visual gallery
- 📝 **Blog/Journal** — fashion posts
- 📬 **Contact** — message form
- 🔐 **Admin Panel** — full CRUD for products, blog, lookbook, messages

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

## Admin Panel
Go to: `http://localhost:5000/admin/login`

Default credentials:
- **Username:** `khadija`
- **Password:** `fashion2025`

> ⚠️ Change the password after first login by editing `app.py` → `init_db()` section.

## Project Structure
```
khadija_fashion/
├── app.py                  # Flask backend (all routes + models)
├── requirements.txt
├── static/
│   ├── css/
│   │   ├── main.css        # Public site styles
│   │   └── admin.css       # Admin panel styles
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── products/       # Uploaded product images go here
└── templates/
    ├── base.html           # Public layout
    ├── index.html          # Homepage
    ├── shop.html           # Shop listing
    ├── product_detail.html
    ├── lookbook.html
    ├── blog.html
    ├── blog_post.html
    ├── contact.html
    ├── cart.html
    └── admin/
        ├── base.html       # Admin layout
        ├── login.html
        ├── dashboard.html
        ├── products.html
        ├── product_form.html
        ├── blog.html
        ├── blog_form.html
        ├── lookbook.html
        ├── lookbook_form.html
        └── messages.html
```

## Database
SQLite database (`khadija.db`) is auto-created on first run with sample data.

## Customization
- Edit colors in `static/css/main.css` under `:root` variables
- Change brand name/tagline in `templates/base.html`
- Update contact info in `templates/contact.html`

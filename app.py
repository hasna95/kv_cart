import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from flask_compress import Compress




# Use Flask
app = Flask(__name__)
Compress(app)

app.secret_key = os.environ.get("SECRET_KEY", "super-secret")  # Use env var or fallback


# Database connection
def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
         CREATE TABLE IF NOT EXISTS users (
             id SERIAL PRIMARY KEY,
             email TEXT UNIQUE NOT NULL,
             password TEXT NOT NULL,
             first_name TEXT NOT NULL,
             last_name TEXT NOT NULL,
             phone TEXT NOT NULL,
             dob DATE NOT NULL,
             address TEXT NOT NULL
         );
     ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
        product_id TEXT,
        name TEXT,
        full_details TEXT,
        share_text TEXT,
        image TEXT,
        min_catalog_price INTEGER,
        product_images TEXT, 
        category TEXT
            );
        ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            UNIQUE(user_id, product_id)
        );
    ''')

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']
        dob = request.form['dob']
        address = request.form.get('address', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, password, phone, dob, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (first_name, last_name, email, password, phone, dob, address))
            conn.commit()
            flash('Registered successfully! Please login.')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Email already registered!')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/api/baby-products')
def api_baby_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, min_catalog_price, image FROM products WHERE category = 'gown' LIMIT 20")
    veggies = cursor.fetchall()
    conn.close()
    return jsonify([{"id": v[0], "name": v[1], "price": float(v[2]), "image_url": v[3]} for v in veggies])


@app.route('/api/women-gowns')
def api_women_growns():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, min_catalog_price, image FROM products WHERE category = 'gown' LIMIT 20")
    fruits = cursor.fetchall()
    conn.close()
    return jsonify([{"id": f[0], "name": f[1], "price": float(f[2]), "image_url": f[3]} for f in fruits])


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        full_details = product[3]
        lines = full_details.split('\\n') if full_details else []
        sizes = []
        collecting_sizes = False

        for line in lines:
            if 'Sizes:' in line:
                collecting_sizes = True
            elif 'Dispatch' in line:
                collecting_sizes = False
            elif collecting_sizes:
                if '(' in line:
                    size_info = line.split('(')[0].strip()
                    if size_info:
                        sizes.append(size_info)

        product_info = {
            "id": product[0],
            "product_id": product[1],
            "name": product[2],
            "full_details": full_details,
            "share_text": product[4],
            "image_url": product[5],
            "min_catalog_price": product[6],
            "product_images": product[7],
            "category": product[8],
            "sizes": sizes   # ✅ Pass ready sizes list
        }
        return render_template('product.html', product=product_info)
    else:
        return "Product not found", 404



@app.route('/api/wishlist/toggle', methods=['POST'])
def toggle_wishlist():
    import json
    data = json.loads(request.data)
    user_id = session.get('user_id')
    product_id = data.get('product_id')

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wishlist WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM wishlist WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "removed"})
    else:
        cursor.execute("INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "added"})


@app.route('/api/wishlist/count')
def wishlist_count():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"count": 0})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM wishlist WHERE user_id = %s", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"count": count})


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    import json
    data = json.loads(request.data)
    user_id = session.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    size = data.get('size')  # 👈✅ new

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO cart (user_id, product_id, quantity, size)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, product_id, size) DO UPDATE
        SET quantity = cart.quantity + EXCLUDED.quantity
    ''', (user_id, product_id, quantity, size))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


    return jsonify({"status": "success"})


@app.route('/api/cart')
def get_cart():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.product_id, p.name, p.min_catalog_price, p.image, c.quantity, c.size
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    ''', (user_id,))
    cart_items = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            'product_id': row[0],
            'name': row[1],
            'price': float(row[2]),
            'image_url': row[3],
            'quantity': row[4],
            'size': row[5] if row[5] else None
        }
        for row in cart_items
    ])



@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    import json
    user_id = session.get('user_id')
    data = json.loads(request.data)
    product_id = data['product_id']
    quantity = data['quantity']

    conn = get_db_connection()
    cursor = conn.cursor()
    if quantity > 0:
        cursor.execute('''
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity
        ''', (user_id, product_id, quantity))
    else:
        cursor.execute('DELETE FROM cart WHERE user_id = %s AND product_id = %s', (user_id, product_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/cart/count')
def cart_count():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(quantity) FROM cart WHERE user_id = %s', (user_id,))
    count = cursor.fetchone()[0] or 0
    conn.close()
    return jsonify({'count': count})


@app.route('/cart')
def cart_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('cart.html')


@app.route('/wishlist')
def wishlist_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('wishlist.html')


@app.route('/api/wishlist/items')
def get_wishlist_items():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.image, p.min_catalog_price
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = %s
    ''', (user_id,))
    data = cursor.fetchall()
    conn.close()
    return jsonify([
        {
            'id': row[0],
            'name': row[1],
            'image_url': row[2],    # frontend expects 'image_url' key
            'price': float(row[3])  # send price in rupees, will convert on frontend
        }
        for row in data
    ])


@app.route('/api/wishlist/clear', methods=['POST'])
def clear_wishlist():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wishlist WHERE user_id = %s', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'cleared'})


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()

    if not query:
        return render_template('search.html', products=[], query='')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, price, image_url
        FROM products
        WHERE LOWER(name) LIKE %s
    ''', (f'%{query.lower()}%',))
    results = cursor.fetchall()
    conn.close()

    products = [{
        'id': row[0],
        'name': row[1],
        'price': float(row[2]),
        'image_url': row[3]
    } for row in results]

    return render_template('search.html', products=products, query=query)


@app.route('/products')
def product_listing():
    category = request.args.get('category', 'gown')
    page = int(request.args.get('page', 1))
    limit = 20
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, min_catalog_price, image
        FROM products
        WHERE category = %s
        ORDER BY id
        LIMIT %s OFFSET %s
    ''', (category, limit, offset))
    products = cursor.fetchall()
    conn.close()

    products_data = [{
        'id': p[0],
        'name': p[1],
        'price': float(p[2]),
        'image_url': p[3]
    } for p in products]

    return render_template('products.html', products=products_data, category=category, page=page)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

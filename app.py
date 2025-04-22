import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify

# Use Flask
app = Flask(__name__)
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
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price DECIMAL(6, 2),
            stock INTEGER,
            image_url TEXT,
            rating DECIMAL(2, 1),
            is_available BOOLEAN,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        address = request.form['address']

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


@app.route('/api/vegetables')
def api_vegetables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_url FROM products WHERE category = 'vegetable'")
    veggies = cursor.fetchall()
    conn.close()
    return jsonify([{"id": v[0], "name": v[1], "price": float(v[2]), "image_url": v[3]} for v in veggies])


@app.route('/api/fruits')
def api_fruits():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_url FROM products WHERE category = 'fruit'")
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
        product_info = {
            "id": product[0],
            "name": product[1],
            "category": product[2],
            "description": product[3],
            "price": product[4],
            "stock": product[5],
            "image_url": product[6],
            "rating": product[7],
            "is_available": product[8],
            "added_on": product[9]
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

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
    stock = cursor.fetchone()

    if not stock or stock[0] < int(quantity):
        return jsonify({"error": "Insufficient stock"}), 400

    cursor.execute("""
        INSERT INTO cart (user_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, product_id) DO UPDATE
        SET quantity = cart.quantity + EXCLUDED.quantity
    """, (user_id, product_id, quantity))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


@app.route('/api/cart')
def get_cart():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.product_id, p.name, p.price, p.image_url, c.quantity
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
            'quantity': row[4]
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
        SELECT p.id, p.name, p.image_url, p.price
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = %s
    ''', (user_id,))
    data = cursor.fetchall()
    conn.close()
    return jsonify([
        {'id': row[0], 'name': row[1], 'image_url': row[2], 'price': float(row[3])}
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


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

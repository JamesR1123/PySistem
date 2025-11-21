import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mysecretkey')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('condo_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS condos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL,
            image_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condo_id INTEGER,
            renter_name TEXT NOT NULL,
            FOREIGN KEY (condo_id) REFERENCES condos (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
        conn.commit()
    conn.close()
    
def get_db_connection():
    conn = sqlite3.connect('condo_system.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/search_condos')
def search_condos():
    location = request.args.get('location', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    status = request.args.get('status', '').strip()
    
    query = "SELECT * FROM condos WHERE 1=1"
    params = []
    
    if location:
        query += " AND location LIKE ?"
        params.append(f'%{location}%')
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    if status:
        query += " AND status = ?"
        params.append(status)
    
    conn = get_db_connection()
    condos = conn.execute(query, params).fetchall()
    conn.close()
    
    condos_list = [dict(condo) for condo in condos]
    return jsonify(condos_list)

@app.route('/')
def home_page():
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    status = request.args.get('status', 'Available')
    
    query = "SELECT * FROM condos WHERE status = 'Available'"
    params = []
    
    if location:
        query += " AND location LIKE ?"
        params.append(f'%{location}%')
    if min_price:
        query += " AND price >= ?"
        params.append(float(min_price))
    if max_price:
        query += " AND price <= ?"
        params.append(float(max_price))
    
    conn = get_db_connection()
    condos = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('home.html', condos=condos, location=location, min_price=min_price, max_price=max_price, status=status)

# --- REGISTRATION SYSTEM ---
@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        flash("Passwords do not match", "error")
        return render_template('register.html')
    
    if len(password) < 6:
        flash("Password must be at least 6 characters long", "error")
        return render_template('register.html')
    
    conn = get_db_connection()
    existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if existing_user:
        conn.close()
        flash("Username already exists. Please choose another.", "error")
        return render_template('register.html')
    
    hashed_pw = generate_password_hash(password)
    try:
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                    (username, hashed_pw, 'user'))
        conn.commit()
        conn.close()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login_page'))
    except Exception as e:
        conn.close()
        flash("Registration failed. Please try again.", "error")
        return render_template('register.html')

# --- LOGIN SYSTEM ---
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['username'] = username
        session['role'] = user['role']
        return redirect(url_for('dashboard'))
    flash("Invalid username or password", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home_page'))

# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    user_role = session.get('role', 'user')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    status = request.args.get('status', '')
    
    if user_role == 'admin':
        query = "SELECT * FROM condos WHERE 1=1"
    else:
        query = "SELECT * FROM condos WHERE status = 'Available'"
    
    params = []
    
    if location:
        query += " AND location LIKE ?"
        params.append(f'%{location}%')
    if min_price:
        query += " AND price >= ?"
        params.append(float(min_price))
    if max_price:
        query += " AND price <= ?"
        params.append(float(max_price))
    if status and user_role == 'admin':
        query += " AND status = ?"
        params.append(status)
    
    conn = get_db_connection()
    condos = conn.execute(query, params).fetchall()
    conn.close()
    
    if user_role == 'admin':
        return render_template('admin_dashboard.html', condos=condos, username=session['username'], location=location, min_price=min_price, max_price=max_price, status=status)
    else:
        return render_template('user_dashboard.html', condos=condos, username=session['username'], location=location, min_price=min_price, max_price=max_price)

# --- ADD CONDO ---
@app.route('/add_condo', methods=['POST'])
def add_condo():
    if 'username' not in session:
        flash("You must be logged in to add condos.", "error")
        return redirect(url_for('login_page'))
    
    if session.get('role') != 'admin':
        flash("Only admins can add condos.", "error")
        return redirect(url_for('dashboard'))
    
    name = request.form.get('name')
    location = request.form.get('location')
    price_str = request.form.get('price')
    
    if not name or not location or not price_str:
        flash("All fields (name, location, price) are required.", "error")
        return redirect(url_for('dashboard'))
    
    try:
        price = float(price_str)
        if price <= 0:
            raise ValueError
    except ValueError:
        flash("Price must be a positive number.", "error")
        return redirect(url_for('dashboard'))
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(file_path)
                image_url = filename
            except Exception as e:
                print(f"File save error: {e}")
                flash("Error uploading image. Try again.", "error")
                return redirect(url_for('dashboard'))
        elif file and not allowed_file(file.filename):
            flash("Invalid image file type. Use PNG, JPG, etc.", "error")
            return redirect(url_for('dashboard'))
    
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO condos (name, location, price, status, image_url) VALUES (?, ?, ?, ?, ?)',
            (name, location, price, 'Available', image_url)
        )
        conn.commit()
        conn.close()
        flash("Condo added successfully!", "success")
    except Exception as e:
        print(f"Database error: {e}")
        flash("Error adding condo. Please try again.", "error")
    
    return redirect(url_for('dashboard'))

# --- DELETE CONDO ---
@app.route('/delete_condo/<int:condo_id>')
def delete_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    if session.get('role') != 'admin':
        flash("Only admins can delete condos.", "error")
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    condo = conn.execute('SELECT image_url FROM condos WHERE id = ?', (condo_id,)).fetchone()
    if condo and condo['image_url']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], condo['image_url'])
        if os.path.exists(image_path):
            os.remove(image_path)
    conn.execute('DELETE FROM condos WHERE id = ?', (condo_id,))
    conn.commit()
    conn.close()
    flash("Condo deleted!", "success")
    return redirect(url_for('dashboard'))

# --- EDIT CONDO ---
@app.route('/edit_condo/<int:condo_id>')
def edit_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    if session.get('role') != 'admin':
        flash("Only admins can edit condos.", "error")
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    condo = conn.execute('SELECT * FROM condos WHERE id = ?', (condo_id,)).fetchone()
    conn.close()
    if not condo:
        flash("Condo not found", "error")
        return redirect(url_for('dashboard'))
    return render_template('edit_condo.html', condo=condo)

@app.route('/update_condo/<int:condo_id>', methods=['POST'])
def update_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    if session.get('role') != 'admin':
        flash("Only admins can update condos.", "error")
        return redirect(url_for('dashboard'))
    
    name = request.form['name']
    location = request.form['location']
    price = request.form['price']
    status = request.form['status']
    
    conn = get_db_connection()
    condo = conn.execute('SELECT image_url FROM condos WHERE id = ?', (condo_id,)).fetchone()
    old_image = condo['image_url'] if condo else None
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = filename
            if old_image:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image)
                if os.path.exists(old_path):
                    os.remove(old_path)
    
    if image_url:
        conn.execute(
            'UPDATE condos SET name=?, location=?, price=?, status=?, image_url=? WHERE id=?',
            (name, location, price, status, image_url, condo_id)
        )
    else:
        conn.execute(
            'UPDATE condos SET name=?, location=?, price=?, status=? WHERE id=?',
            (name, location, price, status, condo_id)
        )
    conn.commit()
    conn.close()
    flash("Condo updated!", "success")
    return redirect(url_for('dashboard'))

# --- BOOK CONDO ---
@app.route('/book_condo/<int:condo_id>', methods=['GET', 'POST'])
def book_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    condo = conn.execute('SELECT * FROM condos WHERE id = ?', (condo_id,)).fetchone()
    if not condo:
        conn.close()
        flash("Condo not found", "error")
        return redirect(url_for('dashboard'))
    
    if condo['status'] != 'Available':
        conn.close()
        flash("Condo is not available for booking", "error")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        renter_name = session['username']
        conn.execute('INSERT INTO bookings (condo_id, renter_name) VALUES (?, ?)', (condo_id, renter_name))
        conn.execute('UPDATE condos SET status = ? WHERE id = ?', ('Booked', condo_id))
        conn.commit()
        conn.close()
        flash("Condo booked successfully!", "success")
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('book_condo.html', condo=condo)

# --- MY BOOKINGS ---
@app.route('/my_bookings')
def my_bookings():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT bookings.id, condos.name, bookings.renter_name
        FROM bookings
        JOIN condos ON bookings.condo_id = condos.id
        WHERE bookings.renter_name = ?
    ''', (session['username'],)).fetchall()
    conn.close()
    return render_template('my_bookings.html', bookings=bookings)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mysecretkey"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
            password TEXT NOT NULL
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
        conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('condo_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- HOME PAGE (Public Landing) ---
@app.route('/home')
def home_page():
    conn = get_db_connection()
    condos = conn.execute('SELECT * FROM condos').fetchall()
    conn.close()
    return render_template('home.html', condos=condos)

# --- LOGIN SYSTEM ---
users = {"admin": "admin123"}

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="Invalid username or password")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

# --- DASHBOARD ---
@app.route('/main')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    condos = conn.execute('SELECT * FROM condos').fetchall()
    conn.close()
    return render_template('index.html', condos=condos, username=session['username'])

# --- ADD CONDO ---
@app.route('/add_condo', methods=['POST'])
def add_condo():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    name = request.form['name']
    location = request.form['location']
    price = request.form['price']

    image_url = None  # default if no image uploaded

    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f"uploads/{filename}"  # store relative path for HTML

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO condos (name, location, price, status, image_url) VALUES (?, ?, ?, ?, ?)',
        (name, location, price, 'Available', image_url)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# --- DELETE CONDO ---
@app.route('/delete_condo/<int:condo_id>')
def delete_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    conn.execute('DELETE FROM condos WHERE id = ?', (condo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# --- EDIT CONDO ---
@app.route('/edit_condo/<int:condo_id>')
def edit_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    condo = conn.execute('SELECT * FROM condos WHERE id = ?', (condo_id,)).fetchone()
    conn.close()
    if not condo:
        return "Condo not found", 404
    return render_template('edit_condo.html', condo=condo)

@app.route('/update_condo/<int:condo_id>', methods=['POST'])
def update_condo(condo_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    name = request.form['name']
    location = request.form['location']
    price = request.form['price']
    status = request.form['status']

    image = request.files.get('image')
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        UPLOAD_FOLDER = os.path.join('static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        image_url = f"uploads/{filename}"  # relative to 'static' folder

        cursor.execute("""
            UPDATE condos SET name=?, location=?, price=?, status=?, image_url=? WHERE id=?
        """, (name, location, price, status, image_url, condo_id))
    else:
        cursor.execute("""
            UPDATE condos SET name=?, location=?, price=?, status=? WHERE id=?
        """, (name, location, price, status, condo_id))

    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))



# --- BOOK CONDO ---
@app.route('/book_condo/<int:condo_id>')
def book_condo_page(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    conn.execute('UPDATE condos SET status = ? WHERE id = ?', ('Booked', condo_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

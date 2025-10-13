import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mysecretkey"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('condo_system.db')
    cursor = conn.cursor()
    # Create Condos Table
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
    # Create Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condo_id INTEGER,
            renter_name TEXT NOT NULL,
            FOREIGN KEY (condo_id) REFERENCES condos (id)
        )
    ''')
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Now, safely check if the admin user exists
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
        conn.commit()
    conn.close()

# Helper to get DB connection
def get_db_connection():
    conn = sqlite3.connect('condo_system.db')
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

# --- USER AUTHENTICATION ---
# Dummy users data for simplicity
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
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error="Invalid username or password")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

# --- MAIN DASHBOARD ---
@app.route('/main')
def home():
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
    image_url = None

    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO condos (name, location, price, status, image_url) VALUES (?, ?, ?, ?, ?)',
        (name, location, price, 'Available', image_url)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# --- DELETE CONDO ---
@app.route('/delete_condo/<int:condo_id>')
def delete_condo(condo_id):
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    conn.execute('DELETE FROM condos WHERE id = ?', (condo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

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
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    name = request.form['name']
    location = request.form['location']
    price = request.form['price']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute(
        'UPDATE condos SET name = ?, location = ?, price = ?, status = ? WHERE id = ?',
        (name, location, price, status, condo_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# --- BOOKING (kept simple for now) ---
@app.route('/book_condo/<int:condo_id>')
def book_condo_page(condo_id):
    # In a real app, you'd have a form here. We'll just update status.
    if 'username' not in session:
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    conn.execute('UPDATE condos SET status = ? WHERE id = ?', ('Booked', condo_id))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))


if __name__ == '__main__':
    init_db() # Initialize the database when the app starts
    app.run(debug=True)
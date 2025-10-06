from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory data
condos = []
bookings = []

@app.route('/')
def home():
    return render_template('incex.html', condos=condos)

# Add Condo
@app.route('/add_condo', methods=['POST'])
def add_condo():
    name = request.form['name']
    location = request.form['location']
    price = request.form['price']
    condo_id = len(condos) + 1
    condo = {"id": condo_id, "name": name, "location": location, "price": price}
    condos.append(condo)
    return redirect(url_for('home'))

# Delete Condo
@app.route('/delete_condo/<int:condo_id>')
def delete_condo(condo_id):
    global condos
    condos = [c for c in condos if c["id"] != condo_id]
    return redirect(url_for('home'))

# Edit Condo - Page
@app.route('/edit_condo/<int:condo_id>')
def edit_condo(condo_id):
    condo = next((c for c in condos if c["id"] == condo_id), None)
    if not condo:
        return "Condo not found", 404
    return render_template('edit_condo.html', condo=condo)

# Update Condo (POST)
@app.route('/update_condo/<int:condo_id>', methods=['POST'])
def update_condo(condo_id):
    for c in condos:
        if c["id"] == condo_id:
            c["name"] = request.form['name']
            c["location"] = request.form['location']
            c["price"] = request.form['price']
            break
    return redirect(url_for('home'))

# Book Condo
@app.route('/book_condo', methods=['POST'])
def book_condo():
    renter = request.form['renter']
    condo_name = request.form['condo']
    booking = {"renter": renter, "condo": condo_name}
    bookings.append(booking)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

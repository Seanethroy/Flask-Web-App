from flask import Flask, render_template, request, redirect, url_for, session, flash
import json

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

def load_data():
    with open('data/flowers.json') as f:
        flowers = json.load(f)
    with open('data/addons.json') as f:
        addons = json.load(f)
    return flowers, addons

@app.route('/')
def home():
    flowers, addons = load_data()
    cart = session.get('cart', {})
    return render_template('index.html', flowers=flowers, addons=addons, cart=cart)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower']
    quantity = int(request.form.get('quantity', 1))
    
    flowers, _ = load_data()
    if flower in flowers:
        if 'cart' not in session:
            session['cart'] = {}
        
        if flower in session['cart']:
            session['cart'][flower]['quantity'] += quantity
        else:
            session['cart'][flower] = {
                'price': flowers[flower]['price'],
                'quantity': quantity
            }
        flash(f"✅ Added {quantity} {flower}(s) to cart!")
    return redirect(url_for('home'))

@app.route('/remove_from_cart/<item>')
def remove_from_cart(item):
    if 'cart' in session and item in session['cart']:
        del session['cart'][item]
        flash(f"🗑️ Removed {item} from cart.")
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

if __name__ == '__main__':
    app.run(debug=True)
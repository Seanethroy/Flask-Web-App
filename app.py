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

def calculate_total(cart, selected_addons):
    total = 0
    # Flowers total
    for details in cart.values():
        total += details['price'] * details['quantity']
    # Add-ons total
    for price in selected_addons.values():
        total += price
    return total

@app.route('/')
def home():
    flowers, addons = load_data()
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    total = calculate_total(cart, selected_addons)
    return render_template('index.html', 
                         flowers=flowers, 
                         addons=addons, 
                         cart=cart, 
                         selected_addons=selected_addons,
                         total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form.get('customer_name', '').strip().title()
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    
    if not customer_name:
        flash("❌ Please enter your name.")
        return redirect(url_for('home'))
    
    if not cart and not selected_addons:
        flash("❌ Your cart is empty!")
        return redirect(url_for('home'))
    
    total = calculate_total(cart, selected_addons)
    
    # Pass data to invoice
    return render_template('invoices.html', 
                         customer_name=customer_name,
                         cart=cart,
                         selected_addons=selected_addons,
                         total=total)

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

@app.route('/select_addons', methods=['POST'])
def select_addons():
    selected = request.form.getlist('addons')
    flowers, addons = load_data()
    
    if 'selected_addons' not in session:
        session['selected_addons'] = {}
    
    for addon in selected:
        if addon in addons:
            session['selected_addons'][addon] = addons[addon]['price']
    
    if selected:
        flash(f"✅ Added {len(selected)} add-on(s) to cart!")
    else:
        flash("No add-ons selected.")
    return redirect(url_for('home'))

@app.route('/remove_from_cart/<item>')
def remove_from_cart(item):
    if 'cart' in session and item in session['cart']:
        del session['cart'][item]
        flash(f"🗑️ Removed all {item} from the cart.")
    return redirect(url_for('home'))

@app.route('/cancel_order')
def cancel_order():
    session.pop('cart', None)
    session.pop('selected_addons', None)
    flash("🗑️ Order has been cancelled.")
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
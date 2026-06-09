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
    flower_subtotal = 0
    addon_subtotal = 0
    
    # Calculate flower subtotal
    for details in cart.values():
        flower_subtotal += details['price'] * details['quantity']
    
    # Calculate add-on subtotal
    for price in selected_addons.values():
        addon_subtotal += price
    
    total = flower_subtotal + addon_subtotal
    return total, flower_subtotal, addon_subtotal

@app.route('/')
def home():
    flowers, addons = load_data()
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    
    total, flower_subtotal, addon_subtotal = calculate_total(cart, selected_addons)

    if total > 100:
     flash("Large order detected!")
    
    return render_template('index.html', 
                         flowers=flowers, 
                         addons=addons, 
                         cart=cart, 
                         selected_addons=selected_addons,
                         total=total,
                         flower_subtotal=flower_subtotal,
                         addon_subtotal=addon_subtotal)

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
    
    total, flower_subtotal, addon_subtotal = calculate_total(
    cart,
    selected_addons
)
    session.pop("cart", None)
    session.pop("selected_addons", None)  
    
    # Pass data to invoice
    return render_template(
    'invoices.html',
    customer_name=customer_name,
    cart=cart,
    selected_addons=selected_addons,
    total=total,
    flower_subtotal=flower_subtotal,
    addon_subtotal=addon_subtotal
)

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

@app.route("/select_addon", methods=["POST"])
def select_addon():

    _, addons = load_data()

    selected_keys = request.form.getlist("addons")

    selected_addons = {}

    for addon in selected_keys:

        if addon in addons:

            selected_addons[addon] = addons[addon]["price"]

    session["selected_addons"] = selected_addons

    if selected_addons:
        flash(f"{len(selected_addons)} add-ons added to cart.")
    else:
        flash("No add-ons selected.")

    return redirect(url_for("home"))

@app.route('/remove_from_cart/<item>')
def remove_from_cart(item):
    if 'cart' in session and item in session['cart']:
        del session['cart'][item]
        flash(f"Removed all {item.capitalize()} from the cart.")
    return redirect(url_for('home'))

@app.route('/cancel_order', methods=['POST'])
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
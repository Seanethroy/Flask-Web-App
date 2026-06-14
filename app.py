from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

def create_database():

    with sqlite3.connect("flower_shop.db") as conn:

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (

                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                customer_name TEXT,
                items TEXT,
                addons TEXT,
                total REAL,
                date TIMESTAMP

            )
        """)

        conn.commit()

def load_data():
    with open('data/flowers.json') as f:
        flowers = json.load(f)

    with open('data/addons.json') as f:
        addons = json.load(f)

    return flowers, addons


def calculate_total(cart, selected_addons):

    flower_subtotal = 0

    for item, details in cart.items():

        flower_subtotal += (
            details["price"] *
            details["quantity"]
        )

    addon_subtotal = sum(
        selected_addons.values()
    )

    total = flower_subtotal + addon_subtotal

    discount_applied = False

    if total > 180:

        total *= 0.9
        discount_applied = True

    return (
        flower_subtotal,
        addon_subtotal,
        total,
        discount_applied
    )


@app.route('/')
def home():

    flowers, addons = load_data()

    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})

    flower_subtotal, addon_subtotal, total, discount_applied = calculate_total(
      cart,
      selected_addons
  )

    if total > 100:
        flash("Large order detected!")

    return render_template(
        'index.html',
        flowers=flowers,
        addons=addons,
        cart=cart,
        selected_addons=selected_addons,
        total=total,
        flower_subtotal=flower_subtotal,
        addon_subtotal=addon_subtotal,
        discount_applied=discount_applied
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

        flash(
            f"Removed all {item.capitalize()} from the cart."
        )

    return redirect(url_for('home'))


@app.route('/cancel_order', methods=['POST'])
def cancel_order():

    session.pop('cart', None)
    session.pop('selected_addons', None)

    flash("Your order has been cancelled.")

    return redirect(url_for('home'))


@app.route('/checkout', methods=['POST'])
def checkout():

    customer_name = (
        request.form.get(
            'customer_name',
            ''
        ).strip().title()
    )

    cart = session.get('cart', {})
    selected_addons = session.get(
        'selected_addons',
        {}
    )

    if not customer_name:

        flash("Please enter your name.")
        return redirect(url_for('home'))

    if not cart and not selected_addons:

        flash("Your cart is empty!")
        return redirect(url_for('home'))

    flower_subtotal, addon_subtotal, total, discount_applied = calculate_total(
        cart,
        selected_addons
    )

    invoice_number = (
        "INV" +
        datetime.now().strftime("%Y%m%d%H%M%S")
    )

    with sqlite3.connect("flower_shop.db") as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO orders
            (
                invoice_number,
                customer_name,
                items,
                addons,
                total,
                date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            customer_name,
            json.dumps(cart),
            json.dumps(selected_addons),
            total,
            datetime.now()
        ))

        conn.commit()

    try:

        with open(
            f"invoice_{invoice_number}.txt",
            "w"
        ) as f:

            f.write(f"Invoice Number: {invoice_number}\n")
            f.write(f"Customer Name: {customer_name}\n")
            f.write(f"Total: ${total:.2f}\n")

    except OSError as e:

        flash("Could not generate invoice file.")
        print(f"Invoice Error: {e}")

    try:

        flowers, _ = load_data()

        for flower, details in cart.items():

            flowers[flower]["stock"] -= details["quantity"]

            if flowers[flower]["stock"] < 0:

                flowers[flower]["stock"] = 0

        with open(
            "data/flowers.json",
            "w"
        ) as f:

            json.dump(
                flowers,
                f,
                indent=4
            )

    except OSError:

        flash(
            "Could not update stock file."
        )

    session.pop("cart", None)
    session.pop("selected_addons", None)

    session.modified = True

    return render_template(
        'invoices.html',
        customer_name=customer_name,
        invoice_number=invoice_number,
        cart=cart,
        selected_addons=selected_addons,
        total=total,
        flower_subtotal=flower_subtotal,
        addon_subtotal=addon_subtotal,
        discount_applied=discount_applied
    )


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/order_history')
def order_history():

    orders = []

    with sqlite3.connect(
        "flower_shop.db"
    ) as conn:

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM orders"
        )

        rows = cursor.fetchall()

        for row in rows:

            orders.append({

                "order_id": row[0],
                "invoice_number": row[1],
                "customer_name": row[2],
                "items": json.loads(row[3]),
                "addons": json.loads(row[4]),
                "total": row[5],
                "date": row[6]
            })

    return render_template(
        "order_history.html",
        orders=orders
    )


@app.route('/invoices')
def invoices():
    return render_template('invoices.html')

@app.route(
    "/cancel_saved_order/<int:order_id>",
    methods=["POST"]
)
def cancel_saved_order(order_id):

    with sqlite3.connect(
        "flower_shop.db"
    ) as conn:

        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM orders WHERE order_id=?",
            (order_id,)
        )

        conn.commit()

    flash("Order cancelled.")

    return redirect(
        url_for("order_history")
    )


if __name__ == '__main__':

    create_database()

    app.run(debug=True)
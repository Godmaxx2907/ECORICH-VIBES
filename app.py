from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session
)

import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "ecorich_secret_key"
UPLOAD_FOLDER = "static/images/products"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_products():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")

    rows = cursor.fetchall()

    conn.close()

    products = []

    for row in rows:

        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "category": row[3],
            "description": row[4],
            "image": row[5]
        })

    return products


@app.route("/")
def home():

    products = get_products()

    # Choose featured product IDs
    featured_ids = [
        8,13,16,35,38,43,46,47,48,49
    ]

    featured_products = []

    for product in products:
        if product["id"] in featured_ids:
            featured_products.append(product)

    return render_template(
        "index.html",
        products=featured_products
    )

@app.route("/product/<int:id>")
def product_page(id):

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    )

    row = cursor.fetchone()

    conn.close()

    product = {
        "id": row[0],
        "name": row[1],
        "price": row[2],
        "category": row[3],
        "description": row[4],
        "image": row[5]
    }

    return render_template(
        "product.html",
        product=product
    )


@app.route("/category/<category_name>")
def category_page(category_name):

    products = get_products()

    filtered_products = []

    for p in products:

        product_category = (
            str(p["category"])
            .strip()
            .lower()
        )

        current_category = (
            str(category_name)
            .strip()
            .lower()
        )

        if product_category == current_category:
            filtered_products.append(p)

    return render_template(
        "category.html",
        products=filtered_products,
        category=category_name
    )



@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get(
        "admin_logged_in"
    ):
        return redirect(
            "/admin-login"
        )

    if request.method == "POST":

        name = request.form["name"]
        price = request.form["price"]
        category = request.form["category"]
        description = request.form["description"]

        image_file = request.files["image"]

        filename = secure_filename(
            image_file.filename
        )

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        image_file.save(image_path)

        conn = sqlite3.connect(
            "database.db"
        )

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO products
        (
            name,
            price,
            category,
            description,
            image
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            price,
            category,
            description,
            filename
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products"
    )

    rows = cursor.fetchall()

    conn.close()

    products = []

    for row in rows:

        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "category": row[3],
            "description": row[4],
            "image": row[5]
        })

    return render_template(
        "admin.html",
        products=products
    )

@app.route("/add-to-cart/<int:id>")
def add_to_cart(id):

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    id_str = str(id)

    if id_str in cart:
        cart[id_str] += 1
    else:
        cart[id_str] = 1

    session["cart"] = cart
    session.modified = True

    return redirect("/cart")


@app.route("/cart")
def cart():

    cart_items = []
    total = 0

    cart = session.get("cart", {})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    for item_id, quantity in cart.items():

        cursor.execute(
            "SELECT * FROM products WHERE id=?",
            (item_id,)
        )

        row = cursor.fetchone()

        if row:

            # SAFE PRICE CLEANING
            price_text = str(row[2])

            clean_price = ""

            for ch in price_text:
                if ch.isdigit():
                    clean_price += ch

            # avoid crash if empty
            if clean_price == "":
                price_number = 0
            else:
                price_number = int(clean_price)

            subtotal = (
                price_number * quantity
            )

            product = {
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "category": row[3],
                "description": row[4],
                "image": row[5],
                "quantity": quantity,
                "subtotal": subtotal
            }

            cart_items.append(product)

            total += subtotal

    conn.close()

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )

@app.route("/remove-from-cart/<int:id>")
def remove_from_cart(id):

    cart = session.get("cart", [])

    if id in cart:
        cart.remove(id)

    session["cart"] = cart

    return redirect("/cart")



@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = session.get("cart", {})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cart_items = []
    total = 0

    for item_id, quantity in cart.items():

        cursor.execute(
            "SELECT * FROM products WHERE id=?",
            (item_id,)
        )

        row = cursor.fetchone()

        if row:

            # SAFE PRICE CLEANING
            price_text = str(row[2])

            clean_price = ""

            for ch in price_text:
                if ch.isdigit():
                    clean_price += ch

            if clean_price == "":
                 price_number = 0
            else:
                price_number = int(clean_price)
            subtotal = (
                price_number * quantity
            )

            product = {
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "quantity": quantity,
                "subtotal": subtotal
            }

            cart_items.append(product)

            total += subtotal

    conn.close()

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]

        # SAVE ORDER
        products_text = ""

        for item in cart_items:

            products_text += (
                f"{item['name']} | "
                f"Qty: {item['quantity']} | "
                f"Price: {item['price']} | "
                f"Subtotal: ₹{item['subtotal']}, "
            )

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO orders
        (
            customer_name,
            phone,
            address,
            products,
            total,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            phone,
            address,
            products_text,
            str(total),
            "Pending"
        ))

        conn.commit()
        conn.close()

        # WHATSAPP MESSAGE
        message = (
            "Hello, I want to place an order.\n\n"
        )

        message += "Products:\n\n"

        for item in cart_items:

            message += (
                f"- {item['name']}\n"
                f"  Qty: {item['quantity']}\n"
                f"  Price: {item['price']}\n"
                f"  Subtotal: ₹{item['subtotal']}\n\n"
            )

        message += (
            f"Total: ₹{total}\n\n"
            f"Customer Name: {name}\n"
            f"Phone: {phone}\n"
            f"Address: {address}"
        )

        import urllib.parse

        encoded_message = urllib.parse.quote(
            message
        )

        whatsapp_url = (
            "https://wa.me/918806288082"
            f"?text={encoded_message}"
        )

        return redirect(whatsapp_url)

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total
    )
@app.route("/search")
def search():

    query = request.args.get("query", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE name LIKE ?
    OR category LIKE ?
    OR description LIKE ?
    """, (
        f"%{query}%",
        f"%{query}%",
        f"%{query}%"
    ))

    rows = cursor.fetchall()

    conn.close()

    products = []

    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "category": row[3],
            "description": row[4],
            "image": row[5]
        })

    return render_template(
        "search.html",
        products=products,
        query=query
    )
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == "admin"
            and password == "ecorich123"
        ):

            session["admin_logged_in"] = True

            return redirect("/admin")

    return render_template(
        "admin_login.html"
    )


@app.route("/logout")
def logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect("/")

@app.route("/orders")
def orders():

    if not session.get(
        "admin_logged_in"
    ):
        return redirect(
            "/admin-login"
        )

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM orders"
    )

    rows = cursor.fetchall()

    conn.close()

    orders = []

    for row in rows:

        orders.append({
            "id": row[0],
            "customer_name": row[1],
            "phone": row[2],
            "address": row[3],
            "products": row[4],
            "total": row[5],
            "status": row[6]
        })

    return render_template(
        "orders.html",
        orders=orders
    )
    
    
@app.route("/delete-product/<int:id>")
def delete_product(id):

    if not session.get(
        "admin_logged_in"
    ):
        return redirect(
            "/admin-login"
        )

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")  
@app.route(
    "/edit-product/<int:id>",
    methods=["GET", "POST"]
)
def edit_product(id):

    if not session.get(
        "admin_logged_in"
    ):
        return redirect(
            "/admin-login"
        )

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        price = request.form["price"]
        category = request.form["category"]
        description = request.form["description"]

        cursor.execute("""
        UPDATE products
        SET
            name=?,
            price=?,
            category=?,
            description=?
        WHERE id=?
        """, (
            name,
            price,
            category,
            description,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    cursor.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    )

    row = cursor.fetchone()

    conn.close()

    product = {
        "id": row[0],
        "name": row[1],
        "price": row[2],
        "category": row[3],
        "description": row[4],
        "image": row[5]
    }

    return render_template(
        "edit_product.html",
        product=product
    )



@app.route("/products")
def products():

    products = get_products()

    return render_template(
        "products.html",
        products=products
    )


@app.route("/sonalika-implements")
def sonalika_implements():

    return render_template(
        "sonalika.html"
    )

@app.route("/delete-order/<int:id>")
def delete_order(id):

    if not session.get(
        "admin_logged_in"
    ):
        return redirect(
            "/admin-login"
        )

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM orders WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/orders")

@app.route("/increase-quantity/<int:id>")
def increase_quantity(id):

    cart = session.get("cart", {})

    id_str = str(id)

    if id_str in cart:
        cart[id_str] += 1

    session["cart"] = cart

    return redirect("/cart")


@app.route("/decrease-quantity/<int:id>")
def decrease_quantity(id):

    cart = session.get("cart", {})

    id_str = str(id)

    if id_str in cart:

        cart[id_str] -= 1

        if cart[id_str] <= 0:
            del cart[id_str]

    session["cart"] = cart

    return redirect("/cart")


@app.route("/update-order-status/<int:id>/<status>")
def update_order_status(id, status):

    if not session.get(
        "admin_logged_in"
    ):
        return redirect(
            "/admin-login"
        )

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status=?
        WHERE id=?
        """,
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/orders")

@app.route("/fpo-products")
def fpo_products():

    subcategories = [
        "Jay Sardar FPO",
        "GOPADMA FED FPO",
        "A",
        "B",
        "C"
    ]

    return render_template(
        "subcategory.html",
        title="FPO Products",
        subcategories=subcategories
    )


@app.route("/training-consultancy")
def training_consultancy():

    subcategories = [
        "Project",
        "Training",
        "Services"
    ]

    return render_template(
        "subcategory.html",
        title="Training & Consultancy",
        subcategories=subcategories
    )
if __name__ == "__main__":
    app.run(debug=True)


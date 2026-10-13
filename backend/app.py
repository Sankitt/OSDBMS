from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS
from decimal import Decimal
import datetime

app = Flask(__name__)

# Allow frontend to communicate with Flask from any origin
CORS(app, resources={r"/*": {"origins": "*"}})

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sankit8077",
    "database": "ecommerce_db"
}


# =========================================================
# HELPER: GET DATABASE CONNECTION & AUTO INITIALIZE
# =========================================================

def get_db_connection():
    """Connect to MySQL and ensure database and tables exist."""
    try:
        # First try direct connection
        return mysql.connector.connect(**DB_CONFIG)
    except Error as err:
        if err.errno == 1049:  # Unknown database
            # Create database if missing
            temp_conn = mysql.connector.connect(
                host=DB_CONFIG["host"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )
            cursor = temp_conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS ecommerce_db")
            cursor.close()
            temp_conn.close()
            return mysql.connector.connect(**DB_CONFIG)
        else:
            raise err


def init_db():
    """Initialize tables and seed default products if empty."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(100) NOT NULL,
                stock INT DEFAULT 50,
                image VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'Completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Create Order Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
            )
        """)

        conn.commit()

        # Seed products if table is empty
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]

        if count == 0:
            sample_products = [
                ("Wireless Headphones", "High quality wireless headphones", 1799.00, "Electronics", 25, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600"),
                ("Smart Watch", "Modern smartwatch with fitness tracking", 2999.00, "Electronics", 20, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"),
                ("Running Shoes", "Comfortable shoes for everyday running", 2499.00, "Fashion", 30, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600"),
                ("Backpack", "Stylish backpack for college and travel", 1499.00, "Fashion", 40, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"),
                ("Sunglasses", "Trendy sunglasses with UV protection", 999.00, "Accessories", 35, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600"),
                ("Smartphone", "Latest smartphone with powerful performance", 24999.00, "Electronics", 10, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600"),
                ("Desk Lamp", "Modern LED lamp for your study desk", 799.00, "Home", 50, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600"),
                ("Coffee Mug", "Premium ceramic coffee mug", 399.00, "Home", 60, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=600")
            ]

            cursor.executemany("""
                INSERT INTO products (name, description, price, category, stock, image)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, sample_products)

            conn.commit()

        cursor.close()
        conn.close()
        print("Database initialization successful!")
    except Exception as e:
        print("DB Init Warning:", e)


# Run DB initialization on startup
init_db()


# =========================================================
# HOME & HEALTH CHECK
# =========================================================

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "ShopSphere E-Commerce Backend is Running!"
    })


@app.route("/test-db")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, name, email, role, created_at FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format datetime
        for u in users:
            if isinstance(u.get("created_at"), (datetime.date, datetime.datetime)):
                u["created_at"] = u["created_at"].isoformat()

        return jsonify({"success": True, "users": users})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================
# USER REGISTER
# =========================================================

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not name or not email or not password:
            return jsonify({
                "success": False,
                "message": "All fields (name, email, password) are required."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing email
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": "Email is already registered. Please login."
            }), 409

        # Insert new user
        cursor.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, "customer"))

        conn.commit()
        user_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Account created successfully!",
            "user": {
                "id": user_id,
                "user_id": user_id,
                "name": name,
                "email": email,
                "role": "customer"
            }
        }), 201

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# USER LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id AS id, user_id, name, email, password, role, created_at
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        if user["password"] != password:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        # Remove password before returning
        user.pop("password", None)

        if isinstance(user.get("created_at"), (datetime.date, datetime.datetime)):
            user["created_at"] = user["created_at"].isoformat()

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user
        }), 200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# GET USER BY ID
# =========================================================

@app.route("/user/<int:user_id>")
def get_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id AS id, user_id, name, email, role, created_at
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if isinstance(user.get("created_at"), (datetime.date, datetime.datetime)):
            user["created_at"] = user["created_at"].isoformat()

        return jsonify({
            "success": True,
            "user": user
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@app.route("/api/products", methods=["GET"])
@app.route("/products", methods=["GET"])
def get_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT product_id AS id, product_id, name, description, price, category, stock, image
            FROM products
            ORDER BY product_id ASC
        """)

        products = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert Decimal values to float for JSON output
        for p in products:
            if isinstance(p.get("price"), Decimal):
                p["price"] = float(p["price"])

        return jsonify({
            "success": True,
            "products": products
        }), 200

    except Exception as e:
        print("GET PRODUCTS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# PLACE NEW ORDER
# =========================================================

@app.route("/api/orders", methods=["POST"])
@app.route("/orders", methods=["POST"])
def place_order():
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id") or data.get("id")
        total_amount = data.get("total_amount")
        items = data.get("items", [])

        if not user_id or not items or total_amount is None:
            return jsonify({
                "success": False,
                "message": "User ID, total amount, and cart items are required."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Create order record
        cursor.execute("""
            INSERT INTO orders (user_id, total_amount, status)
            VALUES (%s, %s, %s)
        """, (user_id, total_amount, "Completed"))

        order_id = cursor.lastrowid

        # Insert order items & update stock
        for item in items:
            p_id = item.get("id") or item.get("product_id")
            qty = item.get("quantity", 1)
            price = item.get("price", 0)

            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, p_id, qty, price))

            # Reduce product stock
            cursor.execute("""
                UPDATE products
                SET stock = GREATEST(0, stock - %s)
                WHERE product_id = %s
            """, (qty, p_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Order placed successfully!",
            "order_id": order_id
        }), 201

    except Exception as e:
        print("PLACE ORDER ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# GET ORDERS BY USER ID
# =========================================================

@app.route("/api/orders/<int:user_id>", methods=["GET"])
@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT order_id, user_id, total_amount, status, created_at
            FROM orders
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))

        orders = cursor.fetchall()

        for o in orders:
            if isinstance(o.get("total_amount"), Decimal):
                o["total_amount"] = float(o["total_amount"])
            if isinstance(o.get("created_at"), (datetime.date, datetime.datetime)):
                o["created_at"] = o["created_at"].strftime("%b %d, %Y %I:%M %p")

            # Fetch items for this order
            cursor.execute("""
                SELECT oi.item_id, oi.product_id, oi.quantity, oi.price, p.name, p.image
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = %s
            """, (o["order_id"],))

            items = cursor.fetchall()
            for item in items:
                if isinstance(item.get("price"), Decimal):
                    item["price"] = float(item["price"])

            o["items"] = items

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "orders": orders
        }), 200

    except Exception as e:
        print("GET ORDERS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

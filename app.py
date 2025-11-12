import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from sqlalchemy import text
from datetime import datetime
from db import db
from models import User, Product, Order, OrderItem, Transaction, Wishlist

# ----------------------------
# INITIAL SETUP
# ----------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# ----------------------------
# JWT CONFIGURATION
# ----------------------------
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    # jwt_data['sub'] comes as a string from the JWT token
    identity = jwt_data.get("sub")
    try:
        # Convert to integer for database lookup
        user_id = int(identity) if isinstance(identity, str) else identity
        return User.query.get(user_id)
    except Exception as e:
        print("❌ JWT identity parsing error:", repr(e), "jwt_data:", jwt_data)
        return None

# JWT error handler
@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"❌ Invalid token error: {error}")
    return jsonify({'msg': 'Invalid token. Please log in again.'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    print(f"❌ Token expired: {jwt_data}")
    return jsonify({'msg': 'Token has expired. Please log in again.'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"❌ Missing token error: {error}")
    return jsonify({'msg': 'Missing authorization token.'}), 401

# ----------------------------
# DATABASE CONFIG
# ----------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mysql+mysqlconnector://root:%40Database.db1018@127.0.0.1:3306/furniture_haven"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'supersecretkey')

db.init_app(app)

# ----------------------------
# FRONTEND ROUTE
# ----------------------------
@app.route('/')
def home():
    return render_template('index.html')

# ----------------------------
# AUTH: REGISTER
# ----------------------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        for f in ('full_name', 'username', 'email', 'password'):
            if not data.get(f):
                return jsonify({'msg': f'{f} is required'}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'msg': 'Username already exists'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'msg': 'Email already exists'}), 400

        pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(
            full_name=data['full_name'],
            username=data['username'],
            email=data['email'],
            password_hash=pw_hash
        )

        db.session.add(user)
        db.session.commit()
        print(f"✅ Registered: {user.username}")
        return jsonify({'msg': 'Registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        print("❌ Register error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# AUTH: LOGIN - FIXED
# ----------------------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        if not data.get('username') or not data.get('password'):
            return jsonify({'msg': 'Username and password are required'}), 400

        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()

        if user and bcrypt.check_password_hash(user.password_hash, data['password']):
            # Pass user id as string (Flask-JWT-Extended requires 'sub' to be string)
            token = create_access_token(identity=str(user.id))
            return jsonify({
                'msg': 'Login successful',
                'access_token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name
                }
            })
        return jsonify({'msg': 'Invalid credentials'}), 401
    except Exception as e:
        print("❌ Login error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# PRODUCTS (list)
# ----------------------------
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([
            {
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': float(p.price or 0),
                'stock': p.stock,
                'dimensions': p.dimensions,
                'description': p.description,
                'image': p.image,
                'threshold': p.threshold,
                'featured': p.featured,
                'is_new': p.is_new
            } for p in products
        ])
    except Exception as e:
        print("❌ Get products error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# SEED PRODUCTS
# - safe: skips insertion if product with same name exists
# ----------------------------
@app.route('/seed-products', methods=['POST'])
def seed_products():
    try:
        products_data = [
            {"name": "Luxury Sofa", "category": "Living Room", "price": 12999.99, "stock": 10,
             "dimensions": "200x90x100 cm", "description": "A premium luxury sofa with soft cushions.",
             "image": "sofa.png", "threshold": 5, "featured": True, "is_new": True},

            {"name": "Modern Chair", "category": "Living Room", "price": 8999.99, "stock": 20,
             "dimensions": "100x50x50 cm", "description": "A stylish and comfortable chair.",
             "image": "chair.png", "threshold": 5, "featured": False, "is_new": True},

            {"name": "Dining Table Set", "category": "Dining Room", "price": 15999.99, "stock": 5,
             "dimensions": "250x100x75 cm", "description": "Elegant dining set with 6 chairs.",
             "image": "dining.png", "threshold": 5, "featured": True, "is_new": False},

            {"name": "Streamer Chair", "category": "Gaming Chairs", "price": 6800.00, "stock": 15,
             "dimensions": None, "description": "Professional streamer chair with premium features.",
             "image": "streamer-chair.png", "threshold": None, "featured": False, "is_new": False},

            {"name": "Racing Style Chair", "category": "Gaming Chairs", "price": 5200.00, "stock": 20,
             "dimensions": None, "description": "Racing style gaming chair with ergonomic design.",
             "image": "racing-chair.png", "threshold": None, "featured": False, "is_new": False},

            {"name": "Pro Gaming Chair", "category": "Gaming Chairs", "price": 4500.00, "stock": 25,
             "dimensions": None, "description": "Professional gaming chair for esports enthusiasts.",
             "image": "gaming-chair.png", "threshold": None, "featured": True, "is_new": False},
        ]

        inserted = 0
        for p in products_data:
            # Skip if a product with the same name already exists (prevents duplicates)
            existing = Product.query.filter_by(name=p["name"]).first()
            if not existing:
                db.session.add(Product(**p))
                inserted += 1

        db.session.commit()
        return jsonify({"message": f"✅ Seed complete. {inserted} new products added."}), 201

    except Exception as e:
        db.session.rollback()
        print("❌ Seed error:", repr(e))
        return jsonify({"msg": "Server error", "error": str(e)}), 500

# ----------------------------
# CHECKOUT
# ----------------------------
@app.route('/api/checkout', methods=['POST'])
@jwt_required(optional=True)
def checkout():
    try:
        data = request.get_json() or {}
        items = data.get('items', [])
        if not items:
            return jsonify({'msg': 'No items in cart'}), 400

        user_id = get_jwt_identity()

        # validate required shipping/customer fields
        for f in ('full_name', 'email', 'street_address', 'city', 'postal_code', 'country', 'total_amount'):
            if not data.get(f):
                return jsonify({'msg': f'{f} is required'}), 400

        order = Order(
            user_id=user_id,
            full_name=data['full_name'],
            email=data['email'],
            phone=data.get('phone'),
            street_address=data['street_address'],
            city=data['city'],
            postal_code=data['postal_code'],
            country=data['country'],
            total_amount=data['total_amount'],
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        for item in items:
            product = Product.query.get(item.get('product_id'))
            if not product:
                db.session.rollback()
                return jsonify({'msg': f'Product {item.get("product_id")} not found'}), 404
            qty = int(item.get('quantity', 1))
            if product.stock < qty:
                db.session.rollback()
                return jsonify({'msg': f'Not enough stock for {product.name}'}), 400

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                qty=qty,
                price=item.get('unit_price') or float(product.price or 0)
            )
            db.session.add(order_item)

            # update stock
            product.stock -= qty

        db.session.commit()
        return jsonify({'msg': 'Checkout successful', 'order_id': order.id}), 201
    except Exception as e:
        db.session.rollback()
        print("❌ Checkout error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# WISHLIST
# ----------------------------
@app.route('/api/wishlist', methods=['GET'])
@jwt_required()
def get_wishlist():
    try:
        user_id = int(get_jwt_identity())  # normalize to int
        wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
        result = []
        for item in wishlist_items:
            product = Product.query.get(item.product_id)
            if product:
                result.append({
                    'wishlist_id': item.id,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': float(product.price or 0),
                        'image': product.image,
                        'category': product.category
                    }
                })
        return jsonify(result)
    except Exception as e:
        print("❌ Wishlist get error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

@app.route('/api/wishlist', methods=['POST'])
@jwt_required()
def add_to_wishlist():
    try:
        user_id = int(get_jwt_identity())  # normalize to int
        data = request.get_json() or {}
        product_id = data.get('product_id')
        
        print(f"🔄 Adding to wishlist - User: {user_id}, Product: {product_id}")
        
        if not product_id:
            return jsonify({'msg': 'product_id required'}), 400
            
        product = Product.query.get(product_id)
        if not product:
            print(f"❌ Product {product_id} not found")
            return jsonify({'msg': 'Product not found'}), 404

        existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            print("⚠️ Already in wishlist")
            return jsonify({'msg': 'Already in wishlist'}), 400

        new_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        
        print(f"✅ Added to wishlist - ID: {new_item.id}")
        return jsonify({'msg': 'Added to wishlist', 'id': new_item.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print("❌ Wishlist add error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

@app.route('/api/wishlist/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_wishlist(product_id):
    try:
        user_id = int(get_jwt_identity())  # normalize to int
        item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not item:
            return jsonify({'msg': 'Item not found in wishlist'}), 404

        db.session.delete(item)
        db.session.commit()
        return jsonify({'msg': 'Removed from wishlist'})
    except Exception as e:
        db.session.rollback()
        print("❌ Wishlist delete error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# ADDITIONAL WISHLIST ROUTES (for frontend compatibility)
# ----------------------------
@app.route('/api/wishlist/add', methods=['POST'])
@jwt_required()
def add_to_wishlist_alt():
    """Alternative route for frontend calling /api/wishlist/add"""
    try:
        user_id = get_jwt_identity()  # ✅ BAGO: Direct integer na, hindi object
        data = request.get_json() or {}
        product_id = data.get('product_id')
        
        print(f"🔄 Adding to wishlist via /add - User: {user_id}, Product: {product_id}")
        
        if not product_id:
            return jsonify({'msg': 'product_id required'}), 400
            
        product = Product.query.get(product_id)
        if not product:
            print(f"❌ Product {product_id} not found")
            return jsonify({'msg': 'Product not found'}), 404

        existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            print("⚠️ Already in wishlist")
            return jsonify({'msg': 'Already in wishlist'}), 400

        new_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        
        print(f"✅ Added to wishlist via /add - ID: {new_item.id}")
        return jsonify({'msg': 'Added to wishlist', 'id': new_item.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print("❌ Wishlist add error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

@app.route('/api/wishlist/remove/<int:user_id>/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_wishlist_alt(user_id, product_id):
    """Alternative route for frontend calling /api/wishlist/remove/user_id/product_id"""
    try:
        current_user_id = int(get_jwt_identity())  # normalize to int
        
        # Verify the user is removing their own wishlist item
        if current_user_id != user_id:
            return jsonify({'msg': 'Unauthorized'}), 403
            
        item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not item:
            return jsonify({'msg': 'Item not found in wishlist'}), 404

        db.session.delete(item)
        db.session.commit()
        print(f"✅ Removed from wishlist via /remove - User: {user_id}, Product: {product_id}")
        return jsonify({'msg': 'Removed from wishlist'})
    except Exception as e:
        db.session.rollback()
        print("❌ Wishlist delete error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# USER ORDERS
# ----------------------------
@app.route('/api/user/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    try:
        user_id = int(get_jwt_identity())
        orders_q = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

        results = []
        for o in orders_q:
            results.append({
                'id': o.id,
                'total_amount': float(o.total_amount or 0),
                'status': o.status,
                'order_date': o.created_at.strftime('%Y-%m-%d') if o.created_at else None,
                'items': [
                    {
                        'product_id': i.product_id,
                        'qty': i.qty,
                        'price': float(i.price or 0),
                        'product_name': i.product.name if getattr(i, 'product', None) else "Unknown",
                        'image': i.product.image if getattr(i, 'product', None) else None
                    } for i in o.items
                ]
            })

        return jsonify({'orders': results})
    except Exception as e:
        print("❌ Get user orders error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e), 'orders': []}), 500


# ----------------------------
# UPDATE USER PROFILE
# ----------------------------
@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        raw_id = get_jwt_identity()
        try:
            user_id = int(raw_id)
        except Exception:
            # log and return a clear error if subject isn't numeric
            print('❌ Invalid JWT subject type:', repr(raw_id))
            return jsonify({'msg': 'Invalid authentication token (subject must be numeric)'}), 401
        user = User.query.get(user_id)

        if not user:
            return jsonify({'msg': 'User not found'}), 404

        data = request.get_json() or {}

        # Update fields if provided
        if 'full_name' in data and data['full_name']:
            user.full_name = data['full_name']
        if 'email' in data and data['email']:
            existing = User.query.filter(User.id != user_id, User.email == data['email']).first()
            if existing:
                return jsonify({'msg': 'Email already taken'}), 400
            user.email = data['email']
        if 'username' in data and data['username']:
            existing = User.query.filter(User.id != user_id, User.username == data['username']).first()
            if existing:
                return jsonify({'msg': 'Username already taken'}), 400
            user.username = data['username']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']

        user.updated_at = datetime.now()
        db.session.commit()

        print(f"✅ Profile updated for user: {user.username}")
        return jsonify({
            'msg': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'address': user.address
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Update profile error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500


# ----------------------------
# DEV: Add missing user columns (one-shot)
# Restricted to localhost requests and debug mode only.
# ----------------------------
@app.route('/admin/add-user-columns', methods=['POST'])
def add_user_columns():
    if not app.debug:
        return jsonify({'msg': 'Not allowed'}), 403
    if request.remote_addr not in ('127.0.0.1', '::1', 'localhost'):
        return jsonify({'msg': 'Not allowed'}), 403

    try:
        conn = db.engine.connect()
        # use SQLAlchemy text() for compatibility with newer SQLAlchemy versions
        res = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'"))
        rows = res.fetchall()
        existing = {row[0] for row in rows}

        stmts = []
        if 'phone' not in existing:
            stmts.append("ALTER TABLE users ADD COLUMN phone VARCHAR(50) NULL")
        if 'address' not in existing:
            stmts.append("ALTER TABLE users ADD COLUMN address VARCHAR(255) NULL")
        if 'updated_at' not in existing:
            stmts.append("ALTER TABLE users ADD COLUMN updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

        if not stmts:
            conn.close()
            return jsonify({'msg': 'No changes needed', 'added': []})

        for s in stmts:
            conn.execute(text(s))

        conn.close()
        return jsonify({'msg': 'Schema updated', 'added': stmts})
    except Exception as e:
        print('❌ Schema update error:', repr(e))
        return jsonify({'msg': 'Failed to update schema', 'error': str(e)}), 500

# ----------------------------
# TEST DATABASE CONNECTION
# ----------------------------
@app.route('/test-db')
def test_db():
    try:
        db.session.execute('SELECT 1')
        return jsonify({'msg': 'Database connection OK'})
    except Exception as e:
        return jsonify({'msg': 'Database connection failed', 'error': str(e)}), 500

# ----------------------------
# AUTH: CHANGE PASSWORD
# ----------------------------
@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'msg': 'User not found'}), 404
        
        data = request.get_json() or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'msg': 'Current and new password are required'}), 400
        
        # Verify current password
        if not bcrypt.check_password_hash(user.password_hash, current_password):
            return jsonify({'msg': 'Current password is incorrect'}), 401
        
        # Check if new password is different from current
        if bcrypt.check_password_hash(user.password_hash, new_password):
            return jsonify({'msg': 'New password must be different from current password'}), 400
        
        # Update password
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.updated_at = datetime.now()
        db.session.commit()
        
        print(f"✅ Password changed for user: {user.username}")
        return jsonify({'msg': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Change password error:", repr(e))
        return jsonify({'msg': 'Server error', 'error': str(e)}), 500

# ----------------------------
# MAIN ENTRY POINT
# ----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🚀 Server running at http://127.0.0.1:5000")
    app.run(debug=True)
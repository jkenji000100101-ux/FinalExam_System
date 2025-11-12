from app import app, db
from models import User, Product
from flask_bcrypt import generate_password_hash

def setup_database():
    with app.app_context():
        # Drop and create all tables
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin_user = User(
            full_name='Administrator',
            username='admin',
            email='admin@furniturehaven.com',
            password_hash=generate_password_hash('admin123').decode('utf-8'),
            is_admin=True
        )
        db.session.add(admin_user)
        
        # Create sample products
        sample_products = [
            Product(
                name='Modern Wooden Chair',
                category='Chairs',
                price=129.99,
                stock=25,
                dimensions='18" x 20" x 32"',
                description='Comfortable modern wooden chair with ergonomic design.',
                image='/images/chair1.jpg',
                threshold=5,
                featured=True,
                is_new=True
            ),
            Product(
                name='Leather Sofa',
                category='Sofas',
                price=899.99,
                stock=10,
                dimensions='84" x 36" x 32"',
                description='Luxurious 3-seater leather sofa for your living room.',
                image='/images/sofa1.jpg',
                threshold=3,
                featured=True,
                is_new=False
            ),
            Product(
                name='Coffee Table',
                category='Tables',
                price=199.99,
                stock=15,
                dimensions='48" x 24" x 18"',
                description='Elegant coffee table with glass top and wooden legs.',
                image='/images/table1.jpg',
                threshold=5,
                featured=False,
                is_new=True
            ),
            Product(
                name='Bookshelf',
                category='Storage',
                price=299.99,
                stock=8,
                dimensions='36" x 12" x 72"',
                description='Tall bookshelf with 5 shelves for ample storage.',
                image='/images/bookshelf1.jpg',
                threshold=3,
                featured=True,
                is_new=False
            )
        ]
        
        for product in sample_products:
            db.session.add(product)
        
        db.session.commit()
        print("✅ Database setup completed!")
        print("✅ Admin user created - username: 'admin', password: 'admin123'")
        print("✅ Sample products added")

if __name__ == '__main__':
    setup_database()
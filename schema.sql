CREATE DATABASE IF NOT EXISTS furniture_haven CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE furniture_haven;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150),
  username VARCHAR(80) UNIQUE NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_admin TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  price DECIMAL(12,2) DEFAULT 0,
  stock INT DEFAULT 0,
  dimensions VARCHAR(255),
  description TEXT,
  image VARCHAR(512),
  threshold INT DEFAULT 10,
  featured TINYINT(1) DEFAULT 0,
  is_new TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  total_amount DECIMAL(12,2) NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  street_address VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  postal_code VARCHAR(20) NOT NULL,
  country VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  qty INT NOT NULL,
  price DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  type VARCHAR(50) NOT NULL,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  note VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE wishlists (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  UNIQUE KEY unique_wishlist_item (user_id, product_id)
);

-- Insert sample data
INSERT INTO products (name, category, price, stock, dimensions, description, image, featured, is_new) VALUES
('Modern Wooden Chair', 'Chairs', 129.99, 25, '18" x 20" x 32"', 'Comfortable modern wooden chair with ergonomic design.', '/images/chair1.jpg', 1, 1),
('Leather Sofa', 'Sofas', 899.99, 10, '84" x 36" x 32"', 'Luxurious 3-seater leather sofa for your living room.', '/images/sofa1.jpg', 1, 0),
('Coffee Table', 'Tables', 199.99, 15, '48" x 24" x 18"', 'Elegant coffee table with glass top and wooden legs.', '/images/table1.jpg', 0, 1),
('Bookshelf', 'Storage', 299.99, 8, '36" x 12" x 72"', 'Tall bookshelf with 5 shelves for ample storage.', '/images/bookshelf1.jpg', 1, 0);

-- Create admin user (password: admin123)
INSERT INTO users (full_name, username, email, password_hash, is_admin) VALUES
('Administrator', 'admin', 'admin@furniturehaven.com', '$2b$12$LQv3c1yqBNWR1IuH6qQAhOQYxx6cTZ.KY9bK7xHj3K9J2J2y2y2y2', 1);
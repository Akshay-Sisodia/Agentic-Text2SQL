import sqlite3
import os
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize faker
fake = Faker()

# Path to the database
DB_PATH = "sample_huge.db"

# Number of records to generate
NUM_USERS = 10000
NUM_PRODUCTS = 5000
NUM_ORDERS = 50000
NUM_ORDER_ITEMS = 150000
NUM_PRODUCT_CATEGORIES = 50
NUM_SUPPLIERS = 200
NUM_WAREHOUSES = 20
NUM_INVENTORY_ITEMS = 25000
NUM_CUSTOMER_SUPPORT_TICKETS = 15000
NUM_PROMOTIONS = 200

def create_database():
    """Create a new SQLite database with production-like schema and data"""
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # Create tables
    
    # Users table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        date_of_birth DATE,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        country TEXT,
        phone_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        is_admin BOOLEAN DEFAULT FALSE
    )
    ''')
    
    # Product categories
    cursor.execute('''
    CREATE TABLE product_categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        parent_category_id INTEGER NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_category_id) REFERENCES product_categories (id)
    )
    ''')
    
    # Suppliers
    cursor.execute('''
    CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        contact_name TEXT,
        email TEXT,
        phone_number TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        country TEXT,
        tax_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Products
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        sku TEXT UNIQUE,
        category_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        cost DECIMAL(10, 2) NOT NULL,
        weight DECIMAL(8, 2),
        dimensions TEXT,
        in_stock BOOLEAN DEFAULT TRUE,
        rating DECIMAL(3, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES product_categories (id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    )
    ''')
    
    # Warehouses
    cursor.execute('''
    CREATE TABLE warehouses (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        country TEXT,
        capacity INTEGER,
        manager_name TEXT,
        phone_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Inventory
    cursor.execute('''
    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        warehouse_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        min_stock_level INTEGER DEFAULT 10,
        max_stock_level INTEGER DEFAULT 1000,
        reorder_level INTEGER DEFAULT 50,
        last_restock_date TIMESTAMP,
        next_restock_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
        UNIQUE (product_id, warehouse_id)
    )
    ''')
    
    # Orders
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        order_date TIMESTAMP NOT NULL,
        status TEXT NOT NULL,
        total_amount DECIMAL(12, 2) NOT NULL,
        tax_amount DECIMAL(10, 2),
        shipping_amount DECIMAL(8, 2),
        shipping_address TEXT,
        shipping_city TEXT,
        shipping_state TEXT,
        shipping_zip_code TEXT,
        shipping_country TEXT,
        payment_method TEXT,
        tracking_number TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Order items
    cursor.execute('''
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        discount_amount DECIMAL(10, 2) DEFAULT 0,
        total_price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Customer support tickets
    cursor.execute('''
    CREATE TABLE customer_support_tickets (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        order_id INTEGER,
        subject TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        priority TEXT NOT NULL,
        assigned_to INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (assigned_to) REFERENCES users (id)
    )
    ''')
    
    # Promotions
    cursor.execute('''
    CREATE TABLE promotions (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        discount_type TEXT NOT NULL,
        discount_value DECIMAL(10, 2) NOT NULL,
        start_date TIMESTAMP NOT NULL,
        end_date TIMESTAMP NOT NULL,
        minimum_order_amount DECIMAL(10, 2),
        coupon_code TEXT,
        usage_limit INTEGER,
        usage_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Add some indices to improve query performance
    print("Creating indices...")
    cursor.execute("CREATE INDEX idx_products_category ON products (category_id)")
    cursor.execute("CREATE INDEX idx_orders_user ON orders (user_id)")
    cursor.execute("CREATE INDEX idx_order_items_order ON order_items (order_id)")
    cursor.execute("CREATE INDEX idx_order_items_product ON order_items (product_id)")
    cursor.execute("CREATE INDEX idx_inventory_product ON inventory (product_id)")
    cursor.execute("CREATE INDEX idx_tickets_user ON customer_support_tickets (user_id)")
    cursor.execute("CREATE INDEX idx_tickets_order ON customer_support_tickets (order_id)")
    
    conn.commit()
    
    # Generate data
    print("Generating data...")
    
    # Generate users
    print(f"Generating {NUM_USERS} users...")
    for i in range(1, NUM_USERS + 1):
        cursor.execute('''
        INSERT INTO users (
            username, email, password_hash, first_name, last_name, 
            date_of_birth, address, city, state, zip_code, country, 
            phone_number, created_at, last_login, is_active, is_admin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fake.user_name() + str(i),
            f"user{i}@" + fake.free_email_domain(),
            fake.sha256(),
            fake.first_name(),
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d'),
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode(),
            fake.country_code(),
            fake.phone_number(),
            fake.date_time_between(start_date='-3y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
            fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
            random.choice([True, True, True, False]),
            random.random() < 0.03  # 3% chance of admin
        ))
        
        if i % 1000 == 0:
            print(f"  {i} users generated")
            conn.commit()
    
    # Generate product categories
    print(f"Generating {NUM_PRODUCT_CATEGORIES} product categories...")
    categories = []
    
    # First create root categories
    root_categories = min(15, NUM_PRODUCT_CATEGORIES // 3)
    for i in range(1, root_categories + 1):
        name = fake.unique.word().capitalize() + " " + random.choice(["Products", "Items", "Goods", "Collection", "Line"])
        cursor.execute('''
        INSERT INTO product_categories (name, description, parent_category_id)
        VALUES (?, ?, NULL)
        ''', (name, fake.text(max_nb_chars=100),))
        categories.append(name)
    
    # Then create subcategories
    for i in range(root_categories + 1, NUM_PRODUCT_CATEGORIES + 1):
        parent_id = random.randint(1, min(i-1, root_categories))
        name = fake.unique.word().capitalize() + " " + random.choice(["Subcategory", "Class", "Type", "Series", "Group"])
        cursor.execute('''
        INSERT INTO product_categories (name, description, parent_category_id)
        VALUES (?, ?, ?)
        ''', (name, fake.text(max_nb_chars=100), parent_id))
        categories.append(name)
    
    # Generate suppliers
    print(f"Generating {NUM_SUPPLIERS} suppliers...")
    for i in range(1, NUM_SUPPLIERS + 1):
        cursor.execute('''
        INSERT INTO suppliers (
            name, contact_name, email, phone_number, address, 
            city, state, zip_code, country, tax_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fake.company(),
            fake.name(),
            fake.company_email(),
            fake.phone_number(),
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode(),
            fake.country_code(),
            fake.numerify(text="TAX-###-###-###")
        ))
        
        if i % 100 == 0:
            conn.commit()
    
    # Generate products
    print(f"Generating {NUM_PRODUCTS} products...")
    for i in range(1, NUM_PRODUCTS + 1):
        price = round(random.uniform(5.99, 1999.99), 2)
        cost = round(price * random.uniform(0.4, 0.8), 2)
        
        cursor.execute('''
        INSERT INTO products (
            name, description, sku, category_id, supplier_id, 
            price, cost, weight, dimensions, in_stock, rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fake.unique.catch_phrase(),
            fake.text(max_nb_chars=200),
            fake.unique.bothify(text="SKU-????-#####"),
            random.randint(1, NUM_PRODUCT_CATEGORIES),
            random.randint(1, NUM_SUPPLIERS),
            price,
            cost,
            round(random.uniform(0.1, 50), 2),
            f"{random.randint(1, 100)}x{random.randint(1, 100)}x{random.randint(1, 100)}",
            random.random() > 0.1,  # 90% in stock
            round(random.uniform(1, 5), 2) if random.random() > 0.3 else None
        ))
        
        if i % 500 == 0:
            print(f"  {i} products generated")
            conn.commit()
    
    # Generate warehouses
    print(f"Generating {NUM_WAREHOUSES} warehouses...")
    for i in range(1, NUM_WAREHOUSES + 1):
        cursor.execute('''
        INSERT INTO warehouses (
            name, address, city, state, zip_code, country, capacity, manager_name, phone_number
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"Warehouse {fake.city_prefix()}-{i}",
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode(),
            fake.country_code(),
            random.randint(50000, 500000),
            fake.name(),
            fake.phone_number()
        ))
    
    conn.commit()
    
    # Generate inventory
    print(f"Generating {NUM_INVENTORY_ITEMS} inventory items...")
    product_warehouse_pairs = set()
    
    for i in range(1, NUM_INVENTORY_ITEMS + 1):
        # Ensure unique product-warehouse combinations
        while True:
            product_id = random.randint(1, NUM_PRODUCTS)
            warehouse_id = random.randint(1, NUM_WAREHOUSES)
            pair = (product_id, warehouse_id)
            if pair not in product_warehouse_pairs:
                product_warehouse_pairs.add(pair)
                break
        
        quantity = random.randint(0, 500)
        min_level = random.randint(5, 50)
        max_level = random.randint(100, 1000)
        reorder_level = random.randint(min_level, max_level // 2)
        
        last_restock = fake.date_time_between(start_date='-1y', end_date='now')
        next_restock = last_restock + timedelta(days=random.randint(7, 90))
        
        cursor.execute('''
        INSERT INTO inventory (
            product_id, warehouse_id, quantity, min_stock_level, 
            max_stock_level, reorder_level, last_restock_date, next_restock_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            warehouse_id,
            quantity,
            min_level,
            max_level,
            reorder_level,
            last_restock.strftime('%Y-%m-%d %H:%M:%S'),
            next_restock.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        if i % 1000 == 0:
            print(f"  {i} inventory items generated")
            conn.commit()
    
    # Generate orders and order items
    print(f"Generating {NUM_ORDERS} orders and {NUM_ORDER_ITEMS} order items...")
    order_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
    payment_methods = ['Credit Card', 'PayPal', 'Bank Transfer', 'Apple Pay', 'Google Pay', 'Cash on Delivery']
    
    for i in range(1, NUM_ORDERS + 1):
        user_id = random.randint(1, NUM_USERS)
        order_date = fake.date_time_between(start_date='-2y', end_date='now')
        status = random.choice(order_statuses)
        
        # If cancelled or returned, add reason
        notes = None
        if status in ['Cancelled', 'Returned']:
            notes = fake.text(max_nb_chars=100)
        
        # Calculate totals later
        cursor.execute('''
        INSERT INTO orders (
            user_id, order_date, status, total_amount, tax_amount, shipping_amount,
            shipping_address, shipping_city, shipping_state, shipping_zip_code,
            shipping_country, payment_method, tracking_number, notes, created_at
        )
        VALUES (?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            order_date.strftime('%Y-%m-%d %H:%M:%S'),
            status,
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode(),
            fake.country_code(),
            random.choice(payment_methods),
            fake.bothify(text="TRK-????-#####") if status in ['Shipped', 'Delivered'] else None,
            notes,
            order_date.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        order_id = cursor.lastrowid
        
        # Generate order items for this order
        num_items = random.randint(1, 10)  # 1 to 10 items per order
        item_ids = random.sample(range(1, NUM_PRODUCTS), num_items)
        
        total_amount = 0
        for product_id in item_ids:
            # Get product price
            cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            quantity = random.randint(1, 5)
            discount = round(price * random.uniform(0, 0.3), 2) if random.random() < 0.3 else 0
            item_total = round((price - discount) * quantity, 2)
            total_amount += item_total
            
            cursor.execute('''
            INSERT INTO order_items (
                order_id, product_id, quantity, unit_price, 
                discount_amount, total_price
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                order_id,
                product_id,
                quantity,
                price,
                discount,
                item_total
            ))
        
        # Calculate and update order totals
        tax_amount = round(total_amount * random.uniform(0.05, 0.15), 2)
        shipping_amount = round(random.uniform(5.99, 29.99) if total_amount < 100 else 0, 2)
        final_total = total_amount + tax_amount + shipping_amount
        
        cursor.execute('''
        UPDATE orders
        SET total_amount = ?, tax_amount = ?, shipping_amount = ?
        WHERE id = ?
        ''', (final_total, tax_amount, shipping_amount, order_id))
        
        if i % 1000 == 0:
            print(f"  {i} orders generated")
            conn.commit()
    
    # Generate customer support tickets
    print(f"Generating {NUM_CUSTOMER_SUPPORT_TICKETS} customer support tickets...")
    ticket_statuses = ['Open', 'In Progress', 'On Hold', 'Resolved', 'Closed']
    ticket_priorities = ['Low', 'Medium', 'High', 'Urgent']
    ticket_subjects = [
        'Product Damaged', 'Wrong Product', 'Missing Items', 'Shipping Delayed',
        'Return Request', 'Refund Request', 'Product Question', 'Technical Support',
        'Account Access Issue', 'Payment Problem', 'Order Modification', 'General Inquiry'
    ]
    
    for i in range(1, NUM_CUSTOMER_SUPPORT_TICKETS + 1):
        user_id = random.randint(1, NUM_USERS)
        
        # 80% of tickets are related to an order
        order_id = None
        if random.random() < 0.8:
            order_id = random.randint(1, NUM_ORDERS)
        
        status = random.choice(ticket_statuses)
        created_at = fake.date_time_between(start_date='-1y', end_date='now')
        
        resolved_at = None
        if status in ['Resolved', 'Closed']:
            resolved_at = created_at + timedelta(days=random.randint(1, 14))
        
        # Assign ticket to admin if in progress
        assigned_to = None
        if status in ['In Progress', 'On Hold', 'Resolved']:
            cursor.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 20")
            admins = cursor.fetchall()
            if admins:
                assigned_to = random.choice(admins)[0]
        
        cursor.execute('''
        INSERT INTO customer_support_tickets (
            user_id, order_id, subject, description, status,
            priority, assigned_to, created_at, resolved_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            order_id,
            random.choice(ticket_subjects),
            fake.text(max_nb_chars=300),
            status,
            random.choice(ticket_priorities),
            assigned_to,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            resolved_at.strftime('%Y-%m-%d %H:%M:%S') if resolved_at else None
        ))
        
        if i % 1000 == 0:
            print(f"  {i} support tickets generated")
            conn.commit()
    
    # Generate promotions
    print(f"Generating {NUM_PROMOTIONS} promotions...")
    discount_types = ['Percentage', 'Fixed', 'Buy One Get One', 'Free Shipping']
    
    for i in range(1, NUM_PROMOTIONS + 1):
        discount_type = random.choice(discount_types)
        
        # Value depends on type
        if discount_type == 'Percentage':
            discount_value = random.randint(5, 50)
        elif discount_type == 'Fixed':
            discount_value = random.randint(5, 100)
        else:
            discount_value = 0
        
        # Date range
        start_date = fake.date_time_between(start_date='-1y', end_date='+1y')
        end_date = start_date + timedelta(days=random.randint(7, 90))
        
        cursor.execute('''
        INSERT INTO promotions (
            name, description, discount_type, discount_value,
            start_date, end_date, minimum_order_amount,
            coupon_code, usage_limit, usage_count, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"{discount_value}% Off" if discount_type == 'Percentage' else fake.word().upper() + " " + random.choice(["Deal", "Special", "Offer", "Discount", "Sale"]),
            fake.text(max_nb_chars=100),
            discount_type,
            discount_value,
            start_date.strftime('%Y-%m-%d %H:%M:%S'),
            end_date.strftime('%Y-%m-%d %H:%M:%S'),
            round(random.uniform(0, 150), 2) if random.random() < 0.7 else None,
            fake.unique.bothify(text="???###").upper() if random.random() < 0.8 else None,
            random.randint(50, 5000) if random.random() < 0.7 else None,
            random.randint(0, 1000) if random.random() < 0.8 else 0,
            start_date <= datetime.now() <= end_date
        ))
    
    conn.commit()
    
    # Create view for common analytics
    print("Creating useful views...")
    
    # Sales by product view
    cursor.execute('''
    CREATE VIEW sales_by_product AS
    SELECT 
        p.id AS product_id, 
        p.name AS product_name,
        p.category_id,
        pc.name AS category_name,
        COUNT(DISTINCT oi.order_id) AS order_count,
        SUM(oi.quantity) AS quantity_sold,
        SUM(oi.total_price) AS total_revenue,
        AVG(oi.unit_price) AS average_price
    FROM 
        products p
    JOIN 
        order_items oi ON p.id = oi.product_id
    JOIN 
        product_categories pc ON p.category_id = pc.id
    JOIN
        orders o ON oi.order_id = o.id
    WHERE
        o.status != 'Cancelled'
    GROUP BY 
        p.id, p.name, p.category_id, pc.name
    ''')
    
    # User purchase history view
    cursor.execute('''
    CREATE VIEW user_purchase_history AS
    SELECT
        u.id AS user_id,
        u.username,
        u.email,
        COUNT(DISTINCT o.id) AS total_orders,
        SUM(o.total_amount) AS total_spent,
        AVG(o.total_amount) AS average_order_value,
        MAX(o.order_date) AS last_order_date
    FROM
        users u
    LEFT JOIN
        orders o ON u.id = o.user_id
    WHERE
        o.status != 'Cancelled'
    GROUP BY
        u.id, u.username, u.email
    ''')
    
    # Inventory status view
    cursor.execute('''
    CREATE VIEW inventory_status AS
    SELECT
        p.id AS product_id,
        p.name AS product_name,
        p.category_id,
        pc.name AS category_name,
        SUM(i.quantity) AS total_stock,
        COUNT(i.warehouse_id) AS warehouse_count,
        AVG(i.quantity) AS average_per_warehouse,
        SUM(CASE WHEN i.quantity <= i.reorder_level THEN 1 ELSE 0 END) AS low_stock_warehouses
    FROM
        products p
    JOIN
        inventory i ON p.id = i.product_id
    JOIN
        product_categories pc ON p.category_id = pc.id
    GROUP BY
        p.id, p.name, p.category_id, pc.name
    ''')
    
    conn.commit()
    print("Database generation completed!")
    
    # Analyze the database to optimize query planning
    cursor.execute("ANALYZE")
    conn.close()

if __name__ == "__main__":
    create_database() 
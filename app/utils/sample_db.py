"""Utility to set up a sample SQLite database for testing."""

import os
import logging
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, ForeignKey, create_engine, insert

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_sample_database():
    """Create a sample SQLite database for testing."""
    # Make sure we're using SQLite
    if settings.DB_TYPE != 'sqlite':
        logger.warning("This utility is only for SQLite databases. Skipping sample database creation.")
        return
    
    db_path = os.path.join(os.getcwd(), f"{settings.DB_NAME}")
    db_url = f"sqlite:///{db_path}"
    
    # Check if database already exists
    if os.path.exists(db_path):
        logger.info(f"Database already exists at {db_path}")
        return
    
    logger.info(f"Creating sample database at {db_path}")
    
    # Create engine and metadata
    engine = create_engine(db_url, echo=settings.DEBUG)
    metadata = MetaData()
    
    # Define tables
    # Customers table
    customers = Table(
        'customers',
        metadata,
        Column('customer_id', Integer, primary_key=True),
        Column('name', String(100), nullable=False),
        Column('email', String(100)),
        Column('phone', String(20)),
        Column('address', String(200)),
    )
    
    # Products table
    products = Table(
        'products',
        metadata,
        Column('product_id', Integer, primary_key=True),
        Column('name', String(100), nullable=False),
        Column('description', String(500)),
        Column('price', Float, nullable=False),
        Column('category', String(50)),
        Column('stock', Integer, default=0),
    )
    
    # Orders table
    orders = Table(
        'orders',
        metadata,
        Column('order_id', Integer, primary_key=True),
        Column('customer_id', Integer, ForeignKey('customers.customer_id'), nullable=False),
        Column('order_date', String(50), nullable=False),  # Using string for simplicity
        Column('total_amount', Float, nullable=False),
        Column('status', String(20), default='pending'),
    )
    
    # Order items table
    order_items = Table(
        'order_items',
        metadata,
        Column('item_id', Integer, primary_key=True),
        Column('order_id', Integer, ForeignKey('orders.order_id'), nullable=False),
        Column('product_id', Integer, ForeignKey('products.product_id'), nullable=False),
        Column('quantity', Integer, nullable=False),
        Column('unit_price', Float, nullable=False),
    )
    
    # Create tables
    metadata.create_all(engine)
    logger.info("Created database tables")
    
    # Insert sample data
    with engine.connect() as conn:
        # Insert customers
        conn.execute(insert(customers).values([
            {'customer_id': 1, 'name': 'John Smith', 'email': 'john@example.com', 'phone': '555-1234', 'address': '123 Main St'},
            {'customer_id': 2, 'name': 'Jane Doe', 'email': 'jane@example.com', 'phone': '555-5678', 'address': '456 Oak Ave'},
            {'customer_id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'phone': '555-9012', 'address': '789 Pine Rd'},
            {'customer_id': 4, 'name': 'Alice Brown', 'email': 'alice@example.com', 'phone': '555-3456', 'address': '321 Elm St'},
            {'customer_id': 5, 'name': 'Charlie Davis', 'email': 'charlie@example.com', 'phone': '555-7890', 'address': '654 Maple Dr'},
        ]))
        
        # Insert products
        conn.execute(insert(products).values([
            {'product_id': 1, 'name': 'Laptop', 'description': 'High-performance laptop', 'price': 999.99, 'category': 'Electronics', 'stock': 10},
            {'product_id': 2, 'name': 'Smartphone', 'description': 'Latest smartphone model', 'price': 699.99, 'category': 'Electronics', 'stock': 15},
            {'product_id': 3, 'name': 'Headphones', 'description': 'Noise-cancelling headphones', 'price': 149.99, 'category': 'Audio', 'stock': 20},
            {'product_id': 4, 'name': 'Tablet', 'description': '10-inch tablet', 'price': 399.99, 'category': 'Electronics', 'stock': 8},
            {'product_id': 5, 'name': 'Smartwatch', 'description': 'Fitness tracking smartwatch', 'price': 249.99, 'category': 'Wearables', 'stock': 12},
            {'product_id': 6, 'name': 'Wireless Mouse', 'description': 'Ergonomic wireless mouse', 'price': 29.99, 'category': 'Accessories', 'stock': 30},
            {'product_id': 7, 'name': 'Keyboard', 'description': 'Mechanical keyboard', 'price': 79.99, 'category': 'Accessories', 'stock': 25},
            {'product_id': 8, 'name': 'Monitor', 'description': '27-inch 4K monitor', 'price': 349.99, 'category': 'Electronics', 'stock': 5},
        ]))
        
        # Insert orders
        conn.execute(insert(orders).values([
            {'order_id': 1, 'customer_id': 1, 'order_date': '2023-01-15', 'total_amount': 1149.98, 'status': 'completed'},
            {'order_id': 2, 'customer_id': 2, 'order_date': '2023-01-20', 'total_amount': 699.99, 'status': 'completed'},
            {'order_id': 3, 'customer_id': 3, 'order_date': '2023-02-05', 'total_amount': 429.98, 'status': 'shipped'},
            {'order_id': 4, 'customer_id': 1, 'order_date': '2023-02-10', 'total_amount': 249.99, 'status': 'pending'},
            {'order_id': 5, 'customer_id': 4, 'order_date': '2023-02-15', 'total_amount': 1099.97, 'status': 'shipped'},
            {'order_id': 6, 'customer_id': 5, 'order_date': '2023-03-01', 'total_amount': 349.99, 'status': 'pending'},
        ]))
        
        # Insert order items
        conn.execute(insert(order_items).values([
            {'item_id': 1, 'order_id': 1, 'product_id': 1, 'quantity': 1, 'unit_price': 999.99},
            {'item_id': 2, 'order_id': 1, 'product_id': 3, 'quantity': 1, 'unit_price': 149.99},
            {'item_id': 3, 'order_id': 2, 'product_id': 2, 'quantity': 1, 'unit_price': 699.99},
            {'item_id': 4, 'order_id': 3, 'product_id': 6, 'quantity': 1, 'unit_price': 29.99},
            {'item_id': 5, 'order_id': 3, 'product_id': 7, 'quantity': 5, 'unit_price': 79.99},
            {'item_id': 6, 'order_id': 4, 'product_id': 5, 'quantity': 1, 'unit_price': 249.99},
            {'item_id': 7, 'order_id': 5, 'product_id': 4, 'quantity': 1, 'unit_price': 399.99},
            {'item_id': 8, 'order_id': 5, 'product_id': 2, 'quantity': 1, 'unit_price': 699.99},
            {'item_id': 9, 'order_id': 6, 'product_id': 8, 'quantity': 1, 'unit_price': 349.99},
        ]))
        
        conn.commit()
    
    logger.info("Inserted sample data")
    logger.info(f"Sample database created at {db_path}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create sample database
    create_sample_database() 
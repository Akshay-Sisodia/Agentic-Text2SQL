"""Utility to set up a sample Oracle database for testing."""

import logging
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, ForeignKey, create_engine, insert, text

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_sample_oracle_database():
    """Create a sample Oracle database for testing."""
    # Make sure we're using Oracle
    if settings.DB_TYPE != 'oracle':
        logger.warning("This utility is only for Oracle databases. Skipping sample database creation.")
        return
    
    # Create engine and metadata
    connection_str = f"oracle+cx_oracle://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    
    try:
        engine = create_engine(connection_str, echo=settings.DEBUG)
        metadata = MetaData()
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
            logger.info(f"Successfully connected to Oracle database: {settings.DB_NAME}")
            
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
            Column('customer_id', Integer, ForeignKey('customers.customer_id')),
            Column('order_date', String(50)),  # Using string for simplicity
            Column('total_amount', Float, nullable=False),
            Column('status', String(20)),
        )
        
        # Order items table
        order_items = Table(
            'order_items',
            metadata,
            Column('item_id', Integer, primary_key=True),
            Column('order_id', Integer, ForeignKey('orders.order_id')),
            Column('product_id', Integer, ForeignKey('products.product_id')),
            Column('quantity', Integer, nullable=False),
            Column('price', Float, nullable=False),
        )
        
        # Drop tables if they exist
        with engine.connect() as conn:
            for table_name in ['order_items', 'orders', 'products', 'customers']:
                try:
                    conn.execute(text(f"DROP TABLE {table_name} PURGE"))
                except Exception:
                    # Table doesn't exist, continue
                    pass
        
        # Create tables
        metadata.create_all(engine)
        logger.info("Created sample tables in Oracle database")
        
        # Create sequences for primary keys
        with engine.connect() as conn:
            for seq_name, table_name in [
                ('customers_seq', 'customers'),
                ('products_seq', 'products'),
                ('orders_seq', 'orders'),
                ('order_items_seq', 'order_items')
            ]:
                try:
                    conn.execute(text(f"DROP SEQUENCE {seq_name}"))
                except Exception:
                    pass
                conn.execute(text(f"CREATE SEQUENCE {seq_name} START WITH 1 INCREMENT BY 1"))
                
        # Sample data
        with engine.begin() as conn:
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
                {'product_id': 2, 'name': 'Smartphone', 'description': 'Latest model smartphone', 'price': 699.99, 'category': 'Electronics', 'stock': 15},
                {'product_id': 3, 'name': 'Headphones', 'description': 'Noise-cancelling headphones', 'price': 149.99, 'category': 'Electronics', 'stock': 20},
                {'product_id': 4, 'name': 'Desk Chair', 'description': 'Ergonomic office chair', 'price': 199.99, 'category': 'Furniture', 'stock': 5},
                {'product_id': 5, 'name': 'Coffee Table', 'description': 'Modern coffee table', 'price': 149.99, 'category': 'Furniture', 'stock': 8},
                {'product_id': 6, 'name': 'Bookshelf', 'description': 'Wooden bookshelf', 'price': 89.99, 'category': 'Furniture', 'stock': 12},
                {'product_id': 7, 'name': 'Blender', 'description': 'High-speed blender', 'price': 79.99, 'category': 'Appliances', 'stock': 7},
                {'product_id': 8, 'name': 'Toaster', 'description': '4-slice toaster', 'price': 49.99, 'category': 'Appliances', 'stock': 9},
            ]))
            
            # Insert orders
            conn.execute(insert(orders).values([
                {'order_id': 1, 'customer_id': 1, 'order_date': '2023-01-15', 'total_amount': 1149.98, 'status': 'Delivered'},
                {'order_id': 2, 'customer_id': 2, 'order_date': '2023-02-20', 'total_amount': 699.99, 'status': 'Delivered'},
                {'order_id': 3, 'customer_id': 3, 'order_date': '2023-03-25', 'total_amount': 249.98, 'status': 'Shipped'},
                {'order_id': 4, 'customer_id': 4, 'order_date': '2023-04-05', 'total_amount': 149.99, 'status': 'Processing'},
                {'order_id': 5, 'customer_id': 5, 'order_date': '2023-04-10', 'total_amount': 129.98, 'status': 'Processing'},
                {'order_id': 6, 'customer_id': 1, 'order_date': '2023-04-15', 'total_amount': 89.99, 'status': 'Pending'},
            ]))
            
            # Insert order items
            conn.execute(insert(order_items).values([
                {'item_id': 1, 'order_id': 1, 'product_id': 1, 'quantity': 1, 'price': 999.99},
                {'item_id': 2, 'order_id': 1, 'product_id': 3, 'quantity': 1, 'price': 149.99},
                {'item_id': 3, 'order_id': 2, 'product_id': 2, 'quantity': 1, 'price': 699.99},
                {'item_id': 4, 'order_id': 3, 'product_id': 4, 'quantity': 1, 'price': 199.99},
                {'item_id': 5, 'order_id': 3, 'product_id': 8, 'quantity': 1, 'price': 49.99},
                {'item_id': 6, 'order_id': 4, 'product_id': 3, 'quantity': 1, 'price': 149.99},
                {'item_id': 7, 'order_id': 5, 'product_id': 7, 'quantity': 1, 'price': 79.99},
                {'item_id': 8, 'order_id': 5, 'product_id': 8, 'quantity': 1, 'price': 49.99},
                {'item_id': 9, 'order_id': 6, 'product_id': 6, 'quantity': 1, 'price': 89.99},
            ]))
            
        logger.info("Inserted sample data into Oracle database")
        
    except Exception as e:
        logger.error(f"Error creating sample Oracle database: {str(e)}")
        raise 
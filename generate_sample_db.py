import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

DB_FILE = 'sample_huge.db'
NUM_USERS = 10000
NUM_PRODUCTS = 2000
NUM_CATEGORIES = 50
NUM_ORDERS = 100000
NUM_REVIEWS = 30000
NUM_ADDRESSES = 15000
NUM_PAYMENTS = 100000

fake = Faker()


def create_schema(conn):
    c = conn.cursor()
    c.executescript('''
    DROP TABLE IF EXISTS reviews;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS payments;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS addresses;
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS categories;

    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        address_line TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        postal_code TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        address_id INTEGER,
        order_date TEXT,
        status TEXT,
        total REAL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (address_id) REFERENCES addresses(id)
    );

    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        payment_date TEXT,
        amount REAL,
        payment_method TEXT,
        status TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );

    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        rating INTEGER,
        review_text TEXT,
        review_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    ''')
    conn.commit()


def populate_categories(conn):
    c = conn.cursor()
    categories = [(fake.word().capitalize() + str(i), fake.sentence()) for i in range(NUM_CATEGORIES)]
    c.executemany('INSERT INTO categories (name, description) VALUES (?, ?)', categories)
    conn.commit()


def populate_products(conn):
    c = conn.cursor()
    products = []
    for _ in range(NUM_PRODUCTS):
        name = fake.word().capitalize() + ' ' + fake.word().capitalize() + ' ' + str(random.randint(1, 99999))
        description = fake.sentence()
        price = round(random.uniform(5, 500), 2)
        category_id = random.randint(1, NUM_CATEGORIES)
        products.append((name, description, price, category_id))
    c.executemany('INSERT INTO products (name, description, price, category_id) VALUES (?, ?, ?, ?)', products)
    conn.commit()


def populate_users(conn):
    c = conn.cursor()
    users = []
    for _ in range(NUM_USERS):
        name = fake.name()
        email = fake.unique.email()
        phone = fake.phone_number()
        created_at = fake.date_time_between(start_date='-5y', end_date='now').isoformat()
        users.append((name, email, phone, created_at))
    c.executemany('INSERT INTO users (name, email, phone, created_at) VALUES (?, ?, ?, ?)', users)
    conn.commit()


def populate_addresses(conn):
    c = conn.cursor()
    addresses = []
    for _ in range(NUM_ADDRESSES):
        user_id = random.randint(1, NUM_USERS)
        address_line = fake.street_address()
        city = fake.city()
        state = fake.state()
        country = fake.country()
        postal_code = fake.postcode()
        addresses.append((user_id, address_line, city, state, country, postal_code))
    c.executemany('INSERT INTO addresses (user_id, address_line, city, state, country, postal_code) VALUES (?, ?, ?, ?, ?, ?)', addresses)
    conn.commit()


def populate_orders(conn):
    c = conn.cursor()
    orders = []
    for _ in range(NUM_ORDERS):
        user_id = random.randint(1, NUM_USERS)
        address_id = random.randint(1, NUM_ADDRESSES)
        order_date = fake.date_time_between(start_date='-3y', end_date='now').isoformat()
        status = random.choice(['pending', 'shipped', 'delivered', 'cancelled'])
        total = round(random.uniform(20, 2000), 2)
        orders.append((user_id, address_id, order_date, status, total))
    c.executemany('INSERT INTO orders (user_id, address_id, order_date, status, total) VALUES (?, ?, ?, ?, ?)', orders)
    conn.commit()


def populate_order_items(conn):
    c = conn.cursor()
    order_items = []
    for order_id in range(1, NUM_ORDERS + 1):
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            product_id = random.randint(1, NUM_PRODUCTS)
            quantity = random.randint(1, 10)
            price = round(random.uniform(5, 500), 2)
            order_items.append((order_id, product_id, quantity, price))
        if order_id % 1000 == 0:
            c.executemany('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', order_items)
            order_items = []
    if order_items:
        c.executemany('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', order_items)
    conn.commit()


def populate_payments(conn):
    c = conn.cursor()
    payments = []
    for order_id in range(1, NUM_ORDERS + 1):
        payment_date = fake.date_time_between(start_date='-3y', end_date='now').isoformat()
        amount = round(random.uniform(20, 2000), 2)
        payment_method = random.choice(['credit_card', 'paypal', 'bank_transfer', 'cash_on_delivery'])
        status = random.choice(['completed', 'pending', 'failed'])
        payments.append((order_id, payment_date, amount, payment_method, status))
        if order_id % 1000 == 0:
            c.executemany('INSERT INTO payments (order_id, payment_date, amount, payment_method, status) VALUES (?, ?, ?, ?, ?)', payments)
            payments = []
    if payments:
        c.executemany('INSERT INTO payments (order_id, payment_date, amount, payment_method, status) VALUES (?, ?, ?, ?, ?)', payments)
    conn.commit()


def populate_reviews(conn):
    c = conn.cursor()
    reviews = []
    for _ in range(NUM_REVIEWS):
        user_id = random.randint(1, NUM_USERS)
        product_id = random.randint(1, NUM_PRODUCTS)
        rating = random.randint(1, 5)
        review_text = fake.sentence()
        review_date = fake.date_time_between(start_date='-3y', end_date='now').isoformat()
        reviews.append((user_id, product_id, rating, review_text, review_date))
        if len(reviews) % 1000 == 0:
            c.executemany('INSERT INTO reviews (user_id, product_id, rating, review_text, review_date) VALUES (?, ?, ?, ?, ?)', reviews)
            reviews = []
    if reviews:
        c.executemany('INSERT INTO reviews (user_id, product_id, rating, review_text, review_date) VALUES (?, ?, ?, ?, ?)', reviews)
    conn.commit()


def main():
    print('Creating database schema...')
    conn = sqlite3.connect(DB_FILE)
    create_schema(conn)

    print('Populating categories...')
    populate_categories(conn)
    print('Populating products...')
    populate_products(conn)
    print('Populating users...')
    populate_users(conn)
    print('Populating addresses...')
    populate_addresses(conn)
    print('Populating orders...')
    populate_orders(conn)
    print('Populating order items...')
    populate_order_items(conn)
    print('Populating payments...')
    populate_payments(conn)
    print('Populating reviews...')
    populate_reviews(conn)
    conn.close()
    print(f'Database {DB_FILE} created and populated successfully!')


if __name__ == '__main__':
    main() 
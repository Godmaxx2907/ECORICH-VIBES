import sqlite3


def create_database():

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    # PRODUCTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        price TEXT NOT NULL,

        category TEXT NOT NULL,

        description TEXT NOT NULL,

        image TEXT NOT NULL
    )
    """)

    # ORDERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_name TEXT NOT NULL,

        phone TEXT NOT NULL,

        address TEXT NOT NULL,

        products TEXT NOT NULL,

        total TEXT NOT NULL,

        status TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


create_database()
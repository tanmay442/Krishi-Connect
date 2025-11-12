import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Successfully connected to SQLite database: {db_file}")
        # Enable foreign key constraint enforcement
        conn.execute("PRAGMA foreign_keys = 1")
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def main():
    # Specify the full path to your database file here
    database = "Backend/app/database.db"

    # SQL statement for creating the 'users' table
    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        tag text NOT NULL CHECK(tag IN ('farmer', 'buyer')),
                                        email text NOT NULL UNIQUE,
                                        contact_number text NOT NULL,
                                        name text NOT NULL,
                                        state text NOT NULL,
                                        record_creation_datetime text DEFAULT CURRENT_TIMESTAMP
                                    ); """

    # SQL statement for creating the 'transactions' table
    sql_create_transactions_table = """CREATE TABLE IF NOT EXISTS transactions (
                                            transaction_id integer PRIMARY KEY AUTOINCREMENT,
                                            item_name text NOT NULL,
                                            item_quantity real NOT NULL,
                                            quoted_price real NOT NULL,
                                            transaction_state text NOT NULL CHECK(transaction_state IN ('initiated', 'completed', 'cancelled')),
                                            transaction_start_datetime text DEFAULT CURRENT_TIMESTAMP,
                                            farmer_id integer NOT NULL,
                                            buyer_id integer NOT NULL,
                                            FOREIGN KEY (farmer_id) REFERENCES users (id),
                                            FOREIGN KEY (buyer_id) REFERENCES users (id)
                                        );"""


    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create users table
        create_table(conn, sql_create_users_table)
        print("'users' table created successfully.")

        # create transactions table
        create_table(conn, sql_create_transactions_table)
        print("'transactions' table created successfully.")
        
        conn.close()
        print("The SQLite connection is closed.")
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
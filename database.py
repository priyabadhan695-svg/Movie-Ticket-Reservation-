# database.py
import sqlite3
import hashlib
from config import APP_CONFIG

class Database:
    def __init__(self, db_name=None):
        if db_name is None:
            db_name = APP_CONFIG['db_name']
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.alter_tables()
        self.insert_default_admin()

    def create_tables(self):
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        
        # Movies table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT,
                duration INTEGER,
                rating REAL,
                description TEXT
            )
        ''')
        
        # Shows table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                total_seats INTEGER NOT NULL,
                available_seats INTEGER NOT NULL,
                price REAL DEFAULT 10.0,
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
        ''')
        
        # Bookings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                show_id INTEGER NOT NULL,
                seats_booked TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                total_price REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (show_id) REFERENCES shows (id)
            )
        ''')
        self.conn.commit()

    def alter_tables(self):
        # Add price column to shows if not exists
        self.cursor.execute("PRAGMA table_info(shows)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'price' not in columns:
            self.cursor.execute("ALTER TABLE shows ADD COLUMN price REAL DEFAULT 10.0")

        # Add booking_deadline column to shows if not exists.
        # Stores "YYYY-MM-DD HH:MM:SS". After this moment the show can no
        # longer be booked, even if seats remain. NULL means no time limit.
        self.cursor.execute("PRAGMA table_info(shows)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'booking_deadline' not in columns:
            self.cursor.execute("ALTER TABLE shows ADD COLUMN booking_deadline TEXT")
        
        # Add total_price to bookings if not exists
        self.cursor.execute("PRAGMA table_info(bookings)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'total_price' not in columns:
            self.cursor.execute("ALTER TABLE bookings ADD COLUMN total_price REAL DEFAULT 0.0")
        self.conn.commit()

    def insert_default_admin(self):
        self.cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not self.cursor.fetchone():
            hashed = hashlib.sha256("admin".encode()).hexdigest()
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                              ("admin", hashed, "admin"))
            self.conn.commit()

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
# models.py
from database import Database
import datetime

def now_str():
    """Current timestamp formatted the same way booking_deadline is stored."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Movie:
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        return self.db.fetch_all("SELECT * FROM movies ORDER BY title")
    
    def get_by_id(self, movie_id):
        return self.db.fetch_one("SELECT * FROM movies WHERE id=?", (movie_id,))
    
    def add(self, title, genre, duration, rating, description):
        return self.db.execute_query(
            "INSERT INTO movies (title, genre, duration, rating, description) VALUES (?, ?, ?, ?, ?)",
            (title, genre, duration, rating, description)
        )

    def delete(self, movie_id):
        """Delete a movie along with every show for it and every booking
        made against those shows (cascading delete)."""
        show_ids = [row[0] for row in self.db.fetch_all(
            "SELECT id FROM shows WHERE movie_id=?", (movie_id,))]
        for show_id in show_ids:
            self.db.execute_query("DELETE FROM bookings WHERE show_id=?", (show_id,))
        self.db.execute_query("DELETE FROM shows WHERE movie_id=?", (movie_id,))
        return self.db.execute_query("DELETE FROM movies WHERE id=?", (movie_id,))

    def count_shows(self, movie_id):
        row = self.db.fetch_one("SELECT COUNT(*) FROM shows WHERE movie_id=?", (movie_id,))
        return row[0] if row else 0
    
    def get_with_shows(self):
        return self.db.fetch_all('''
            SELECT movies.title, movies.genre, movies.duration, movies.rating,
                   shows.date, shows.time, shows.available_seats, shows.price
            FROM shows
            JOIN movies ON shows.movie_id = movies.id
            WHERE shows.available_seats > 0
              AND (shows.booking_deadline IS NULL OR shows.booking_deadline > ?)
            ORDER BY shows.date, shows.time
        ''', (now_str(),))

class Show:
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        """All shows for the admin list, including their booking deadline
        (if any) so the UI can show a live countdown / Expired status."""
        return self.db.fetch_all('''
            SELECT shows.id, movies.title, shows.date, shows.time,
                   shows.total_seats, shows.available_seats, shows.price,
                   shows.booking_deadline
            FROM shows JOIN movies ON shows.movie_id = movies.id
            ORDER BY shows.date, shows.time
        ''')
    
    def get_available(self):
        """Shows that still have seats AND whose booking window (if any)
        has not expired yet. Once the timer runs out, a show automatically
        drops out of this list and can no longer be booked."""
        return self.db.fetch_all('''
            SELECT shows.id, movies.title, shows.date, shows.time, 
                   shows.available_seats, shows.price, shows.booking_deadline
            FROM shows
            JOIN movies ON shows.movie_id = movies.id
            WHERE shows.available_seats > 0
              AND (shows.booking_deadline IS NULL OR shows.booking_deadline > ?)
            ORDER BY shows.date, shows.time
        ''', (now_str(),))
    
    def add(self, movie_id, date, time, total_seats, price, duration_minutes=None):
        """Create a show. If duration_minutes is given (and > 0), booking
        for this show automatically closes duration_minutes from now."""
        deadline = None
        if duration_minutes:
            deadline = (datetime.datetime.now() +
                        datetime.timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        return self.db.execute_query(
            "INSERT INTO shows (movie_id, date, time, total_seats, available_seats, price, booking_deadline) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (movie_id, date, time, total_seats, total_seats, price, deadline)
        )
    
    def update_seats(self, show_id, new_available):
        return self.db.execute_query(
            "UPDATE shows SET available_seats=? WHERE id=?",
            (new_available, show_id)
        )
    
    def get_by_id(self, show_id):
        return self.db.fetch_one("SELECT * FROM shows WHERE id=?", (show_id,))

    def is_booking_open(self, show_id):
        """True if the show still has seats and its booking timer (if any)
        has not expired."""
        row = self.db.fetch_one(
            "SELECT available_seats, booking_deadline FROM shows WHERE id=?", (show_id,))
        if not row:
            return False
        available_seats, deadline = row
        if available_seats <= 0:
            return False
        if deadline and deadline <= now_str():
            return False
        return True

    def delete(self, show_id):
        """Delete a show along with every booking made for it (cascading
        delete). Unlike cancelling a single booking, deleting a show does
        not need to restore seats since the show itself is gone."""
        self.db.execute_query("DELETE FROM bookings WHERE show_id=?", (show_id,))
        return self.db.execute_query("DELETE FROM shows WHERE id=?", (show_id,))

    def count_bookings(self, show_id):
        row = self.db.fetch_one("SELECT COUNT(*) FROM bookings WHERE show_id=?", (show_id,))
        return row[0] if row else 0

class Booking:
    def __init__(self, db):
        self.db = db
    
    def create(self, user_id, show_id, seats_booked, total_price):
        booking_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.db.execute_query(
            "INSERT INTO bookings (user_id, show_id, seats_booked, booking_time, total_price) VALUES (?, ?, ?, ?, ?)",
            (user_id, show_id, seats_booked, booking_time, total_price)
        )
    
    def get_user_bookings(self, user_id):
        return self.db.fetch_all('''
            SELECT bookings.id, movies.title, shows.date, shows.time, 
                   bookings.seats_booked, bookings.total_price, bookings.booking_time
            FROM bookings
            JOIN shows ON bookings.show_id = shows.id
            JOIN movies ON shows.movie_id = movies.id
            WHERE bookings.user_id = ?
            ORDER BY bookings.booking_time DESC
        ''', (user_id,))
    
    def get_all_bookings(self):
        return self.db.fetch_all('''
            SELECT bookings.id, users.username, movies.title, shows.date, shows.time,
                   bookings.seats_booked, bookings.total_price, bookings.booking_time
            FROM bookings
            JOIN users ON bookings.user_id = users.id
            JOIN shows ON bookings.show_id = shows.id
            JOIN movies ON shows.movie_id = movies.id
            ORDER BY bookings.booking_time DESC
        ''')
    
    def delete(self, booking_id):
        booking = self.db.fetch_one("SELECT show_id, seats_booked FROM bookings WHERE id=?", (booking_id,))
        if booking:
            show_id, seats_str = booking
            seats_count = len(seats_str.split(','))
            self.db.execute_query("UPDATE shows SET available_seats = available_seats + ? WHERE id=?", 
                                (seats_count, show_id))
        return self.db.execute_query("DELETE FROM bookings WHERE id=?", (booking_id,))
    
    def delete_all(self):
        bookings = self.db.fetch_all("SELECT show_id, seats_booked FROM bookings")
        for show_id, seats_str in bookings:
            seats_count = len(seats_str.split(','))
            self.db.execute_query("UPDATE shows SET available_seats = available_seats + ? WHERE id=?", 
                                (seats_count, show_id))
        return self.db.execute_query("DELETE FROM bookings")

class User:
    def __init__(self, db):
        self.db = db
    
    def authenticate(self, username, password):
        import hashlib
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self.db.fetch_one(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, hashed)
        )
    
    def create(self, username, password):
        import hashlib
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self.db.execute_query(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed, "user")
        )
    
    def user_exists(self, username):
        return self.db.fetch_one("SELECT id FROM users WHERE username=?", (username,))
import os, sqlite3, hashlib, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "movie_reservation_web.db"))

def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        g.db = sqlite3.connect(DB_PATH, timeout=20)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre TEXT,
        duration INTEGER,
        rating REAL,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS shows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        total_seats INTEGER NOT NULL,
        available_seats INTEGER NOT NULL,
        price REAL DEFAULT 10.0,
        booking_deadline TEXT,
        FOREIGN KEY(movie_id) REFERENCES movies(id)
    );
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        show_id INTEGER NOT NULL,
        seats_booked TEXT NOT NULL,
        booking_time TEXT NOT NULL,
        total_price REAL DEFAULT 0.0,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(show_id) REFERENCES shows(id)
    );
    """)
    # Match the original desktop project's built-in admin account.
    existing = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        db.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                   ("admin", hash_password("admin"), "admin"))
    db.commit()
    db.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required.", "danger")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper

def now_text():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.route("/")
def home():
    db = get_db()
    shows = db.execute("""
        SELECT s.id, m.title, m.genre, m.duration, m.rating, s.date, s.time,
               s.available_seats, s.price, s.booking_deadline
        FROM shows s JOIN movies m ON m.id=s.movie_id
        WHERE s.available_seats > 0
          AND (s.booking_deadline IS NULL OR s.booking_deadline > ?)
        ORDER BY s.date, s.time
    """, (now_text(),)).fetchall()
    return render_template("home.html", shows=shows)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm", "").strip()
        if not username or not password:
            flash("Username and password cannot be empty.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
        else:
            db = get_db()
            try:
                db.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                           (username, hash_password(password), "user"))
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username already exists.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = get_db().execute(
            "SELECT id,username,role FROM users WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()
        if user:
            session.clear()
            session.update(user_id=user["id"], username=user["username"], role=user["role"])
            flash("Welcome, " + user["username"] + "!", "success")
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "home"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/book/<int:show_id>", methods=["POST"])
@login_required
def book(show_id):
    try:
        seats = int(request.form.get("seats", "0"))
        if seats <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid positive number of seats.", "danger")
        return redirect(url_for("home"))
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        show = db.execute("""
            SELECT s.*, m.title FROM shows s JOIN movies m ON m.id=s.movie_id
            WHERE s.id=?
        """, (show_id,)).fetchone()
        if not show:
            raise ValueError("This show no longer exists.")
        if show["available_seats"] < seats:
            raise ValueError("Only {} seats are available.".format(show["available_seats"]))
        if show["booking_deadline"] and show["booking_deadline"] <= now_text():
            raise ValueError("The booking window for this show has closed.")
        subtotal = seats * float(show["price"])
        tax = subtotal * 0.10
        discount = subtotal * 0.05 if seats >= 5 else 0
        total = subtotal + tax - discount
        first = show["available_seats"] - seats + 1
        seat_list = ",".join(str(n) for n in range(first, first + seats))
        db.execute("INSERT INTO bookings(user_id,show_id,seats_booked,booking_time,total_price) VALUES(?,?,?,?,?)",
                   (session["user_id"], show_id, seat_list, now_text(), total))
        db.execute("UPDATE shows SET available_seats=available_seats-? WHERE id=?", (seats, show_id))
        db.commit()
        flash("Booking confirmed for {}. Total: ${:.2f} (includes 10% tax and any eligible discount).".format(show["title"], total), "success")
    except (ValueError, sqlite3.Error) as exc:
        db.rollback()
        flash(str(exc) or "Booking could not be completed.", "danger")
    return redirect(url_for("my_bookings"))

@app.route("/my-bookings")
@login_required
def my_bookings():
    rows = get_db().execute("""
        SELECT b.id, m.title, s.date, s.time, b.seats_booked,
               b.total_price, b.booking_time
        FROM bookings b JOIN shows s ON s.id=b.show_id
        JOIN movies m ON m.id=s.movie_id
        WHERE b.user_id=? ORDER BY b.booking_time DESC
    """, (session["user_id"],)).fetchall()
    return render_template("my_bookings.html", bookings=rows)

@app.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT show_id,seats_booked FROM bookings WHERE id=? AND user_id=?",
                         (booking_id, session["user_id"])).fetchone()
        if not row:
            raise ValueError("Booking not found.")
        count = len(row["seats_booked"].split(","))
        db.execute("UPDATE shows SET available_seats=available_seats+? WHERE id=?", (count, row["show_id"]))
        db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        db.commit()
        flash("Booking cancelled and seats restored.", "success")
    except (ValueError, sqlite3.Error) as exc:
        db.rollback()
        flash(str(exc), "danger")
    return redirect(url_for("my_bookings"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    movies = db.execute("SELECT * FROM movies ORDER BY title").fetchall()
    shows = db.execute("""
        SELECT s.*,m.title FROM shows s JOIN movies m ON m.id=s.movie_id
        ORDER BY s.date,s.time
    """).fetchall()
    bookings = db.execute("""
        SELECT b.id,u.username,m.title,s.date,s.time,b.seats_booked,b.total_price,b.booking_time
        FROM bookings b JOIN users u ON u.id=b.user_id
        JOIN shows s ON s.id=b.show_id JOIN movies m ON m.id=s.movie_id
        ORDER BY b.booking_time DESC
    """).fetchall()
    return render_template("admin.html", movies=movies, shows=shows, bookings=bookings)

@app.route("/admin/movie/add", methods=["POST"])
@admin_required
def add_movie():
    title = request.form.get("title", "").strip()
    genre = request.form.get("genre", "").strip()
    description = request.form.get("description", "").strip()
    try:
        duration = int(request.form.get("duration", "0"))
        rating_text = request.form.get("rating", "").strip()
        rating = float(rating_text) if rating_text else None
        if not title or duration <= 0 or (rating is not None and not 0 <= rating <= 10):
            raise ValueError
    except ValueError:
        flash("Enter a title, positive duration and rating between 0 and 10.", "danger")
        return redirect(url_for("admin_dashboard"))
    db = get_db()
    db.execute("INSERT INTO movies(title,genre,duration,rating,description) VALUES(?,?,?,?,?)",
               (title, genre, duration, rating, description))
    db.commit()
    flash("Movie added.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/movie/delete/<int:movie_id>", methods=["POST"])
@admin_required
def delete_movie(movie_id):
    db = get_db()
    db.execute("DELETE FROM bookings WHERE show_id IN (SELECT id FROM shows WHERE movie_id=?)", (movie_id,))
    db.execute("DELETE FROM shows WHERE movie_id=?", (movie_id,))
    db.execute("DELETE FROM movies WHERE id=?", (movie_id,))
    db.commit()
    flash("Movie and its shows/bookings deleted.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/show/add", methods=["POST"])
@admin_required
def add_show():
    db = get_db()
    try:
        movie_id = int(request.form.get("movie_id", "0"))
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()
        total_seats = int(request.form.get("total_seats", "0"))
        price = float(request.form.get("price", "0"))
        duration_text = request.form.get("duration_minutes", "").strip()
        duration_minutes = int(duration_text) if duration_text else None
        datetime.datetime.strptime(date, "%Y-%m-%d")
        datetime.datetime.strptime(time, "%H:%M")
        if total_seats <= 0 or price < 0 or (duration_minutes is not None and duration_minutes <= 0):
            raise ValueError
        if not db.execute("SELECT id FROM movies WHERE id=?", (movie_id,)).fetchone():
            raise ValueError
    except ValueError:
        flash("Check movie, date (YYYY-MM-DD), time (HH:MM), seats, price and optional timer.", "danger")
        return redirect(url_for("admin_dashboard"))
    deadline = None
    if duration_minutes:
        deadline = (datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""INSERT INTO shows(movie_id,date,time,total_seats,available_seats,price,booking_deadline)
                  VALUES(?,?,?,?,?,?,?)""",
               (movie_id, date, time, total_seats, total_seats, price, deadline))
    db.commit()
    flash("Show added successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/show/delete/<int:show_id>", methods=["POST"])
@admin_required
def delete_show(show_id):
    db = get_db()
    db.execute("DELETE FROM bookings WHERE show_id=?", (show_id,))
    db.execute("DELETE FROM shows WHERE id=?", (show_id,))
    db.commit()
    flash("Show and its bookings deleted.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/booking/delete/<int:booking_id>", methods=["POST"])
@admin_required
def admin_delete_booking(booking_id):
    db = get_db()
    row = db.execute("SELECT show_id,seats_booked FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if row:
        db.execute("UPDATE shows SET available_seats=available_seats+? WHERE id=?",
                   (len(row["seats_booked"].split(",")), row["show_id"]))
        db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        db.commit()
        flash("Booking deleted and seats restored.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/bookings/clear", methods=["POST"])
@admin_required
def clear_bookings():
    db = get_db()
    rows = db.execute("SELECT show_id,seats_booked FROM bookings").fetchall()
    for row in rows:
        db.execute("UPDATE shows SET available_seats=available_seats+? WHERE id=?",
                   (len(row["seats_booked"].split(",")), row["show_id"]))
    db.execute("DELETE FROM bookings")
    db.commit()
    flash("All bookings cleared and seats restored.", "info")
    return redirect(url_for("admin_dashboard"))

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

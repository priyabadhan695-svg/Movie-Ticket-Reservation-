# admin_panel.py
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONT
from utils import (create_styled_button, validate_date, validate_time,
                    validate_price, validate_duration, format_time_left)

class AdminPanel:
    def __init__(self, parent, db, current_user):
        self.parent = parent
        self.db = db
        self.current_user = current_user
        self.content_frame = None
        self.admin_booking_tree = None
        self.movie_tree = None
        self.show_tree = None
        self._shows_refresh_job = None
        
    def show(self):
        """Display admin panel"""
        self.clear_window()
        self.parent.configure(bg=COLORS['dark'])
        
        main_frame = tk.Frame(self.parent, bg=COLORS['dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        sidebar = tk.Frame(main_frame, bg=COLORS['dark'], width=230)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        sidebar.pack_propagate(False)
        
        tk.Label(sidebar, text="🔧 Admin", font=('Helvetica', 20, 'bold'),
                bg=COLORS['dark'], fg=COLORS['light']).pack(pady=(15, 25))
        
        # Sidebar buttons
        buttons = [
            ("➕ Add Movie", self.add_movie),
            ("📽️ View Movies", self.view_movies),
            ("🕒 Add Show", self.add_show),
            ("📅 View Shows", self.view_shows),
            ("📋 View Bookings", self.view_bookings),
            ("🚪 Logout", self.logout)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(sidebar, text=text, command=cmd,
                          font=FONT['normal'], bg=COLORS['darker'], fg='white',
                          relief=tk.FLAT, bd=0, anchor='w', padx=15, pady=12,
                          activebackground=COLORS['primary'], activeforeground='white',
                          width=22, justify=tk.LEFT)
            btn.pack(pady=4, fill=tk.X)
        
        # Content frame
        self.content_frame = tk.Frame(main_frame, bg=COLORS['light'], bd=0)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Welcome message
        welcome = tk.Label(self.content_frame, 
                          text=f"Welcome Admin: {self.current_user['username']}",
                          font=('Helvetica', 22), bg=COLORS['light'], fg=COLORS['dark'])
        welcome.pack(pady=40)
        tk.Label(self.content_frame, 
                text="Use the sidebar to manage movies, shows, and bookings.",
                font=FONT['normal'], bg=COLORS['light'], fg='#7f8c8d').pack()
    
    def clear_content(self):
        """Clear content frame"""
        if self._shows_refresh_job is not None:
            try:
                self.parent.after_cancel(self._shows_refresh_job)
            except Exception:
                pass
            self._shows_refresh_job = None
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()
    
    def clear_window(self):
        """Clear all widgets"""
        for widget in self.parent.winfo_children():
            widget.destroy()
    
    def logout(self):
        """Logout and return to login"""
        self.auth.logout()
    def on_login_success(self, user):
        """Callback when login succeeds"""
        self.current_user = user
        if user['role'] == 'admin':
            self.show()
        else:
            from user_panel import UserPanel
            user_panel = UserPanel(self.parent, self.db, user)
            user_panel.show()
    
    def add_movie(self):
        """Add movie form"""
        self.clear_content()
        frame = tk.Frame(self.content_frame, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        tk.Label(frame, text="Add New Movie", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).grid(row=0, column=0, columnspan=2, pady=15)
        
        fields = [
            ("Title", "title_entry"),
            ("Genre", "genre_entry"),
            ("Duration (min)", "duration_entry"),
            ("Rating (0-10)", "rating_entry"),
            ("Description", "desc_entry")
        ]
        
        entries = {}
        for i, (label, attr) in enumerate(fields, start=1):
            tk.Label(frame, text=label, font=FONT['normal'],
                    bg=COLORS['light'], fg=COLORS['dark']).grid(row=i, column=0, sticky='w', pady=8)
            
            if label == "Description":
                entry = tk.Text(frame, height=5, width=40, font=FONT['normal'],
                              bg='white', relief=tk.FLAT, bd=0,
                              highlightthickness=1, highlightcolor=COLORS['primary'])
                entry.grid(row=i, column=1, pady=8, padx=15)
            else:
                entry = tk.Entry(frame, font=FONT['normal'], width=40,
                               bg='white', relief=tk.FLAT, bd=0,
                               highlightthickness=1, highlightcolor=COLORS['primary'])
                entry.grid(row=i, column=1, pady=8, padx=15)
            entries[attr] = entry
        
        def submit():
            title = entries['title_entry'].get().strip()
            genre = entries['genre_entry'].get().strip()
            duration_str = entries['duration_entry'].get().strip()
            rating_str = entries['rating_entry'].get().strip()
            description = entries['desc_entry'].get("1.0", tk.END).strip()
            
            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            if not duration_str.isdigit() or int(duration_str) <= 0:
                messagebox.showerror("Error", "Duration must be a positive integer")
                return
            try:
                rating = float(rating_str) if rating_str else None
                if rating is not None and (rating < 0 or rating > 10):
                    raise ValueError
            except:
                messagebox.showerror("Error", "Rating must be a number between 0 and 10")
                return
            
            self.db.execute_query(
                "INSERT INTO movies (title, genre, duration, rating, description) VALUES (?, ?, ?, ?, ?)",
                (title, genre, int(duration_str), rating, description)
            )
            messagebox.showinfo("Success", "Movie added successfully!")
            self.view_movies()
        
        btn = tk.Button(frame, text="Add Movie", command=submit, font=('Segoe UI', 13, 'bold'),
                       bg=COLORS['primary'], fg='white', relief=tk.FLAT, padx=25, pady=10,
                       activebackground=COLORS['primary_dark'], activeforeground='white')
        btn.grid(row=len(fields)+1, column=0, columnspan=2, pady=25)
    
    def view_movies(self):
        """View all movies"""
        self.clear_content()
        frame = tk.Frame(self.content_frame, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="All Movies", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).pack(pady=10)

        toolbar = tk.Frame(frame, bg=COLORS['light'])
        toolbar.pack(fill=tk.X, pady=5)

        def make_tool_btn(text, cmd, color, hover):
            btn = tk.Button(toolbar, text=text, command=cmd, font=FONT['normal'],
                          bg=color, fg='white', relief=tk.FLAT, padx=15, pady=5,
                          activebackground=hover, activeforeground='white')
            btn.pack(side=tk.LEFT, padx=5)
            return btn

        make_tool_btn("🗑️ Delete Selected", self.delete_movie, COLORS['danger'], COLORS['danger_dark'])
        make_tool_btn("🔄 Refresh", self.view_movies, COLORS['primary'], COLORS['primary_dark'])
        
        tree_frame = tk.Frame(frame, bg=COLORS['light'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Title", "Genre", "Duration", "Rating", "Description")
        self.movie_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.movie_tree.heading(col, text=col)
            self.movie_tree.column(col, width=100 if col != "Description" else 250)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.movie_tree.yview)
        self.movie_tree.configure(yscrollcommand=scroll.set)
        self.movie_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        movies = self.db.fetch_all("SELECT * FROM movies")
        for i, movie in enumerate(movies):
            tag = 'even' if i % 2 == 0 else 'odd'
            self.movie_tree.insert("", tk.END, iid=str(movie[0]), values=movie, tags=(tag,))
        self.movie_tree.tag_configure('even', background=COLORS['even_row'])
        self.movie_tree.tag_configure('odd', background=COLORS['odd_row'])

    def delete_movie(self):
        """Delete the selected movie, cascading to its shows and bookings"""
        if not self.movie_tree:
            return
        selected = self.movie_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a movie to delete.")
            return
        movie_id = int(selected[0])
        movie = self.db.fetch_one("SELECT title FROM movies WHERE id=?", (movie_id,))
        title = movie[0] if movie else f"ID {movie_id}"

        from models import Movie
        movie_model = Movie(self.db)
        show_count = movie_model.count_shows(movie_id)

        warning = f"Delete movie '{title}'?"
        if show_count > 0:
            warning += (f"\n\nThis will also delete {show_count} show(s) for this movie "
                        f"and every booking made against them. This cannot be undone.")
        confirm = messagebox.askyesno("Confirm Delete", warning)
        if confirm:
            movie_model.delete(movie_id)
            messagebox.showinfo("Success", f"'{title}' and its shows/bookings were deleted.")
            self.view_movies()
    
    def add_show(self):
        """Add show form"""
        self.clear_content()
        frame = tk.Frame(self.content_frame, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        tk.Label(frame, text="Add New Show", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).grid(row=0, column=0, columnspan=2, pady=15)
        
        movies = self.db.fetch_all("SELECT id, title FROM movies")
        movie_options = {f"{m[1]} (ID:{m[0]})": m[0] for m in movies}
        if not movie_options:
            tk.Label(frame, text="No movies available. Please add a movie first.", 
                    font=FONT['normal'], bg=COLORS['light'], fg=COLORS['danger']).grid(row=1, column=0, columnspan=2, pady=10)
            return
        
        tk.Label(frame, text="Movie", font=FONT['normal'],
                bg=COLORS['light'], fg=COLORS['dark']).grid(row=1, column=0, sticky='w', pady=8)
        movie_var = tk.StringVar()
        movie_combo = ttk.Combobox(frame, textvariable=movie_var, 
                                 values=list(movie_options.keys()), width=38, font=FONT['normal'])
        movie_combo.grid(row=1, column=1, pady=8, padx=15)
        movie_combo.current(0)
        
        fields = [
            ("Date (YYYY-MM-DD)", "date_entry"),
            ("Time (HH:MM)", "time_entry"),
            ("Total Seats", "seats_entry"),
            ("Price per Ticket ($)", "price_entry"),
            ("Booking Available For (minutes, blank = no limit)", "duration_entry"),
        ]
        
        entries = {}
        for i, (label, attr) in enumerate(fields, start=2):
            tk.Label(frame, text=label, font=FONT['normal'],
                    bg=COLORS['light'], fg=COLORS['dark']).grid(row=i, column=0, sticky='w', pady=8)
            entry = tk.Entry(frame, font=FONT['normal'], width=40,
                           bg='white', relief=tk.FLAT, bd=0,
                           highlightthickness=1, highlightcolor=COLORS['primary'])
            entry.grid(row=i, column=1, pady=8, padx=15)
            if label == "Price per Ticket ($)":
                entry.insert(0, "10.0")
            entries[attr] = entry

        tk.Label(frame, text="Once the timer runs out, the show automatically stops\naccepting new bookings — even if seats are still free.",
                font=FONT['small'], bg=COLORS['light'], fg='#7f8c8d', justify='left'
                ).grid(row=len(fields)+2, column=0, columnspan=2, sticky='w', pady=(0, 5))
        
        def submit():
            movie_selected = movie_var.get()
            if not movie_selected:
                messagebox.showerror("Error", "Select a movie")
                return
            movie_id = movie_options[movie_selected]
            date = entries['date_entry'].get().strip()
            time = entries['time_entry'].get().strip()
            seats_str = entries['seats_entry'].get().strip()
            price_str = entries['price_entry'].get().strip()
            
            if not validate_date(date):
                messagebox.showerror("Error", "Enter date in YYYY-MM-DD format")
                return
            if not validate_time(time):
                messagebox.showerror("Error", "Enter time in HH:MM format")
                return
            if not seats_str.isdigit() or int(seats_str) <= 0:
                messagebox.showerror("Error", "Total seats must be a positive integer")
                return
            if not validate_price(price_str):
                messagebox.showerror("Error", "Price must be a non-negative number")
                return
            duration_str = entries['duration_entry'].get().strip()
            if not validate_duration(duration_str):
                messagebox.showerror("Error", "Booking timer must be a positive whole number of minutes, or left blank")
                return
            
            total = int(seats_str)
            price = float(price_str)
            duration_minutes = int(duration_str) if duration_str else None

            from models import Show
            show_model = Show(self.db)
            show_model.add(movie_id, date, time, total, price, duration_minutes)

            if duration_minutes:
                messagebox.showinfo("Success", f"Show added! Booking closes automatically in {duration_minutes} minute(s).")
            else:
                messagebox.showinfo("Success", "Show added successfully!")
            self.view_shows()
        
        btn = tk.Button(frame, text="Add Show", command=submit, font=('Segoe UI', 13, 'bold'),
                       bg=COLORS['primary'], fg='white', relief=tk.FLAT, padx=25, pady=10,
                       activebackground=COLORS['primary_dark'], activeforeground='white')
        btn.grid(row=len(fields)+3, column=0, columnspan=2, pady=25)
    
    def view_shows(self):
        """View all shows"""
        self.clear_content()
        frame = tk.Frame(self.content_frame, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="All Shows", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).pack(pady=10)

        toolbar = tk.Frame(frame, bg=COLORS['light'])
        toolbar.pack(fill=tk.X, pady=5)

        def make_tool_btn(text, cmd, color, hover):
            btn = tk.Button(toolbar, text=text, command=cmd, font=FONT['normal'],
                          bg=color, fg='white', relief=tk.FLAT, padx=15, pady=5,
                          activebackground=hover, activeforeground='white')
            btn.pack(side=tk.LEFT, padx=5)
            return btn

        make_tool_btn("🗑️ Delete Selected", self.delete_show, COLORS['danger'], COLORS['danger_dark'])
        make_tool_btn("🔄 Refresh", self.view_shows, COLORS['primary'], COLORS['primary_dark'])
        
        tree_frame = tk.Frame(frame, bg=COLORS['light'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Show ID", "Movie", "Date", "Time", "Total Seats", "Available", "Price ($)", "Booking Status")
        self.show_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.show_tree.heading(col, text=col)
            self.show_tree.column(col, width=100 if col not in ("Movie", "Booking Status") else 150)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.show_tree.yview)
        self.show_tree.configure(yscrollcommand=scroll.set)
        self.show_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_shows_tree()

    def refresh_shows_tree(self):
        """Reload the shows tree and reschedule itself so the 'time left'
        countdown and Expired status stay live without manual refresh."""
        if not self.show_tree or not self.show_tree.winfo_exists():
            self._shows_refresh_job = None
            return

        selected = self.show_tree.selection()
        for item in self.show_tree.get_children():
            self.show_tree.delete(item)

        from models import Show
        show_model = Show(self.db)
        shows = show_model.get_all()
        for i, show in enumerate(shows):
            show_id, title, date, time, total, available, price, deadline = show
            status = format_time_left(deadline)
            if status == "Expired" or available <= 0:
                tag = 'closed'
            else:
                tag = 'even' if i % 2 == 0 else 'odd'
            values = (show_id, title, date, time, total, available, f"{price:.2f}", status)
            self.show_tree.insert("", tk.END, iid=str(show_id), values=values, tags=(tag,))
        self.show_tree.tag_configure('even', background=COLORS['even_row'])
        self.show_tree.tag_configure('odd', background=COLORS['odd_row'])
        self.show_tree.tag_configure('closed', background='#f5d5d0')
        if selected:
            try:
                self.show_tree.selection_set(selected)
            except Exception:
                pass

        self._shows_refresh_job = self.parent.after(5000, self.refresh_shows_tree)

    def delete_show(self):
        """Delete the selected show, cascading to its bookings"""
        if not self.show_tree:
            return
        selected = self.show_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a show to delete.")
            return
        show_id = int(selected[0])
        show = self.db.fetch_one('''
            SELECT movies.title, shows.date, shows.time FROM shows
            JOIN movies ON shows.movie_id = movies.id WHERE shows.id=?
        ''', (show_id,))
        label = f"{show[0]} ({show[1]} {show[2]})" if show else f"ID {show_id}"

        from models import Show
        show_model = Show(self.db)
        booking_count = show_model.count_bookings(show_id)

        warning = f"Delete show '{label}'?"
        if booking_count > 0:
            warning += (f"\n\nThis will also delete {booking_count} existing booking(s) for "
                        f"this show. This cannot be undone.")
        confirm = messagebox.askyesno("Confirm Delete", warning)
        if confirm:
            show_model.delete(show_id)
            messagebox.showinfo("Success", f"'{label}' and its bookings were deleted.")
            self.view_shows()
    
    def view_bookings(self):
        """View all bookings (admin)"""
        self.clear_content()
        frame = tk.Frame(self.content_frame, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="All Bookings", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).pack(pady=10)
        
        toolbar = tk.Frame(frame, bg=COLORS['light'])
        toolbar.pack(fill=tk.X, pady=5)
        
        def make_tool_btn(text, cmd, color, hover):
            btn = tk.Button(toolbar, text=text, command=cmd, font=FONT['normal'],
                          bg=color, fg='white', relief=tk.FLAT, padx=15, pady=5,
                          activebackground=hover, activeforeground='white')
            btn.pack(side=tk.LEFT, padx=5)
            return btn
        
        make_tool_btn("🗑️ Delete Selected", self.delete_booking, COLORS['danger'], COLORS['danger_dark'])
        make_tool_btn("🧹 Clear All", self.clear_all_bookings, COLORS['warning'], COLORS['warning_dark'])
        make_tool_btn("🔄 Refresh", self.refresh_bookings, COLORS['primary'], COLORS['primary_dark'])
        
        tree_frame = tk.Frame(frame, bg=COLORS['light'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Booking ID", "User", "Movie", "Date", "Time", "Seats", "Total Price", "Booking Time")
        self.admin_booking_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.admin_booking_tree.heading(col, text=col)
            self.admin_booking_tree.column(col, width=100)
        self.admin_booking_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.admin_booking_tree.yview)
        self.admin_booking_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_bookings()
    
    def refresh_bookings(self):
        """Refresh admin bookings view"""
        if not hasattr(self, 'admin_booking_tree') or not self.admin_booking_tree:
            return
            
        for item in self.admin_booking_tree.get_children():
            self.admin_booking_tree.delete(item)
        
        bookings = self.db.fetch_all('''
            SELECT bookings.id, users.username, movies.title, shows.date, shows.time,
                   bookings.seats_booked, bookings.total_price, bookings.booking_time
            FROM bookings
            JOIN users ON bookings.user_id = users.id
            JOIN shows ON bookings.show_id = shows.id
            JOIN movies ON shows.movie_id = movies.id
            ORDER BY bookings.booking_time DESC
        ''')
        for i, b in enumerate(bookings):
            values = list(b)
            values[6] = f"${values[6]:.2f}"
            tag = 'even' if i % 2 == 0 else 'odd'
            self.admin_booking_tree.insert("", tk.END, iid=str(b[0]), values=values, tags=(tag,))
        self.admin_booking_tree.tag_configure('even', background=COLORS['even_row'])
        self.admin_booking_tree.tag_configure('odd', background=COLORS['odd_row'])
    
    def delete_booking(self):
        """Delete selected booking"""
        if not hasattr(self, 'admin_booking_tree'):
            return
        selected = self.admin_booking_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a booking to delete.")
            return
        booking_id = int(selected[0])
        confirm = messagebox.askyesno("Confirm Delete", f"Delete booking ID {booking_id}? Seats will be restored.")
        if confirm:
            from models import Booking
            booking_model = Booking(self.db)
            booking_model.delete(booking_id)
            messagebox.showinfo("Success", "Booking deleted and seats restored.")
            self.refresh_bookings()
    
    def clear_all_bookings(self):
        """Clear all bookings"""
        confirm = messagebox.askyesno("Confirm Clear All", "Delete ALL bookings? Seats will be restored.")
        if confirm:
            from models import Booking
            booking_model = Booking(self.db)
            booking_model.delete_all()
            messagebox.showinfo("Success", "All bookings cleared and seats restored.")
            self.refresh_bookings()
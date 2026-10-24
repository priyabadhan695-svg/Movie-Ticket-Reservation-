# user_panel.py
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONT
from utils import create_styled_button, generate_bill, format_time_left
from models import Show, Booking
import datetime

class UserPanel:
    def __init__(self, parent, db, current_user):
        self.parent = parent
        self.db = db
        self.current_user = current_user
        self.user_booking_tree = None
        self.movies_tree = None
        self.show_model = Show(db)
        self.booking_model = Booking(db)
        self._movies_refresh_job = None
        self._book_refresh_job = None
        
    def show(self):
        """Display user panel"""
        self.clear_window()
        self.parent.configure(bg=COLORS['dark'])
        
        main_frame = tk.Frame(self.parent, bg=COLORS['dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar
        top_bar = tk.Canvas(main_frame, height=80, bg=COLORS['darker'], highlightthickness=0)
        top_bar.pack(fill=tk.X)
        
        top_bar.create_text(30, 40, text="🎬 Movie Reservation", font=('Helvetica', 22, 'bold'), 
                          fill='white', anchor='w')
        top_bar.create_text(920, 40, text=f"👤 {self.current_user['username']}", 
                          font=FONT['normal'], fill='white', anchor='e')
        
        logout_btn = tk.Button(main_frame, text="Logout", command=self.logout,
                             font=FONT['normal'], bg=COLORS['danger'], fg='white',
                             relief=tk.FLAT, padx=15, pady=5, 
                             activebackground=COLORS['danger_dark'], activeforeground='white')
        top_bar.create_window(1000, 40, window=logout_btn, anchor='e')
        
        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Movies tab
        self.tab_movies = tk.Frame(self.notebook, bg=COLORS['light'])
        self.notebook.add(self.tab_movies, text="📽️ Movies & Shows")
        self.populate_movies_tab()
        
        # Book tab
        self.tab_book = tk.Frame(self.notebook, bg=COLORS['light'])
        self.notebook.add(self.tab_book, text="🎫 Book Tickets")
        self.populate_book_tab()
        
        # My bookings tab
        self.tab_bookings = tk.Frame(self.notebook, bg=COLORS['light'])
        self.notebook.add(self.tab_bookings, text="📋 My Bookings")
        self.populate_my_bookings()
    
    def clear_window(self):
        """Clear all widgets"""
        for widget in self.parent.winfo_children():
            widget.destroy()
    
    def logout(self):
        """Logout and return to login"""
        for job_attr in ('_movies_refresh_job', '_book_refresh_job'):
            job = getattr(self, job_attr, None)
            if job is not None:
                try:
                    self.parent.after_cancel(job)
                except Exception:
                    pass
                setattr(self, job_attr, None)
        self.auth.logout()
    
    def populate_movies_tab(self):
        """Populate movies and shows tab"""
        frame = tk.Frame(self.tab_movies, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frame, text="🎞️ Now Showing", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).pack(pady=10)
        
        tree_frame = tk.Frame(frame, bg=COLORS['light'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Movie", "Genre", "Duration", "Rating", "Date", "Time", "Available", "Price ($)", "Booking Window")
        self.movies_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.movies_tree.heading(col, text=col)
            self.movies_tree.column(col, width=100 if col not in ("Movie", "Booking Window") else 160)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.movies_tree.yview)
        self.movies_tree.configure(yscrollcommand=scroll.set)
        self.movies_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_movies_tree()

    def refresh_movies_tree(self):
        """Reload the 'Now Showing' list — shows whose booking timer has run
        out drop off automatically — and reschedule the next refresh."""
        if not self.movies_tree or not self.movies_tree.winfo_exists():
            self._movies_refresh_job = None
            return

        for item in self.movies_tree.get_children():
            self.movies_tree.delete(item)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shows = self.db.fetch_all('''
            SELECT movies.title, movies.genre, movies.duration, movies.rating,
                   shows.date, shows.time, shows.available_seats, shows.price,
                   shows.booking_deadline
            FROM shows
            JOIN movies ON shows.movie_id = movies.id
            WHERE shows.available_seats > 0
              AND (shows.booking_deadline IS NULL OR shows.booking_deadline > ?)
            ORDER BY shows.date, shows.time
        ''', (now,))
        for i, show in enumerate(shows):
            values = list(show)
            values[7] = f"${values[7]:.2f}"
            values[8] = format_time_left(values[8])
            tag = 'even' if i % 2 == 0 else 'odd'
            self.movies_tree.insert("", tk.END, values=values, tags=(tag,))
        self.movies_tree.tag_configure('even', background=COLORS['even_row'])
        self.movies_tree.tag_configure('odd', background=COLORS['odd_row'])

        self._movies_refresh_job = self.parent.after(5000, self.refresh_movies_tree)
    
    def populate_book_tab(self):
        """Populate booking tab"""
        frame = tk.Frame(self.tab_book, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        tk.Label(frame, text="🎫 Book Tickets", font=('Helvetica', 26, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).grid(row=0, column=0, columnspan=2, pady=15)
        
        tk.Label(frame, text="Select Show", font=FONT['heading'],
                bg=COLORS['light'], fg=COLORS['dark']).grid(row=1, column=0, sticky='w', pady=10)
        self.show_var = tk.StringVar()
        self.show_combo = ttk.Combobox(frame, textvariable=self.show_var, width=55, font=FONT['normal'])
        self.show_combo.grid(row=1, column=1, pady=10, padx=15)
        
        def refresh_shows():
            if not self.show_combo.winfo_exists():
                self._book_refresh_job = None
                return
            shows = self.show_model.get_available()
            options = []
            for s in shows:
                show_id, title, date, time, available, price, deadline = s
                time_left = format_time_left(deadline)
                suffix = f" [{time_left}]" if deadline else ""
                options.append(f"{title} - {date} {time} (Seats: {available}) - ${price:.2f}/ticket{suffix}")
            current = self.show_var.get()
            self.show_combo['values'] = options
            if current in options:
                self.show_var.set(current)
            elif options:
                self.show_combo.current(0)
            else:
                self.show_var.set("")
            if self._book_refresh_job is not None:
                try:
                    self.parent.after_cancel(self._book_refresh_job)
                except Exception:
                    pass
            if hasattr(self, 'tab_book') and self.tab_book.winfo_exists():
                self._book_refresh_job = self.parent.after(5000, refresh_shows)
        
        refresh_shows()
        
        tk.Label(frame, text="Number of Seats", font=FONT['heading'],
                bg=COLORS['light'], fg=COLORS['dark']).grid(row=2, column=0, sticky='w', pady=10)
        self.seats_entry = tk.Entry(frame, font=FONT['normal'], width=12,
                                  bg='white', relief=tk.FLAT, bd=0,
                                  highlightthickness=1, highlightcolor=COLORS['primary'])
        self.seats_entry.grid(row=2, column=1, sticky='w', pady=10, padx=15)
        
        self.total_label = tk.Label(frame, text="Total: $0.00", font=('Segoe UI', 15, 'bold'),
                                  bg=COLORS['light'], fg='#27ae60')
        self.total_label.grid(row=3, column=1, sticky='w', pady=5, padx=15)
        
        def update_total(*args):
            try:
                seats = int(self.seats_entry.get()) if self.seats_entry.get().isdigit() else 0
                selected = self.show_var.get()
                if selected and seats > 0:
                    price_str = selected.split('$')[-1].split('/')[0]
                    price = float(price_str)
                    total = seats * price
                    self.total_label.config(text=f"Total: ${total:.2f}")
                else:
                    self.total_label.config(text="Total: $0.00")
            except:
                self.total_label.config(text="Total: $0.00")
        
        self.seats_entry.bind('<KeyRelease>', update_total)
        self.show_var.trace('w', update_total)
        
        def book():
            selected = self.show_var.get()
            if not selected:
                messagebox.showerror("Error", "Please select a show")
                return
            
            # Parse show info
            try:
                show_data = None
                for show in self.show_model.get_available():
                    base = f"{show[1]} - {show[2]} {show[3]}"
                    if selected.startswith(base):
                        show_data = show
                        break
                if not show_data:
                    messagebox.showerror("Error", "Invalid show selection")
                    return
                
                show_id, movie_title, date, time, available, price, deadline = show_data
                seats_str = self.seats_entry.get().strip()
                if not seats_str.isdigit() or int(seats_str) <= 0:
                    messagebox.showerror("Error", "Enter a valid positive number of seats")
                    return
                seats = int(seats_str)
                
                if seats > available:
                    messagebox.showerror("Error", f"Only {available} seats available")
                    return
                
                # Calculate bill
                subtotal = seats * price
                tax = subtotal * 0.10
                discount = subtotal * 0.05 if seats >= 5 else 0
                final_total = subtotal + tax - discount
                
                confirm = messagebox.askyesno("Confirm Booking", 
                    f"Total Amount: ${final_total:.2f}\nProceed with booking?")
                if not confirm:
                    return

                # Re-check right before committing: the booking window may
                # have expired (or seats sold out) while the confirm dialog
                # was open. If so, the booking is automatically rejected.
                if not self.show_model.is_booking_open(show_id):
                    messagebox.showerror("Booking Closed",
                        "Sorry, the booking window for this show has just closed.")
                    refresh_shows()
                    return
                
                # Create booking
                user_id = self.current_user["id"]
                seat_numbers = ",".join(str(i) for i in range(available - seats + 1, available + 1))
                self.booking_model.create(user_id, show_id, seat_numbers, final_total)
                self.show_model.update_seats(show_id, available - seats)
                
                # Show bill
                bill = generate_bill(movie_title, date, time, seats, price, subtotal, tax, discount, final_total)
                messagebox.showinfo("Payment Bill", bill)
                
                # Refresh UI
                refresh_shows()
                self.refresh_my_bookings()
                self.seats_entry.delete(0, tk.END)
                self.total_label.config(text="Total: $0.00")
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = tk.Frame(frame, bg=COLORS['light'])
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        book_btn = create_styled_button(btn_frame, "Book Now", book,
                                      COLORS['primary'], COLORS['primary_dark'])
        book_btn.pack(side=tk.LEFT, padx=10)
        
        refresh_btn = create_styled_button(btn_frame, "Refresh Shows", refresh_shows,
                                         COLORS['secondary'], COLORS['secondary_dark'])
        refresh_btn.pack(side=tk.LEFT, padx=10)
    
    def populate_my_bookings(self):
        """Populate my bookings tab"""
        for widget in self.tab_bookings.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.tab_bookings, bg=COLORS['light'])
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frame, text="📋 My Bookings", font=('Helvetica', 24, 'bold'),
                bg=COLORS['light'], fg=COLORS['dark']).pack(pady=10)
        
        toolbar = tk.Frame(frame, bg=COLORS['light'])
        toolbar.pack(fill=tk.X, pady=5)
        
        cancel_btn = create_styled_button(toolbar, "❌ Cancel Selected", self.cancel_booking,
                                        COLORS['danger'], COLORS['danger_dark'])
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = create_styled_button(toolbar, "🔄 Refresh", self.refresh_my_bookings,
                                         COLORS['primary'], COLORS['primary_dark'])
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        tree_frame = tk.Frame(frame, bg=COLORS['light'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Booking ID", "Movie", "Date", "Time", "Seats Booked", "Total Price", "Booking Time")
        self.user_booking_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.user_booking_tree.heading(col, text=col)
            self.user_booking_tree.column(col, width=100 if col != "Movie" else 170)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.user_booking_tree.yview)
        self.user_booking_tree.configure(yscrollcommand=scroll.set)
        self.user_booking_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_my_bookings()
    
    def refresh_my_bookings(self):
        """Refresh user's bookings"""
        if not hasattr(self, 'user_booking_tree') or not self.user_booking_tree:
            return
            
        for item in self.user_booking_tree.get_children():
            self.user_booking_tree.delete(item)
        
        user_id = self.current_user["id"]
        bookings = self.booking_model.get_user_bookings(user_id)
        for i, b in enumerate(bookings):
            values = list(b)
            values[5] = f"${values[5]:.2f}"
            tag = 'even' if i % 2 == 0 else 'odd'
            self.user_booking_tree.insert("", tk.END, iid=str(b[0]), values=values, tags=(tag,))
        self.user_booking_tree.tag_configure('even', background=COLORS['even_row'])
        self.user_booking_tree.tag_configure('odd', background=COLORS['odd_row'])
    
    def cancel_booking(self):
        """Cancel selected booking"""
        if not hasattr(self, 'user_booking_tree') or not self.user_booking_tree:
            return
        selected = self.user_booking_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a booking to cancel.")
            return
        booking_id = int(selected[0])
        confirm = messagebox.askyesno("Confirm Cancel", f"Cancel booking ID {booking_id}? Seats will be restored.")
        if confirm:
            self.booking_model.delete(booking_id)
            messagebox.showinfo("Success", "Booking cancelled and seats restored.")
            self.refresh_my_bookings()
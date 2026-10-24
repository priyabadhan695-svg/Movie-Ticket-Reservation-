# main.py
import tkinter as tk
from tkinter import ttk
from database import Database
from models import User, Movie, Show, Booking
from auth import AuthManager
from admin_panel import AdminPanel 
from user_panel import UserPanel
from config import APP_CONFIG, COLORS

class MovieApp:
    def __init__(self):
        self.db = Database()
        self.root = tk.Tk()
        self.root.title(APP_CONFIG['app_name'])
        self.root.geometry(APP_CONFIG['window_size'])
        self.root.resizable(True, True)
        self.center_window()
        
        # Models
        self.user_model = User(self.db)
        self.movie_model = Movie(self.db)
        self.show_model = Show(self.db)
        self.booking_model = Booking(self.db)
        
        # Setup styles
        self.setup_styles()
        
        # Auth manager
        self.auth = AuthManager(self.root, self.user_model, self.on_login_success)
        self.auth.show_login()
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TNotebook', background=COLORS['light'], borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 11, 'bold'), 
                       padding=[15, 8], background='#bdc3c7')
        style.map('TNotebook.Tab', background=[('selected', COLORS['primary']), 
                                              ('active', COLORS['light'])])
        
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=28,
                       background=COLORS['white'], fieldbackground=COLORS['white'])
        style.map('Treeview', background=[('selected', COLORS['secondary'])])
        
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'),
                       background=COLORS['dark'], foreground='white')
        style.map('Treeview.Heading', background=[('active', COLORS['darker'])])
        
        style.configure('TCombobox', font=('Segoe UI', 11), padding=5)
        style.configure('TButton', font=('Segoe UI', 11, 'bold'), padding=8,
                       background=COLORS['primary'], foreground='white')
        style.map('TButton', background=[('active', COLORS['primary_dark'])])
    
    def on_login_success(self, user):
        """Handle successful login"""
        if user['role'] == 'admin':
            admin_panel = AdminPanel(self.root, self.db, user)
            admin_panel.auth = self.auth
            admin_panel.show()
        else:
            user_panel = UserPanel(self.root, self.db, user)
            user_panel.auth = self.auth
            user_panel.show()
        
    def run(self):
        """Run the application"""
        self.root.mainloop()
        self.db.close()

if __name__ == "__main__":
    app = MovieApp()
    app.run()
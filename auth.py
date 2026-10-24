# auth.py
import tkinter as tk
from tkinter import messagebox
from config import COLORS, FONT
from utils import create_gradient_bg, create_card, create_styled_entry, create_styled_button

class AuthManager:
    def __init__(self, parent, user_model, on_login_success):
        self.parent = parent
        self.user_model = user_model
        self.on_login_success = on_login_success
        self.current_user = None
    
    def show_login(self):
        """Display login screen"""
        self.clear_window()
        canvas = tk.Canvas(self.parent, bg=COLORS['dark'], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        create_gradient_bg(canvas)
        
        card = create_card(canvas, width=440, height=400)
        
        tk.Label(card, text="🎬 Movie Reservation", font=('Helvetica', 26, 'bold'),
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(30, 15))
        
        tk.Label(card, text="Username", font=FONT['normal'], 
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(10,0))
        self.username_entry = create_styled_entry(card, width=30)
        self.username_entry.pack(pady=5, ipady=4)
        
        tk.Label(card, text="Password", font=FONT['normal'],
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(10,0))
        self.password_entry = create_styled_entry(card, width=30, show='*')
        self.password_entry.pack(pady=5, ipady=4)
        
        btn_frame = tk.Frame(card, bg=COLORS['darker'])
        btn_frame.pack(pady=25)
        
        login_btn = create_styled_button(btn_frame, "Login", self.login, 
                                        COLORS['primary'], COLORS['primary_dark'])
        login_btn.pack(side=tk.LEFT, padx=10)
        
        reg_btn = create_styled_button(btn_frame, "Register", self.show_register,
                                      COLORS['secondary'], COLORS['secondary_dark'])
        reg_btn.pack(side=tk.LEFT, padx=10)
        
        self.parent.bind('<Return>', lambda e: self.login())
    
    def show_register(self):
        """Display registration screen"""
        self.clear_window()
        canvas = tk.Canvas(self.parent, bg=COLORS['dark'], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        create_gradient_bg(canvas)
        card = create_card(canvas, width=440, height=460)
        
        tk.Label(card, text="📝 Create Account", font=('Helvetica', 24, 'bold'),
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(25, 10))
        
        tk.Label(card, text="Username", font=FONT['normal'],
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(10,0))
        self.reg_user_entry = create_styled_entry(card, width=30)
        self.reg_user_entry.pack(pady=5, ipady=4)
        
        tk.Label(card, text="Password", font=FONT['normal'],
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(10,0))
        self.reg_pass_entry = create_styled_entry(card, width=30, show='*')
        self.reg_pass_entry.pack(pady=5, ipady=4)
        
        tk.Label(card, text="Confirm Password", font=FONT['normal'],
                bg=COLORS['darker'], fg=COLORS['light']).pack(pady=(10,0))
        self.reg_confirm_entry = create_styled_entry(card, width=30, show='*')
        self.reg_confirm_entry.pack(pady=5, ipady=4)
        
        btn_frame = tk.Frame(card, bg=COLORS['darker'])
        btn_frame.pack(pady=25)
        
        reg_btn = create_styled_button(btn_frame, "Register", self.register,
                                     COLORS['primary'], COLORS['primary_dark'])
        reg_btn.pack(side=tk.LEFT, padx=10)
        
        back_btn = create_styled_button(btn_frame, "Back to Login", self.show_login,
                                      COLORS['danger'], COLORS['danger_dark'])
        back_btn.pack(side=tk.LEFT, padx=10)
        
        self.parent.bind('<Return>', lambda e: self.register())
    
    def login(self):
        """Authenticate user"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        user = self.user_model.authenticate(username, password)
        if user:
            self.current_user = {"id": user[0], "username": user[1], "role": user[2]}
            self.on_login_success(self.current_user)
        else:
            messagebox.showerror("Error", "Invalid credentials")
    
    def register(self):
        """Register new user"""
        username = self.reg_user_entry.get().strip()
        password = self.reg_pass_entry.get().strip()
        confirm = self.reg_confirm_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty")
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters")
            return
        if self.user_model.user_exists(username):
            messagebox.showerror("Error", "Username already taken")
            return
        
        self.user_model.create(username, password)
        messagebox.showinfo("Success", "Registration successful! Please login.")
        self.show_login()
    
    def clear_window(self):
        """Clear all widgets from parent"""
        for widget in self.parent.winfo_children():
            widget.destroy()
    
    def logout(self):
        """Logout user"""
        self.current_user = None
        self.show_login()
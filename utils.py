# utils.py
import tkinter as tk
import re
import datetime
from config import COLORS, FONT

def create_gradient_bg(canvas, width=1050, height=800, start_color='#2c3e50'):
    """Create gradient background on canvas"""
    r1, g1, b1 = 44, 62, 80
    for i in range(0, height, 10):
        r = int(r1 + i/15)
        g = int(g1 + i/20)
        b = int(b1 + i/20)
        color = f'#{r:02x}{g:02x}{b:02x}'
        canvas.create_rectangle(0, i, width, i+10, fill=color, outline='')

def create_card(parent, width=440, height=400, bg=COLORS['darker']):
    """Create a styled card frame"""
    card = tk.Frame(parent, bg=bg, bd=0)
    card.place(relx=0.5, rely=0.5, anchor='center', width=width, height=height)
    return card

def create_styled_entry(parent, width=30, show=None):
    """Create a styled entry widget"""
    entry = tk.Entry(parent, font=FONT['normal'], width=width, 
                     show=show, bg=COLORS['light'], fg=COLORS['dark'],
                     relief=tk.FLAT, bd=0, highlightthickness=1, 
                     highlightcolor=COLORS['primary'])
    return entry

def create_styled_button(parent, text, command, color, hover_color,
                         font=FONT['normal'], padx=20, pady=8):
    """Create a styled button"""
    btn = tk.Button(parent, text=text, command=command, font=font,
                    bg=color, fg='white', relief=tk.FLAT, padx=padx, 
                    pady=pady, activebackground=hover_color, 
                    activeforeground='white', bd=0)
    return btn

def validate_date(date_str):
    """Validate date format YYYY-MM-DD"""
    return bool(re.match(r'\d{4}-\d{2}-\d{2}', date_str))

def validate_time(time_str):
    """Validate time format HH:MM"""
    return bool(re.match(r'\d{2}:\d{2}', time_str))

def validate_price(price_str):
    """Validate price is a non-negative number"""
    try:
        price = float(price_str)
        return price >= 0
    except:
        return False

def validate_duration(duration_str):
    """Validate the 'available for X minutes' timer field.
    Empty string is allowed and means 'no time limit'."""
    if duration_str.strip() == "":
        return True
    return duration_str.strip().isdigit() and int(duration_str.strip()) > 0

def format_time_left(deadline_str):
    """Turn a booking_deadline ('YYYY-MM-DD HH:MM:SS') into a short,
    human-friendly status string for display in the UI."""
    if not deadline_str:
        return "No limit"
    try:
        deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "No limit"
    remaining = deadline - datetime.datetime.now()
    total_seconds = int(remaining.total_seconds())
    if total_seconds <= 0:
        return "Expired"
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes}m left"
    if minutes > 0:
        return f"{minutes}m {seconds}s left"
    return f"{seconds}s left"

def generate_bill(movie_title, date, time, seats, price_per, subtotal, tax, discount, final_total):
    """Generate formatted bill"""
    return f"""
═══════════════════════════════════════════
            🎬 MOVIE TICKET RECEIPT
═══════════════════════════════════════════
Movie      : {movie_title}
Date       : {date}
Time       : {time}
Seats      : {seats}
Price/ticket: ${price_per:.2f}
───────────────────────────────────────────
Subtotal   : ${subtotal:.2f}
Tax (10%)  : ${tax:.2f}
Discount ({'5%' if discount > 0 else '0%'}) : ${discount:.2f}
───────────────────────────────────────────
TOTAL      : ${final_total:.2f}
═══════════════════════════════════════════
Thank you for booking with us! 🎉
    """
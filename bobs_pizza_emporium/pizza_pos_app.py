#!/usr/bin/env python3
"""
Pizza Point of Sales Application for Bob's Pizza Emporium
System Requirements Implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

class PizzaPOSApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bob's Pizza Emporium - Point of Sales System")
        self.root.geometry("1200x800")
        
        # Define color scheme inspired by the pizza ordering interface
        self.colors = {
            'bg_primary': '#e8f4fd',      # Light blue background (like the image)
            'bg_secondary': '#d1e7f0',    # Medium blue-gray background
            'bg_sidebar': '#4a6fa5',      # Darker blue for sidebar (like "Current Pizza" area)
            'bg_header': '#2c3e50',       # Dark blue header
            'bg_button': '#6bb6ff',       # Bright blue buttons
            'bg_button_hover': '#5aa3e6', # Darker blue for hover
            'bg_success': '#27ae60',      # Green for success actions
            'bg_danger': '#e74c3c',       # Red for danger actions
            'bg_warning': '#f39c12',      # Orange for warnings
            'text_primary': '#2c3e50',    # Dark text
            'text_secondary': '#7f8c8d',  # Gray text
            'text_light': '#ffffff',      # White text
            'text_accent': '#e74c3c',     # Red accent text
            'text_button': '#000000',     # Black text for buttons
            'border': '#000000',          # Black border (like the image)
            'border_dark': '#34495e',     # Dark border
            'topping_bg': '#f0f8ff'       # Light blue for topping buttons
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Initialize database
        self.init_database()
        
        # Current user and cart
        self.current_user = None
        self.cart = []
        self.total = Decimal('0.00')
        self.tax_rate = Decimal('0.08')  # 8% tax rate
        
        # Pizza prices
        self.pizza_prices = {
            'small': Decimal('12.99'),
            'medium': Decimal('15.99'),
            'large': Decimal('18.99')
        }
        
        # Topping prices
        self.topping_prices = {
            'Pepperoni': Decimal('1.50'),
            'Sausage': Decimal('1.50'),
            'Bacon': Decimal('2.00'),
            'Pineapple': Decimal('1.00'),
            'Mushrooms': Decimal('1.00'),
            'Onions': Decimal('1.00')
        }
        
        # Drink prices
        self.drink_prices = {
            'Coca-Cola': Decimal('2.50'),
            'Pepsi': Decimal('2.50'),
            'Sprite': Decimal('2.50'),
            'Water': Decimal('1.50'),
            'Orange Juice': Decimal('3.00')
        }
        
        # Show login screen
        self.show_login()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        self.conn = sqlite3.connect('pizza_pos.db')
        self.cursor = self.conn.cursor()
        
        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                pin TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create orders table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                items TEXT NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                tax DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create default admin user if not exists
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO users (username, pin, is_admin) 
                VALUES ('admin', '1234', 1)
            ''')
        
        # Create default regular user if not exists
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 0')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO users (username, pin, is_admin) 
                VALUES ('employee', '5678', 0)
            ''')
        
        self.conn.commit()
    
    def show_login(self):
        """Display login screen"""
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Login frame
        login_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        login_frame.pack(expand=True, fill='both')
        
        # Title with rounded, friendly font styling
        title_label = tk.Label(login_frame, text="Bob's Pizza Emporium", 
                              font=('Arial', 32, 'bold'), bg=self.colors['bg_primary'], 
                              fg=self.colors['text_primary'])
        title_label.pack(pady=50)
        
        subtitle_label = tk.Label(login_frame, text="Point of Sales System", 
                                font=('Arial', 18), bg=self.colors['bg_primary'], 
                                fg=self.colors['text_secondary'])
        subtitle_label.pack(pady=10)
        
        # Login form container
        form_container = tk.Frame(login_frame, bg=self.colors['bg_secondary'], 
                                 relief='solid', bd=1)
        form_container.pack(pady=30, padx=50)
        
        # Login form
        form_frame = tk.Frame(form_container, bg=self.colors['bg_secondary'])
        form_frame.pack(pady=30, padx=30)
        
        # Username
        tk.Label(form_frame, text="Username:", font=('Arial', 12, 'bold'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', pady=(0,5))
        self.username_entry = tk.Entry(form_frame, font=('Arial', 12), width=25,
                                      relief='solid', bd=1, bg=self.colors['bg_primary'],
                                      fg=self.colors['text_primary'])
        self.username_entry.pack(pady=5)
        
        # PIN
        tk.Label(form_frame, text="4-Digit PIN:", font=('Arial', 12, 'bold'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', pady=(15,5))
        self.pin_entry = tk.Entry(form_frame, font=('Arial', 12), width=25, show='*',
                                 relief='solid', bd=1, bg=self.colors['bg_primary'],
                                 fg=self.colors['text_primary'])
        self.pin_entry.pack(pady=5)
        
        # Login button with rounded styling
        login_btn = tk.Button(form_frame, text="Login", font=('Arial', 14, 'bold'),
                             bg=self.colors['bg_button'], fg=self.colors['text_button'], 
                             width=15, relief='raised', bd=3, padx=25, pady=12,
                             activebackground=self.colors['bg_button_hover'],
                             activeforeground=self.colors['text_button'],
                             command=self.login)
        login_btn.pack(pady=20)
        
        # Forgot password button
        forgot_btn = tk.Button(form_frame, text="Forgot Password", font=('Arial', 10),
                              bg=self.colors['bg_secondary'], fg=self.colors['text_button'], 
                              relief='raised', bd=1, command=self.forgot_password,
                              activebackground=self.colors['bg_secondary'],
                              activeforeground=self.colors['text_button'])
        forgot_btn.pack(pady=5)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.login())
        self.username_entry.focus()
    
    def login(self):
        """Handle login authentication"""
        username = self.username_entry.get().strip()
        pin = self.pin_entry.get().strip()
        
        if not username or not pin:
            messagebox.showerror("Error", "Please enter both username and PIN")
            return
        
        if len(pin) != 4 or not pin.isdigit():
            messagebox.showerror("Error", "PIN must be exactly 4 digits")
            return
        
        # Check credentials
        self.cursor.execute('''
            SELECT id, username, is_admin FROM users 
            WHERE username = ? AND pin = ?
        ''', (username, pin))
        
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'is_admin': bool(user[2])
            }
            self.show_main_screen()
        else:
            messagebox.showerror("Error", "Invalid username or PIN")
            self.pin_entry.delete(0, tk.END)
    
    def forgot_password(self):
        """Handle forgot password functionality"""
        messagebox.showinfo("Password Reset", 
                           "An alert has been sent to the administrator. "
                           "Please contact your admin to reset your password.")
    
    def show_main_screen(self):
        """Display main application screen"""
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_header'], height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # User info
        user_label = tk.Label(header_frame, text=f"Welcome, {self.current_user['username']}", 
                             font=('Arial', 14, 'bold'), bg=self.colors['bg_header'], 
                             fg=self.colors['text_light'])
        user_label.pack(side='right', padx=20, pady=15)
        
        # Logout button
        logout_btn = tk.Button(header_frame, text="Logout", font=('Arial', 10),
                              bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                              relief='raised', bd=2, command=self.logout,
                              activebackground=self.colors['bg_danger'],
                              activeforeground=self.colors['text_button'])
        logout_btn.pack(side='right', padx=10, pady=15)
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        if self.current_user['is_admin']:
            self.show_admin_view(content_frame)
        else:
            self.show_user_view(content_frame)
    
    def show_user_view(self, parent):
        """Display user interface"""
        # Left frame - Menu
        menu_frame = tk.LabelFrame(parent, text="Menu", font=('Arial', 12, 'bold'),
                                  bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                  relief='solid', bd=1)
        menu_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Pizza section
        pizza_frame = tk.LabelFrame(menu_frame, text="Pizzas", font=('Arial', 10, 'bold'),
                                   bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                   relief='solid', bd=1)
        pizza_frame.pack(fill='x', padx=10, pady=10)
        
        # Standard pizzas
        standard_pizzas = [
            ("Margherita", "Classic tomato and mozzarella"),
            ("Pepperoni", "Pepperoni and mozzarella"),
            ("Supreme", "Pepperoni, sausage, mushrooms, onions"),
            ("Hawaiian", "Ham and pineapple"),
            ("Meat Lovers", "Pepperoni, sausage, bacon")
        ]
        
        for pizza_name, description in standard_pizzas:
            pizza_btn = tk.Button(pizza_frame, text=f"{pizza_name}\n{description}",
                                font=('Arial', 9), bg=self.colors['bg_secondary'], 
                                fg=self.colors['text_button'], relief='raised', bd=2,
                                activebackground=self.colors['bg_secondary'],
                                activeforeground=self.colors['text_button'],
                                command=lambda p=pizza_name: self.add_standard_pizza(p))
            pizza_btn.pack(fill='x', padx=5, pady=2)
        
        # Custom pizza button with enhanced styling
        custom_btn = tk.Button(pizza_frame, text="🍕 Custom Pizza", font=('Arial', 12, 'bold'),
                              bg=self.colors['bg_button'], fg=self.colors['text_button'], 
                              relief='raised', bd=3, command=self.create_custom_pizza,
                              activebackground=self.colors['bg_button_hover'],
                              activeforeground=self.colors['text_button'],
                              padx=10, pady=8)
        custom_btn.pack(fill='x', padx=5, pady=8)
        
        # Drinks section
        drinks_frame = tk.LabelFrame(menu_frame, text="Drinks", font=('Arial', 10, 'bold'),
                                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                    relief='solid', bd=1)
        drinks_frame.pack(fill='x', padx=10, pady=10)
        
        for drink, price in self.drink_prices.items():
            drink_btn = tk.Button(drinks_frame, text=f"{drink} - ${price}",
                                font=('Arial', 9), bg=self.colors['bg_secondary'], 
                                fg=self.colors['text_button'], relief='raised', bd=2,
                                activebackground=self.colors['bg_secondary'],
                                activeforeground=self.colors['text_button'],
                                command=lambda d=drink, p=price: self.add_drink(d, p))
            drink_btn.pack(fill='x', padx=5, pady=2)
        
        # Right frame - Cart and Order
        cart_frame = tk.LabelFrame(parent, text="Order Cart", font=('Arial', 12, 'bold'),
                                  bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                  relief='solid', bd=1)
        cart_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Cart list
        self.cart_listbox = tk.Listbox(cart_frame, font=('Arial', 10), height=15,
                                      bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                      relief='solid', bd=1)
        self.cart_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Cart controls
        cart_controls = tk.Frame(cart_frame, bg=self.colors['bg_primary'])
        cart_controls.pack(fill='x', padx=10, pady=5)
        
        remove_btn = tk.Button(cart_controls, text="Remove Item", font=('Arial', 10),
                              bg=self.colors['bg_warning'], fg=self.colors['text_button'], 
                              relief='raised', bd=2, command=self.remove_cart_item,
                              activebackground=self.colors['bg_warning'],
                              activeforeground=self.colors['text_button'])
        remove_btn.pack(side='left', padx=5)
        
        clear_btn = tk.Button(cart_controls, text="Clear Cart", font=('Arial', 10),
                             bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                             relief='raised', bd=2, command=self.clear_cart,
                             activebackground=self.colors['bg_danger'],
                             activeforeground=self.colors['text_button'])
        clear_btn.pack(side='left', padx=5)
        
        # Order summary
        summary_frame = tk.Frame(cart_frame, bg=self.colors['bg_primary'])
        summary_frame.pack(fill='x', padx=10, pady=10)
        
        self.subtotal_label = tk.Label(summary_frame, text="Subtotal: $0.00", 
                                      font=('Arial', 12), bg=self.colors['bg_primary'],
                                      fg=self.colors['text_primary'])
        self.subtotal_label.pack(anchor='w')
        
        self.tax_label = tk.Label(summary_frame, text="Tax: $0.00", 
                                 font=('Arial', 12), bg=self.colors['bg_primary'],
                                 fg=self.colors['text_primary'])
        self.tax_label.pack(anchor='w')
        
        self.total_label = tk.Label(summary_frame, text="Total: $0.00", 
                                   font=('Arial', 14, 'bold'), bg=self.colors['bg_primary'], 
                                   fg=self.colors['text_accent'])
        self.total_label.pack(anchor='w')
        
        # Process order button with enhanced styling
        process_btn = tk.Button(cart_frame, text="✅ Process Order", font=('Arial', 16, 'bold'),
                               bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                               relief='raised', bd=3, command=self.process_order,
                               activebackground=self.colors['bg_success'],
                               activeforeground=self.colors['text_button'],
                               padx=15, pady=12)
        process_btn.pack(fill='x', padx=10, pady=15)
    
    def show_admin_view(self, parent):
        """Display admin interface"""
        # Admin controls
        admin_frame = tk.LabelFrame(parent, text="Administrative Panel", 
                                   font=('Arial', 12, 'bold'), bg=self.colors['bg_primary'], 
                                   fg=self.colors['text_primary'], relief='solid', bd=1)
        admin_frame.pack(fill='both', expand=True)
        
        # User management
        user_mgmt_frame = tk.LabelFrame(admin_frame, text="User Management", 
                                        font=('Arial', 10, 'bold'), bg=self.colors['bg_primary'],
                                        fg=self.colors['text_primary'], relief='solid', bd=1)
        user_mgmt_frame.pack(fill='x', padx=10, pady=10)
        
        # User list
        self.user_listbox = tk.Listbox(user_mgmt_frame, font=('Arial', 10), height=8,
                                      bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                      relief='solid', bd=1)
        self.user_listbox.pack(fill='x', padx=10, pady=5)
        
        # User controls
        user_controls = tk.Frame(user_mgmt_frame, bg=self.colors['bg_primary'])
        user_controls.pack(fill='x', padx=10, pady=5)
        
        tk.Button(user_controls, text="Add User", font=('Arial', 10),
                 bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=self.add_user,
                 activebackground=self.colors['bg_success'],
                 activeforeground=self.colors['text_button']).pack(side='left', padx=5)
        
        tk.Button(user_controls, text="Edit User", font=('Arial', 10),
                 bg=self.colors['bg_button'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=self.edit_user,
                 activebackground=self.colors['bg_button_hover'],
                 activeforeground=self.colors['text_button']).pack(side='left', padx=5)
        
        tk.Button(user_controls, text="Delete User", font=('Arial', 10),
                 bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=self.delete_user,
                 activebackground=self.colors['bg_danger'],
                 activeforeground=self.colors['text_button']).pack(side='left', padx=5)
        
        tk.Button(user_controls, text="Reset Password", font=('Arial', 10),
                 bg=self.colors['bg_warning'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=self.reset_password,
                 activebackground=self.colors['bg_warning'],
                 activeforeground=self.colors['text_button']).pack(side='left', padx=5)
        
        # System settings
        settings_frame = tk.LabelFrame(admin_frame, text="System Settings", 
                                      font=('Arial', 10, 'bold'), bg=self.colors['bg_primary'],
                                      fg=self.colors['text_primary'], relief='solid', bd=1)
        settings_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(settings_frame, text="Configure Prices", font=('Arial', 10),
                 bg=self.colors['bg_button'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=self.configure_prices,
                 activebackground=self.colors['bg_button_hover'],
                 activeforeground=self.colors['text_button']).pack(side='left', padx=10, pady=10)
        
        tk.Button(settings_frame, text="View Orders", font=('Arial', 10),
                 bg=self.colors['bg_button'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=self.view_orders,
                 activebackground=self.colors['bg_button_hover'],
                 activeforeground=self.colors['text_button']).pack(side='left', padx=10, pady=10)
        
        # Load users
        self.load_users()
    
    def add_standard_pizza(self, pizza_name):
        """Add standard pizza to cart"""
        size = simpledialog.askstring("Pizza Size", "Enter size (small/medium/large):", 
                                     initialvalue="medium")
        if size and size.lower() in self.pizza_prices:
            size = size.lower()
            price = self.pizza_prices[size]
            item = {
                'type': 'pizza',
                'name': f"{pizza_name} ({size.title()})",
                'price': price,
                'size': size
            }
            self.cart.append(item)
            self.update_cart_display()
        elif size:
            messagebox.showerror("Error", "Invalid size. Please enter small, medium, or large.")
    
    def create_custom_pizza(self):
        """Create custom pizza dialog inspired by the image design"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Pizza")
        dialog.geometry("1000x700")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Header with user info (like in the image)
        header_frame = tk.Frame(dialog, bg=self.colors['bg_primary'], height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # User avatar placeholder (simple circle)
        avatar_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'], width=40, height=40)
        avatar_frame.pack(side='left', padx=20, pady=10)
        avatar_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, text="Add Pizza", 
                              font=('Arial', 24, 'bold'), bg=self.colors['bg_primary'], 
                              fg=self.colors['text_primary'])
        title_label.pack(side='left', padx=20, pady=15)
        
        # Username display
        username_label = tk.Label(header_frame, text=self.current_user['username'], 
                                 font=('Arial', 16, 'bold'), bg=self.colors['bg_primary'], 
                                 fg=self.colors['text_primary'])
        username_label.pack(side='right', padx=20, pady=15)
        
        # Main content frame
        main_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left sidebar - Current Pizza (like in the image)
        sidebar_frame = tk.Frame(main_frame, bg=self.colors['bg_sidebar'], width=250)
        sidebar_frame.pack(side='left', fill='y', padx=(0, 10))
        sidebar_frame.pack_propagate(False)
        
        # Current Pizza title
        current_pizza_label = tk.Label(sidebar_frame, text="Current Pizza", 
                                      font=('Arial', 16, 'bold'), bg=self.colors['bg_sidebar'], 
                                      fg=self.colors['text_light'])
        current_pizza_label.pack(pady=20)
        
        # Current toppings display
        self.current_toppings_text = tk.Text(sidebar_frame, height=8, width=25, 
                                           font=('Arial', 10), bg=self.colors['bg_sidebar'], 
                                           fg=self.colors['text_light'], relief='flat', bd=0)
        self.current_toppings_text.pack(pady=10, padx=10)
        self.current_toppings_text.insert('1.0', "")
        self.current_toppings_text.config(state='disabled')
        
        # Size selection in sidebar
        size_label = tk.Label(sidebar_frame, text="Size", 
                             font=('Arial', 14, 'bold'), bg=self.colors['bg_sidebar'], 
                             fg=self.colors['text_light'])
        size_label.pack(pady=(20, 10))
        
        # Size selection frame
        size_frame = tk.Frame(sidebar_frame, bg=self.colors['bg_sidebar'])
        size_frame.pack(pady=10)
        
        self.selected_size = tk.StringVar(value="medium")
        self.size_buttons = {}
        
        # Create visual size buttons (inspired by the image's circular size indicators)
        sizes = ['small', 'medium', 'large']
        size_icons = ['●', '●●', '●●●']  # Simple circular indicators
        
        for i, size in enumerate(sizes):
            # Create circular-like button with size indicator
            size_btn = tk.Button(size_frame, text=f"{size_icons[i]}\n{size.title()}\n${self.pizza_prices[size]}", 
                                font=('Arial', 9, 'bold'), width=6, height=4,
                                bg=self.colors['bg_secondary'], fg=self.colors['text_button'], 
                                relief='raised', bd=3, command=lambda s=size: self.select_size(s),
                                activebackground=self.colors['bg_button_hover'],
                                activeforeground=self.colors['text_button'])
            size_btn.pack(side='left', padx=3)
            self.size_buttons[size] = size_btn
        
        # Highlight medium by default
        self.size_buttons['medium'].config(bg=self.colors['bg_button'])
        
        # Add to Order button
        add_to_order_btn = tk.Button(sidebar_frame, text="Add to Order", font=('Arial', 14, 'bold'),
                                   bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                                   relief='raised', bd=3, command=lambda: self.add_pizza_to_order(dialog),
                                   activebackground=self.colors['bg_success'],
                                   activeforeground=self.colors['text_button'],
                                   padx=15, pady=10)
        add_to_order_btn.pack(pady=20)
        
        # Right side - Topping selection area (like in the image)
        toppings_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'])
        toppings_frame.pack(side='right', fill='both', expand=True)
        
        # Toppings title
        toppings_title = tk.Label(toppings_frame, text="Select Toppings", 
                                 font=('Arial', 18, 'bold'), bg=self.colors['bg_secondary'], 
                                 fg=self.colors['text_primary'])
        toppings_title.pack(pady=20)
        
        # Toppings grid (2 columns, 3 rows like in the image)
        toppings_grid = tk.Frame(toppings_frame, bg=self.colors['bg_secondary'])
        toppings_grid.pack(expand=True, padx=20, pady=20)
        
        self.selected_toppings = {}
        self.topping_counts = {}
        
        # Create topping buttons with +/- controls and icons (like in the image)
        toppings = list(self.topping_prices.keys())
        print(f"DEBUG: Toppings list: {toppings}")  # Debug line
        
        # Topping icons based on the image descriptions
        topping_icons = {
            'Pepperoni': '🍕',      # Red-brown pepperoni slices
            'Bacon': '🥓',           # Wavy bacon strip
            'Mushrooms': '🍄',       # Mushroom cap
            'Onions': '🧅',          # Purple onion
            'Sausage': '🌭',         # Sausage link
            'Pineapple': '🍍'        # Pineapple chunk
        }
        
        for i, topping in enumerate(toppings):
            row = i // 2
            col = i % 2
            print(f"DEBUG: Creating buttons for topping: {topping} at row {row}, col {col}")  # Debug line
            
            # Topping button frame
            topping_frame = tk.Frame(toppings_grid, bg=self.colors['topping_bg'], 
                                   relief='raised', bd=3)
            topping_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            # Topping icon and name
            icon_label = tk.Label(topping_frame, text=topping_icons.get(topping, '🍕'), 
                                 font=('Arial', 20), bg=self.colors['topping_bg'], 
                                 fg=self.colors['text_primary'])
            icon_label.pack(pady=(8, 2))
            
            topping_label = tk.Label(topping_frame, text=topping, 
                                   font=('Arial', 11, 'bold'), bg=self.colors['topping_bg'], 
                                   fg=self.colors['text_primary'])
            topping_label.pack(pady=(0, 5))
            
            # Controls frame
            controls_frame = tk.Frame(topping_frame, bg=self.colors['topping_bg'])
            controls_frame.pack(pady=5)
            
            # Create closure to capture the current topping value
            def make_decrease_handler(t):
                return lambda: self.decrease_topping(t)
            
            def make_increase_handler(t):
                return lambda: self.increase_topping(t)
            
            # Minus button
            minus_btn = tk.Button(controls_frame, text="—", font=('Arial', 18, 'bold'), 
                                 width=3, height=1, bg=self.colors['bg_secondary'], 
                                 fg=self.colors['text_button'], relief='raised', bd=3,
                                 command=make_decrease_handler(topping),
                                 activebackground=self.colors['bg_button_hover'],
                                 activeforeground=self.colors['text_button'])
            minus_btn.pack(side='left', padx=5)
            
            # Count display
            count_label = tk.Label(controls_frame, text="0", font=('Arial', 16, 'bold'), 
                                  bg=self.colors['topping_bg'], fg=self.colors['text_primary'],
                                  width=3)
            count_label.pack(side='left', padx=5)
            
            # Plus button
            plus_btn = tk.Button(controls_frame, text="+", font=('Arial', 18, 'bold'), 
                                width=3, height=1, bg=self.colors['bg_secondary'], 
                                fg=self.colors['text_button'], relief='raised', bd=3,
                                command=make_increase_handler(topping),
                                activebackground=self.colors['bg_button_hover'],
                                activeforeground=self.colors['text_button'])
            plus_btn.pack(side='left', padx=5)
            
            # Store references
            self.topping_counts[topping] = count_label
            print(f"DEBUG: Stored count label for {topping}")  # Debug line
        
        # Configure grid weights
        toppings_grid.columnconfigure(0, weight=1)
        toppings_grid.columnconfigure(1, weight=1)
        
        # Bottom buttons
        button_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        button_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Button(button_frame, text="Cancel", font=('Arial', 12),
                 bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=dialog.destroy,
                 activebackground=self.colors['bg_danger'],
                 activeforeground=self.colors['text_button']).pack(side='right', padx=10)
    
    def select_size(self, size):
        """Select pizza size and update visual feedback"""
        self.selected_size.set(size)
        # Reset all buttons to default color
        for s, btn in self.size_buttons.items():
            btn.config(bg=self.colors['bg_secondary'])
        # Highlight selected size
        self.size_buttons[size].config(bg=self.colors['bg_button'])
        self.update_current_pizza_display()
    
    def increase_topping(self, topping):
        """Increase topping count"""
        print(f"DEBUG: increase_topping called with: {topping}")  # Debug line
        print(f"DEBUG: topping_counts keys: {list(self.topping_counts.keys())}")  # Debug line
        if topping not in self.selected_toppings:
            self.selected_toppings[topping] = 0
        self.selected_toppings[topping] += 1
        if topping in self.topping_counts:
            self.topping_counts[topping].config(text=str(self.selected_toppings[topping]))
            print(f"DEBUG: Updated count for {topping} to {self.selected_toppings[topping]}")  # Debug line
        else:
            print(f"DEBUG: ERROR - {topping} not found in topping_counts!")  # Debug line
        self.update_current_pizza_display()
    
    def decrease_topping(self, topping):
        """Decrease topping count"""
        if topping not in self.selected_toppings:
            self.selected_toppings[topping] = 0
        if self.selected_toppings[topping] > 0:
            self.selected_toppings[topping] -= 1
            self.topping_counts[topping].config(text=str(self.selected_toppings[topping]))
            self.update_current_pizza_display()
    
    def update_current_pizza_display(self):
        """Update the current pizza display in the sidebar"""
        self.current_toppings_text.config(state='normal')
        self.current_toppings_text.delete('1.0', tk.END)
        
        # Show selected size
        size_text = f"Size: {self.selected_size.get().title()}\n\n"
        self.current_toppings_text.insert('1.0', size_text)
        
        # Show selected toppings
        toppings_text = "Toppings:\n"
        has_toppings = False
        for topping, count in self.selected_toppings.items():
            if count > 0:
                has_toppings = True
                toppings_text += f"• {topping} x{count}\n"
        
        if not has_toppings:
            toppings_text += ""
        
        self.current_toppings_text.insert(tk.END, toppings_text)
        self.current_toppings_text.config(state='disabled')
    
    def add_pizza_to_order(self, dialog):
        """Add pizza to order with validation"""
        # Check if size is selected
        size = self.selected_size.get()
        if not size:
            messagebox.showwarning("Size Required", "Please select a pizza size before adding to order.")
            return
        
        # Check if at least one topping is selected
        has_toppings = False
        for topping, count in self.selected_toppings.items():
            if count > 0:
                has_toppings = True
                break
        
        if not has_toppings:
            messagebox.showwarning("Toppings Required", "Please select at least one topping before adding to order.")
            return
        
        # Add the pizza to cart
        self.add_custom_pizza(dialog)
    
    def add_custom_pizza(self, dialog):
        """Add custom pizza to cart"""
        size = self.selected_size.get()
        base_price = self.pizza_prices[size]
        
        toppings = []
        topping_price = Decimal('0.00')
        
        # Group toppings by name and calculate total price
        topping_groups = {}
        for topping, count in self.selected_toppings.items():
            if count > 0:
                topping_groups[topping] = count
                # Add topping price for each quantity
                for _ in range(count):
                    topping_price += self.topping_prices[topping]
        
        total_price = base_price + topping_price
        
        # Create descriptive name with grouped toppings
        if topping_groups:
            topping_names = [f"{topping} x{count}" for topping, count in topping_groups.items()]
            pizza_name = f"Custom Pizza ({size.title()}) - {', '.join(topping_names)}"
        else:
            pizza_name = f"Custom Pizza ({size.title()}) - Plain"
        
        item = {
            'type': 'custom_pizza',
            'name': pizza_name,
            'price': total_price,
            'size': size,
            'toppings': list(topping_groups.keys())  # Store unique topping names
        }
        
        self.cart.append(item)
        self.update_cart_display()
        dialog.destroy()
    
    def add_drink(self, drink_name, price):
        """Add drink to cart"""
        item = {
            'type': 'drink',
            'name': drink_name,
            'price': price
        }
        self.cart.append(item)
        self.update_cart_display()
    
    def update_cart_display(self):
        """Update cart display and totals"""
        self.cart_listbox.delete(0, tk.END)
        self.total = Decimal('0.00')
        
        for item in self.cart:
            display_text = f"{item['name']} - ${item['price']}"
            self.cart_listbox.insert(tk.END, display_text)
            self.total += item['price']
        
        # Calculate tax and total
        tax = self.total * self.tax_rate
        tax = tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        final_total = self.total + tax
        
        # Update labels
        self.subtotal_label.config(text=f"Subtotal: ${self.total}")
        self.tax_label.config(text=f"Tax: ${tax}")
        self.total_label.config(text=f"Total: ${final_total}")
    
    def remove_cart_item(self):
        """Remove selected item from cart"""
        selection = self.cart_listbox.curselection()
        if selection:
            index = selection[0]
            del self.cart[index]
            self.update_cart_display()
    
    def clear_cart(self):
        """Clear entire cart"""
        if messagebox.askyesno("Clear Cart", "Are you sure you want to clear the cart?"):
            self.cart = []
            self.update_cart_display()
    
    def process_order(self):
        """Process the order"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Your cart is empty. Please add items before processing.")
            return
        
        # Calculate final total
        tax = self.total * self.tax_rate
        tax = tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        final_total = self.total + tax
        
        # Confirm order
        order_summary = f"Order Total: ${final_total}\n\nItems:\n"
        for item in self.cart:
            order_summary += f"• {item['name']} - ${item['price']}\n"
        
        if messagebox.askyesno("Confirm Order", f"{order_summary}\n\nProcess this order?"):
            # Save order to database
            items_json = str(self.cart)
            self.cursor.execute('''
                INSERT INTO orders (user_id, items, subtotal, tax, total)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.current_user['id'], items_json, float(self.total), float(tax), float(final_total)))
            self.conn.commit()
            
            messagebox.showinfo("Order Processed", f"Order processed successfully!\nTotal: ${final_total}")
            
            # Clear cart
            self.cart = []
            self.update_cart_display()
    
    def load_users(self):
        """Load users for admin view"""
        self.user_listbox.delete(0, tk.END)
        self.cursor.execute('SELECT username, is_admin FROM users ORDER BY username')
        users = self.cursor.fetchall()
        
        for username, is_admin in users:
            admin_text = " (Admin)" if is_admin else ""
            self.user_listbox.insert(tk.END, f"{username}{admin_text}")
    
    def add_user(self):
        """Add new user"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add User")
        dialog.geometry("300x200")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Username
        tk.Label(dialog, text="Username:", font=('Arial', 10, 'bold'), 
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        username_entry = tk.Entry(dialog, font=('Arial', 10), width=20,
                                 relief='solid', bd=1, bg=self.colors['bg_primary'],
                                 fg=self.colors['text_primary'])
        username_entry.pack(padx=10, pady=5)
        
        # PIN
        tk.Label(dialog, text="4-Digit PIN:", font=('Arial', 10, 'bold'), 
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        pin_entry = tk.Entry(dialog, font=('Arial', 10), width=20, show='*',
                            relief='solid', bd=1, bg=self.colors['bg_primary'],
                            fg=self.colors['text_primary'])
        pin_entry.pack(padx=10, pady=5)
        
        # Admin checkbox
        is_admin_var = tk.BooleanVar()
        admin_check = tk.Checkbutton(dialog, text="Administrator", variable=is_admin_var, 
                                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        admin_check.pack(anchor='w', padx=10, pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        button_frame.pack(fill='x', padx=10, pady=10)
        
        def save_user():
            username = username_entry.get().strip()
            pin = pin_entry.get().strip()
            
            if not username or not pin:
                messagebox.showerror("Error", "Please enter both username and PIN")
                return
            
            if len(pin) != 4 or not pin.isdigit():
                messagebox.showerror("Error", "PIN must be exactly 4 digits")
                return
            
            try:
                self.cursor.execute('''
                    INSERT INTO users (username, pin, is_admin)
                    VALUES (?, ?, ?)
                ''', (username, pin, int(is_admin_var.get())))
                self.conn.commit()
                messagebox.showinfo("Success", "User added successfully!")
                dialog.destroy()
                self.load_users()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")
        
        tk.Button(button_frame, text="Save", font=('Arial', 10, 'bold'),
                 bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=save_user,
                 activebackground=self.colors['bg_success'],
                 activeforeground=self.colors['text_button']).pack(side='right', padx=5)
        
        tk.Button(button_frame, text="Cancel", font=('Arial', 10),
                 bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=dialog.destroy,
                 activebackground=self.colors['bg_danger'],
                 activeforeground=self.colors['text_button']).pack(side='right', padx=5)
    
    def edit_user(self):
        """Edit selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to edit")
            return
        
        username = self.user_listbox.get(selection[0]).split(' (Admin)')[0]
        
        # Get user data
        self.cursor.execute('SELECT username, pin, is_admin FROM users WHERE username = ?', (username,))
        user_data = self.cursor.fetchone()
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit User")
        dialog.geometry("300x200")
        dialog.configure(bg='#f0f0f0')
        
        # Username
        tk.Label(dialog, text="Username:", font=('Arial', 10), bg='#f0f0f0').pack(anchor='w', padx=10, pady=5)
        username_entry = tk.Entry(dialog, font=('Arial', 10), width=20)
        username_entry.insert(0, user_data[0])
        username_entry.pack(padx=10, pady=5)
        
        # PIN
        tk.Label(dialog, text="4-Digit PIN:", font=('Arial', 10), bg='#f0f0f0').pack(anchor='w', padx=10, pady=5)
        pin_entry = tk.Entry(dialog, font=('Arial', 10), width=20, show='*')
        pin_entry.insert(0, user_data[1])
        pin_entry.pack(padx=10, pady=5)
        
        # Admin checkbox
        is_admin_var = tk.BooleanVar(value=bool(user_data[2]))
        admin_check = tk.Checkbutton(dialog, text="Administrator", variable=is_admin_var, bg='#f0f0f0')
        admin_check.pack(anchor='w', padx=10, pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#f0f0f0')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        def save_changes():
            new_username = username_entry.get().strip()
            new_pin = pin_entry.get().strip()
            
            if not new_username or not new_pin:
                messagebox.showerror("Error", "Please enter both username and PIN")
                return
            
            if len(new_pin) != 4 or not new_pin.isdigit():
                messagebox.showerror("Error", "PIN must be exactly 4 digits")
                return
            
            try:
                self.cursor.execute('''
                    UPDATE users SET username = ?, pin = ?, is_admin = ?
                    WHERE username = ?
                ''', (new_username, new_pin, int(is_admin_var.get()), username))
                self.conn.commit()
                messagebox.showinfo("Success", "User updated successfully!")
                dialog.destroy()
                self.load_users()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")
        
        tk.Button(button_frame, text="Save", font=('Arial', 10, 'bold'),
                 bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=save_changes,
                 activebackground=self.colors['bg_success'],
                 activeforeground=self.colors['text_button']).pack(side='right', padx=5)
        
        tk.Button(button_frame, text="Cancel", font=('Arial', 10),
                 bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=dialog.destroy,
                 activebackground=self.colors['bg_danger'],
                 activeforeground=self.colors['text_button']).pack(side='right', padx=5)
    
    def delete_user(self):
        """Delete selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to delete")
            return
        
        username = self.user_listbox.get(selection[0]).split(' (Admin)')[0]
        
        if username == self.current_user['username']:
            messagebox.showerror("Error", "You cannot delete your own account")
            return
        
        if messagebox.askyesno("Delete User", f"Are you sure you want to delete user '{username}'?"):
            self.cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            self.conn.commit()
            messagebox.showinfo("Success", "User deleted successfully!")
            self.load_users()
    
    def reset_password(self):
        """Reset user password"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to reset password")
            return
        
        username = self.user_listbox.get(selection[0]).split(' (Admin)')[0]
        
        new_pin = simpledialog.askstring("Reset Password", f"Enter new 4-digit PIN for {username}:")
        if new_pin and len(new_pin) == 4 and new_pin.isdigit():
            self.cursor.execute('UPDATE users SET pin = ? WHERE username = ?', (new_pin, username))
            self.conn.commit()
            messagebox.showinfo("Success", f"Password reset for {username}")
        elif new_pin:
            messagebox.showerror("Error", "PIN must be exactly 4 digits")
    
    def configure_prices(self):
        """Configure system prices"""
        messagebox.showinfo("Price Configuration", 
                           "Price configuration feature would be implemented here.\n"
                           "This would allow admins to modify pizza, topping, and drink prices.")
    
    def view_orders(self):
        """View order history"""
        self.cursor.execute('''
            SELECT o.id, u.username, o.total, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT 50
        ''')
        orders = self.cursor.fetchall()
        
        if not orders:
            messagebox.showinfo("No Orders", "No orders found in the system.")
            return
        
        # Create orders window
        orders_window = tk.Toplevel(self.root)
        orders_window.title("Order History")
        orders_window.geometry("600x400")
        
        # Orders list
        orders_frame = tk.Frame(orders_window)
        orders_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Headers
        headers = ["Order ID", "User", "Total", "Date"]
        for i, header in enumerate(headers):
            tk.Label(orders_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=i, padx=5, pady=5)
        
        # Order rows
        for row, (order_id, username, total, created_at) in enumerate(orders, 1):
            tk.Label(orders_frame, text=str(order_id)).grid(row=row, column=0, padx=5, pady=2)
            tk.Label(orders_frame, text=username).grid(row=row, column=1, padx=5, pady=2)
            tk.Label(orders_frame, text=f"${total:.2f}").grid(row=row, column=2, padx=5, pady=2)
            tk.Label(orders_frame, text=created_at).grid(row=row, column=3, padx=5, pady=2)
    
    def logout(self):
        """Logout and return to login screen"""
        self.current_user = None
        self.cart = []
        self.show_login()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.conn.close()

if __name__ == "__main__":
    app = PizzaPOSApp()
    app.run()

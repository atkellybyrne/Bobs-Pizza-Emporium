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
        
        # Initialize prices (will be loaded from database)
        self.pizza_prices = {}
        self.topping_prices = {}
        self.drink_prices = {}
        self.tax_rate = Decimal('0.08')
        
        # Load prices from database
        self.load_prices_from_database()
        
        # Show login screen
        self.show_login()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        # Get a writable path for the database
        # Use user's AppData directory on Windows, or current directory if writable
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA')
            if appdata:
                db_dir = os.path.join(appdata, 'BobsPizzaEmporium')
                os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, 'pizza_pos.db')
            else:
                # Fallback to current directory
                db_path = 'pizza_pos.db'
        else:
            # For macOS/Linux, use user's home directory
            home = os.path.expanduser('~')
            db_dir = os.path.join(home, '.bobs_pizza_emporium')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'pizza_pos.db')
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                pin TEXT NOT NULL,
                name TEXT,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add name column if it doesn't exist (for existing databases)
        try:
            self.cursor.execute('ALTER TABLE users ADD COLUMN name TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
        
        # Create cart persistence table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_carts (
                user_id INTEGER PRIMARY KEY,
                cart_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create prices table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                size TEXT,
                price DECIMAL(10,2) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, item_name, size)
            )
        ''')
        
        # Add size column if it doesn't exist (for existing databases)
        try:
            self.cursor.execute('ALTER TABLE prices ADD COLUMN size TEXT')
            # Update unique constraint
            self.cursor.execute('DROP INDEX IF EXISTS prices_category_item_name')
        except sqlite3.OperationalError:
            pass  # Column already exists or constraint already updated
        
        # Create default admin user if not exists (PIN: 1234)
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE pin = ?', ('1234',))
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO users (username, pin, name, is_admin) 
                VALUES ('1234', '1234', 'Admin', 1)
            ''')
        
        # Create default regular user if not exists (PIN: 5678)
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE pin = ?', ('5678',))
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO users (username, pin, name, is_admin) 
                VALUES ('5678', '5678', 'Employee', 0)
            ''')
        
        # Initialize default prices if not exists
        self.init_default_prices()
        
        self.conn.commit()
    
    def init_default_prices(self):
        """Initialize default prices in database if they don't exist"""
        # Default pizza prices
        default_pizza = [
            ('pizza', 'small', '12.99'),
            ('pizza', 'medium', '15.99'),
            ('pizza', 'large', '18.99')
        ]
        
        # Default topping prices (size-based)
        default_toppings = []
        toppings_list = ['Pepperoni', 'Sausage', 'Bacon', 'Pineapple', 'Mushrooms', 'Onions']
        # Small: base price, Medium: +0.25, Large: +0.50
        base_prices = {'Pepperoni': 1.00, 'Sausage': 1.00, 'Bacon': 1.50, 'Pineapple': 0.75, 'Mushrooms': 0.75, 'Onions': 0.75}
        for topping in toppings_list:
            base = base_prices[topping]
            default_toppings.extend([
                ('topping', topping, 'small', str(base)),
                ('topping', topping, 'medium', str(base + 0.25)),
                ('topping', topping, 'large', str(base + 0.50))
            ])
        
        # Default drink prices
        default_drinks = [
            ('drink', 'Coca-Cola', '2.50'),
            ('drink', 'Pepsi', '2.50'),
            ('drink', 'Sprite', '2.50'),
            ('drink', 'Water', '1.50'),
            ('drink', 'Orange Juice', '3.00')
        ]
        
        # Default tax rate
        default_tax = [('tax', 'rate', '0.08')]
        
        # Insert all defaults
        all_defaults = default_pizza + default_toppings + default_drinks + default_tax
        
        for item in all_defaults:
            if len(item) == 3:
                # Old format: (category, item_name, price) - for pizza, drinks, tax
                category, item_name, price = item
                self.cursor.execute('''
                    INSERT OR IGNORE INTO prices (category, item_name, size, price)
                    VALUES (?, ?, NULL, ?)
                ''', (category, item_name, price))
            elif len(item) == 4:
                # New format: (category, item_name, size, price) - for toppings
                category, item_name, size, price = item
                self.cursor.execute('''
                    INSERT OR IGNORE INTO prices (category, item_name, size, price)
                    VALUES (?, ?, ?, ?)
                ''', (category, item_name, size, price))
    
    def load_prices_from_database(self):
        """Load prices from database"""
        # Load pizza prices
        self.cursor.execute('SELECT item_name, price FROM prices WHERE category = ? AND size IS NULL', ('pizza',))
        pizza_data = self.cursor.fetchall()
        self.pizza_prices = {}
        for size, price in pizza_data:
            self.pizza_prices[size] = Decimal(str(price))
        
        # Load topping prices (size-based)
        self.cursor.execute('SELECT item_name, size, price FROM prices WHERE category = ? AND size IS NOT NULL', ('topping',))
        topping_data = self.cursor.fetchall()
        self.topping_prices = {}  # Structure: {topping_name: {size: price}}
        for name, size, price in topping_data:
            if name not in self.topping_prices:
                self.topping_prices[name] = {}
            self.topping_prices[name][size] = Decimal(str(price))
        
        # Load drink prices
        self.cursor.execute('SELECT item_name, price FROM prices WHERE category = ?', ('drink',))
        drink_data = self.cursor.fetchall()
        self.drink_prices = {}
        for name, price in drink_data:
            self.drink_prices[name] = Decimal(str(price))
        
        # Load tax rate
        self.cursor.execute('SELECT price FROM prices WHERE category = ? AND item_name = ?', ('tax', 'rate'))
        tax_data = self.cursor.fetchone()
        if tax_data:
            self.tax_rate = Decimal(str(tax_data[0]))
        else:
            self.tax_rate = Decimal('0.08')  # Default 8%
    
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
        
        # PIN
        tk.Label(form_frame, text="Enter 4-Digit PIN:", font=('Arial', 14, 'bold'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', pady=(0,10))
        self.pin_entry = tk.Entry(form_frame, font=('Arial', 16), width=20, show='*',
                                 relief='solid', bd=2, bg=self.colors['bg_primary'],
                                 fg=self.colors['text_primary'], justify='center')
        self.pin_entry.pack(pady=10)
        
        # Login button with rounded styling
        login_btn = tk.Button(form_frame, text="Login", font=('Arial', 14, 'bold'),
                             bg=self.colors['bg_button'], fg=self.colors['text_button'], 
                             width=15, relief='raised', bd=3, padx=25, pady=12,
                             activebackground=self.colors['bg_button_hover'],
                             activeforeground=self.colors['text_button'],
                             command=self.login)
        login_btn.pack(pady=20)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.login())
        self.pin_entry.focus()
    
    def login(self):
        """Handle login authentication"""
        pin = self.pin_entry.get().strip()
        
        if not pin:
            messagebox.showerror("Error", "Please enter a PIN")
            return
        
        if len(pin) != 4 or not pin.isdigit():
            messagebox.showerror("Error", "PIN must be exactly 4 digits")
            self.pin_entry.delete(0, tk.END)
            return
        
        # Check credentials by PIN only
        self.cursor.execute('''
            SELECT id, pin, name, is_admin FROM users 
            WHERE pin = ?
        ''', (pin,))
        
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = {
                'id': user[0],
                'pin': user[1],
                'name': user[2] if user[2] else f"PIN {user[1]}",  # Use name or fallback to PIN
                'is_admin': bool(user[3])
            }
            # Load saved cart for this user
            self.load_user_cart()
            self.show_main_screen()
        else:
            messagebox.showerror("Error", "Invalid PIN")
            self.pin_entry.delete(0, tk.END)
    
    
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
        user_type = "Admin" if self.current_user['is_admin'] else "Employee"
        user_name = self.current_user.get('name', f"PIN {self.current_user['pin']}")
        user_label = tk.Label(header_frame, text=f"{user_name} (PIN: {self.current_user['pin']}) - {user_type}", 
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
        """Add standard pizza to cart with size selection dialog"""
        # Create size selection dialog
        size_dialog = tk.Toplevel(self.root)
        size_dialog.title("Select Pizza Size")
        dialog_width = 700
        dialog_height = 600
        size_dialog.geometry(f"{dialog_width}x{dialog_height}")
        size_dialog.configure(bg=self.colors['bg_primary'])
        size_dialog.transient(self.root)
        size_dialog.grab_set()
        
        # Center the dialog
        size_dialog.update_idletasks()
        x = (size_dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (size_dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        size_dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Main container frame - everything in one frame
        main_container = tk.Frame(size_dialog, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Title
        title_label = tk.Label(main_container, text=f"Select Size for {pizza_name}", 
                              font=('Arial', 20, 'bold'), bg=self.colors['bg_primary'], 
                              fg=self.colors['text_primary'])
        title_label.pack(pady=(0, 25))
        
        # Size selection frame - fixed height, no expand
        size_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        size_frame.pack(fill='x', pady=10)
        
        selected_size = tk.StringVar(value="medium")
        size_buttons = {}
        
        # Create size buttons
        sizes = ['small', 'medium', 'large']
        size_icons = ['●', '●●', '●●●']
        
        for i, size in enumerate(sizes):
            size_container = tk.Frame(size_frame, bg=self.colors['bg_primary'])
            size_container.pack(pady=15, padx=20, fill='x')
            
            size_btn = tk.Radiobutton(size_container, 
                                     text=f"{size_icons[i]} {size.title()} - ${self.pizza_prices[size]}",
                                     font=('Arial', 16, 'bold'),
                                     variable=selected_size,
                                     value=size,
                                     bg=self.colors['bg_secondary'],
                                     fg=self.colors['text_primary'],
                                     selectcolor=self.colors['bg_button'],
                                     activebackground=self.colors['bg_secondary'],
                                     activeforeground=self.colors['text_primary'],
                                     indicatoron=1,
                                     width=40,
                                     height=3,
                                     relief='raised',
                                     bd=4)
            size_btn.pack(fill='x', expand=True)
            size_buttons[size] = size_btn
        
        # Separator line
        separator = tk.Frame(main_container, height=2, bg=self.colors['border_dark'])
        separator.pack(fill='x', pady=20)
        
        # Action buttons frame - always visible at bottom
        button_frame = tk.Frame(main_container, bg=self.colors['bg_secondary'], relief='raised', bd=3)
        button_frame.pack(fill='x', pady=(10, 0))
        
        def add_to_cart():
            """Add pizza to cart with selected size"""
            size = selected_size.get()
            if size in self.pizza_prices:
                price = self.pizza_prices[size]
                item = {
                    'type': 'pizza',
                    'name': f"{pizza_name} ({size.title()})",
                    'price': price,
                    'size': size
                }
                self.cart.append(item)
                self.update_cart_display()
                self.save_user_cart()  # Save cart when item is added
                size_dialog.destroy()
                messagebox.showinfo("Added", f"{pizza_name} ({size.title()}) added to cart!")
        
        # Inner button container for better spacing
        inner_button_frame = tk.Frame(button_frame, bg=self.colors['bg_secondary'])
        inner_button_frame.pack(pady=15, padx=15)
        
        tk.Button(inner_button_frame, text="Add to Cart", font=('Arial', 14, 'bold'),
                 bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                 relief='raised', bd=3, command=add_to_cart,
                 activebackground=self.colors['bg_success'],
                 activeforeground=self.colors['text_button'],
                 padx=30, pady=12, width=15).pack(side='right', padx=10)
        
        tk.Button(inner_button_frame, text="Cancel", font=('Arial', 14, 'bold'),
                 bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                 relief='raised', bd=3, command=size_dialog.destroy,
                 activebackground=self.colors['bg_danger'],
                 activeforeground=self.colors['text_button'],
                 padx=30, pady=12, width=15).pack(side='right', padx=10)
    
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
        
        # Back button in header
        back_btn_header = tk.Button(header_frame, text="← Back to Menu", font=('Arial', 12, 'bold'),
                                    bg=self.colors['bg_warning'], fg=self.colors['text_button'], 
                                    relief='raised', bd=2, command=dialog.destroy,
                                    activebackground=self.colors['bg_warning'],
                                    activeforeground=self.colors['text_button'],
                                    padx=15, pady=8)
        back_btn_header.pack(side='right', padx=10, pady=15)
        
        # PIN display
        pin_label = tk.Label(header_frame, text=f"PIN: {self.current_user['pin']}", 
                                 font=('Arial', 16, 'bold'), bg=self.colors['bg_primary'], 
                                 fg=self.colors['text_primary'])
        pin_label.pack(side='right', padx=20, pady=15)
        
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
        
        # Initialize topping prices display for default size
        self.update_topping_prices_display()
        
        # Add to Order button
        add_to_order_btn = tk.Button(sidebar_frame, text="Add to Order", font=('Arial', 14, 'bold'),
                                   bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                                   relief='raised', bd=3, command=lambda: self.add_pizza_to_order(dialog),
                                   activebackground=self.colors['bg_success'],
                                   activeforeground=self.colors['text_button'],
                                   padx=15, pady=10)
        add_to_order_btn.pack(pady=15)
        
        # Back to Menu button in sidebar
        back_btn_sidebar = tk.Button(sidebar_frame, text="← Back to Menu", font=('Arial', 12, 'bold'),
                                     bg=self.colors['bg_warning'], fg=self.colors['text_button'], 
                                     relief='raised', bd=2, command=dialog.destroy,
                                     activebackground=self.colors['bg_warning'],
                                     activeforeground=self.colors['text_button'],
                                     padx=15, pady=10)
        back_btn_sidebar.pack(pady=10)
        
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
        
        # Topping icons based on the image descriptions
        topping_icons = {
            'Pepperoni': '🍕',      # Red-brown pepperoni slices
            'Bacon': '🥓',           # Wavy bacon strip
            'Mushrooms': '🍄',       # Mushroom cap
            'Onions': '🧅',          # Purple onion
            'Sausage': '🌭',         # Sausage link
            'Pineapple': '🍍'        # Pineapple chunk
        }
        
        # Store price labels for updating when size changes
        self.topping_price_labels = {}
        
        for i, topping in enumerate(toppings):
            row = i // 2
            col = i % 2
            
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
            topping_label.pack(pady=(0, 2))
            
            # Price label (will update based on size)
            price_label = tk.Label(topping_frame, text="", 
                                  font=('Arial', 9), bg=self.colors['topping_bg'], 
                                  fg=self.colors['text_secondary'])
            price_label.pack(pady=(0, 5))
            self.topping_price_labels[topping] = price_label
            
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
        
    
    def select_size(self, size):
        """Select pizza size and update visual feedback"""
        self.selected_size.set(size)
        # Reset all buttons to default color
        for s, btn in self.size_buttons.items():
            btn.config(bg=self.colors['bg_secondary'])
        # Highlight selected size
        self.size_buttons[size].config(bg=self.colors['bg_button'])
        # Update topping prices display
        self.update_topping_prices_display()
        self.update_current_pizza_display()
    
    def update_topping_prices_display(self):
        """Update price labels for toppings based on selected size"""
        size = self.selected_size.get()
        for topping, price_label in self.topping_price_labels.items():
            if topping in self.topping_prices and size in self.topping_prices[topping]:
                price = self.topping_prices[topping][size]
                price_label.config(text=f"${price:.2f}")
            else:
                price_label.config(text="")
    
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
        
        # Group toppings by name and calculate total price (size-based)
        topping_groups = {}
        for topping, count in self.selected_toppings.items():
            if count > 0:
                topping_groups[topping] = count
                # Add topping price for each quantity (using size-based pricing)
                if topping in self.topping_prices and size in self.topping_prices[topping]:
                    for _ in range(count):
                        topping_price += self.topping_prices[topping][size]
        
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
        self.save_user_cart()  # Save cart when item is added
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
        self.save_user_cart()  # Save cart when item is added
    
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
            self.save_user_cart()  # Save cart when item is removed
    
    def clear_cart(self):
        """Clear entire cart"""
        if messagebox.askyesno("Clear Cart", "Are you sure you want to clear the cart?"):
            self.cart = []
            self.update_cart_display()
            self.save_user_cart()  # Save empty cart
    
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
            
            # Clear cart after processing
            self.cart = []
            self.update_cart_display()
            self.save_user_cart()  # Save empty cart after order is processed
    
    def load_users(self):
        """Load users for admin view"""
        self.user_listbox.delete(0, tk.END)
        self.cursor.execute('SELECT pin, name, is_admin FROM users ORDER BY pin')
        users = self.cursor.fetchall()
        
        for pin, name, is_admin in users:
            admin_text = " (Admin)" if is_admin else ""
            display_name = name if name else f"PIN {pin}"
            self.user_listbox.insert(tk.END, f"{display_name} - PIN: {pin}{admin_text}")
    
    def add_user(self):
        """Add new user"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add User")
        dialog.geometry("300x220")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Name
        tk.Label(dialog, text="Name:", font=('Arial', 10, 'bold'), 
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        name_entry = tk.Entry(dialog, font=('Arial', 10), width=20,
                            relief='solid', bd=1, bg=self.colors['bg_primary'],
                            fg=self.colors['text_primary'])
        name_entry.pack(padx=10, pady=5)
        
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
            name = name_entry.get().strip()
            pin = pin_entry.get().strip()
            
            if not pin:
                messagebox.showerror("Error", "Please enter a PIN")
                return
            
            if len(pin) != 4 or not pin.isdigit():
                messagebox.showerror("Error", "PIN must be exactly 4 digits")
                return
            
            # Check if PIN already exists
            self.cursor.execute('SELECT COUNT(*) FROM users WHERE pin = ?', (pin,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", "This PIN is already in use")
                return
            
            try:
                # Use PIN as username for database compatibility (username column still exists)
                # Name is optional - use empty string if not provided
                self.cursor.execute('''
                    INSERT INTO users (username, pin, name, is_admin)
                    VALUES (?, ?, ?, ?)
                ''', (pin, pin, name if name else None, int(is_admin_var.get())))
                self.conn.commit()
                messagebox.showinfo("Success", "User added successfully!")
                dialog.destroy()
                self.load_users()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This PIN is already in use")
        
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
        
        # Parse the selected user - format is "Name - PIN: XXXX (Admin)" or "PIN: XXXX (Admin)"
        selected_text = self.user_listbox.get(selection[0])
        # Extract PIN from the text
        if "PIN: " in selected_text:
            old_pin = selected_text.split("PIN: ")[1].split(" (")[0].split(")")[0].strip()
        else:
            old_pin = selected_text.split(" - ")[-1].replace("PIN: ", "").split(" (")[0].strip()
        
        # Get user data
        self.cursor.execute('SELECT pin, name, is_admin FROM users WHERE pin = ?', (old_pin,))
        user_data = self.cursor.fetchone()
        
        if not user_data:
            messagebox.showerror("Error", "User not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit User")
        dialog.geometry("300x220")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Name
        tk.Label(dialog, text="Name:", font=('Arial', 10, 'bold'), 
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        name_entry = tk.Entry(dialog, font=('Arial', 10), width=20,
                            relief='solid', bd=1, bg=self.colors['bg_primary'],
                            fg=self.colors['text_primary'])
        name_entry.insert(0, user_data[1] if user_data[1] else "")
        name_entry.pack(padx=10, pady=5)
        
        # PIN
        tk.Label(dialog, text="4-Digit PIN:", font=('Arial', 10, 'bold'), 
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        pin_entry = tk.Entry(dialog, font=('Arial', 10), width=20, show='*',
                            relief='solid', bd=1, bg=self.colors['bg_primary'],
                            fg=self.colors['text_primary'])
        pin_entry.insert(0, user_data[0])
        pin_entry.pack(padx=10, pady=5)
        
        # Admin checkbox
        is_admin_var = tk.BooleanVar(value=bool(user_data[2]))
        admin_check = tk.Checkbutton(dialog, text="Administrator", variable=is_admin_var, 
                                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        admin_check.pack(anchor='w', padx=10, pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        button_frame.pack(fill='x', padx=10, pady=10)
        
        def save_changes():
            name = name_entry.get().strip()
            new_pin = pin_entry.get().strip()
            
            if not new_pin:
                messagebox.showerror("Error", "Please enter a PIN")
                return
            
            if len(new_pin) != 4 or not new_pin.isdigit():
                messagebox.showerror("Error", "PIN must be exactly 4 digits")
                return
            
            # Check if new PIN is already in use by another user
            if new_pin != old_pin:
                self.cursor.execute('SELECT COUNT(*) FROM users WHERE pin = ?', (new_pin,))
                if self.cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "This PIN is already in use")
                    return
            
            try:
                # Update name, PIN and admin status, use PIN as username for compatibility
                self.cursor.execute('''
                    UPDATE users SET username = ?, pin = ?, name = ?, is_admin = ?
                    WHERE pin = ?
                ''', (new_pin, new_pin, name if name else None, int(is_admin_var.get()), old_pin))
                self.conn.commit()
                messagebox.showinfo("Success", "User updated successfully!")
                dialog.destroy()
                self.load_users()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This PIN is already in use")
        
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
        
        # Parse the selected user - format is "Name - PIN: XXXX (Admin)" or "PIN: XXXX (Admin)"
        selected_text = self.user_listbox.get(selection[0])
        if "PIN: " in selected_text:
            pin = selected_text.split("PIN: ")[1].split(" (")[0].split(")")[0].strip()
        else:
            pin = selected_text.split(" - ")[-1].replace("PIN: ", "").split(" (")[0].strip()
        
        if pin == self.current_user['pin']:
            messagebox.showerror("Error", "You cannot delete your own account")
            return
        
        # Get user name for confirmation message
        self.cursor.execute('SELECT name FROM users WHERE pin = ?', (pin,))
        user_name = self.cursor.fetchone()
        display_name = user_name[0] if user_name and user_name[0] else f"PIN {pin}"
        
        if messagebox.askyesno("Delete User", f"Are you sure you want to delete user '{display_name}' (PIN: {pin})?"):
            self.cursor.execute('DELETE FROM users WHERE pin = ?', (pin,))
            self.conn.commit()
            messagebox.showinfo("Success", "User deleted successfully!")
            self.load_users()
    
    def reset_password(self):
        """Reset user PIN"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to reset PIN")
            return
        
        # Parse the selected user - format is "Name - PIN: XXXX (Admin)" or "PIN: XXXX (Admin)"
        selected_text = self.user_listbox.get(selection[0])
        if "PIN: " in selected_text:
            old_pin = selected_text.split("PIN: ")[1].split(" (")[0].split(")")[0].strip()
        else:
            old_pin = selected_text.split(" - ")[-1].replace("PIN: ", "").split(" (")[0].strip()
        
        # Get user name for dialog message
        self.cursor.execute('SELECT name FROM users WHERE pin = ?', (old_pin,))
        user_name = self.cursor.fetchone()
        display_name = user_name[0] if user_name and user_name[0] else f"PIN {old_pin}"
        
        new_pin = simpledialog.askstring("Reset PIN", f"Enter new 4-digit PIN for '{display_name}' (current PIN: {old_pin}):")
        if new_pin and len(new_pin) == 4 and new_pin.isdigit():
            # Check if new PIN is already in use
            if new_pin != old_pin:
                self.cursor.execute('SELECT COUNT(*) FROM users WHERE pin = ?', (new_pin,))
                if self.cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "This PIN is already in use")
                    return
            self.cursor.execute('UPDATE users SET pin = ?, username = ? WHERE pin = ?', (new_pin, new_pin, old_pin))
            self.conn.commit()
            messagebox.showinfo("Success", f"PIN reset for user with PIN {old_pin}")
        elif new_pin:
            messagebox.showerror("Error", "PIN must be exactly 4 digits")
    
    def configure_prices(self):
        """Configure system prices"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Prices")
        dialog.geometry("800x700")
        dialog.configure(bg=self.colors['bg_primary'])
        
        # Main scrollable frame
        main_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="Price Configuration", 
                              font=('Arial', 18, 'bold'), bg=self.colors['bg_primary'], 
                              fg=self.colors['text_primary'])
        title_label.pack(pady=(0, 20))
        
        # Create a canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_frame, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Price entry fields storage
        price_entries = {}
        
        # Pizza Prices Section
        pizza_frame = tk.LabelFrame(scrollable_frame, text="Pizza Prices", 
                                    font=('Arial', 12, 'bold'), bg=self.colors['bg_primary'],
                                    fg=self.colors['text_primary'], relief='solid', bd=1)
        pizza_frame.pack(fill='x', padx=10, pady=10)
        
        pizza_inner = tk.Frame(pizza_frame, bg=self.colors['bg_primary'])
        pizza_inner.pack(fill='x', padx=10, pady=10)
        
        for size in ['small', 'medium', 'large']:
            row = tk.Frame(pizza_inner, bg=self.colors['bg_primary'])
            row.pack(fill='x', pady=5)
            
            tk.Label(row, text=f"{size.title()} Pizza:", font=('Arial', 10, 'bold'),
                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=15, anchor='w').pack(side='left')
            tk.Label(row, text="$", font=('Arial', 10), bg=self.colors['bg_primary'],
                    fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
            
            entry = tk.Entry(row, font=('Arial', 10), width=10, relief='solid', bd=1,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
            entry.insert(0, str(self.pizza_prices.get(size, '0.00')))
            entry.pack(side='left')
            price_entries[('pizza', size)] = entry
        
        # Topping Prices Section (size-based)
        topping_frame = tk.LabelFrame(scrollable_frame, text="Topping Prices (by Size)", 
                                      font=('Arial', 12, 'bold'), bg=self.colors['bg_primary'],
                                      fg=self.colors['text_primary'], relief='solid', bd=1)
        topping_frame.pack(fill='x', padx=10, pady=10)
        
        topping_inner = tk.Frame(topping_frame, bg=self.colors['bg_primary'])
        topping_inner.pack(fill='x', padx=10, pady=10)
        
        # Get unique topping names
        topping_names = sorted(set(self.topping_prices.keys()))
        sizes = ['small', 'medium', 'large']
        
        for topping in topping_names:
            # Topping name header
            topping_header = tk.Label(topping_inner, text=f"{topping}:", 
                                    font=('Arial', 10, 'bold'),
                                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
            topping_header.pack(anchor='w', pady=(10, 5))
            
            # Size-based price entries
            size_row = tk.Frame(topping_inner, bg=self.colors['bg_primary'])
            size_row.pack(fill='x', pady=2)
            
            for size in sizes:
                tk.Label(size_row, text=f"{size.title()}:", font=('Arial', 9),
                        bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=8, anchor='w').pack(side='left', padx=(20, 2))
                tk.Label(size_row, text="$", font=('Arial', 9), bg=self.colors['bg_primary'],
                        fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
                
                entry = tk.Entry(size_row, font=('Arial', 9), width=8, relief='solid', bd=1,
                               bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
                # Get price for this topping and size
                price = '0.00'
                if topping in self.topping_prices and size in self.topping_prices[topping]:
                    price = str(self.topping_prices[topping][size])
                entry.insert(0, price)
                entry.pack(side='left', padx=2)
                price_entries[('topping', topping, size)] = entry
        
        # Drink Prices Section
        drink_frame = tk.LabelFrame(scrollable_frame, text="Drink Prices", 
                                   font=('Arial', 12, 'bold'), bg=self.colors['bg_primary'],
                                   fg=self.colors['text_primary'], relief='solid', bd=1)
        drink_frame.pack(fill='x', padx=10, pady=10)
        
        drink_inner = tk.Frame(drink_frame, bg=self.colors['bg_primary'])
        drink_inner.pack(fill='x', padx=10, pady=10)
        
        for drink in sorted(self.drink_prices.keys()):
            row = tk.Frame(drink_inner, bg=self.colors['bg_primary'])
            row.pack(fill='x', pady=5)
            
            tk.Label(row, text=f"{drink}:", font=('Arial', 10, 'bold'),
                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=15, anchor='w').pack(side='left')
            tk.Label(row, text="$", font=('Arial', 10), bg=self.colors['bg_primary'],
                    fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
            
            entry = tk.Entry(row, font=('Arial', 10), width=10, relief='solid', bd=1,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
            entry.insert(0, str(self.drink_prices.get(drink, '0.00')))
            entry.pack(side='left')
            price_entries[('drink', drink)] = entry
        
        # Tax Rate Section
        tax_frame = tk.LabelFrame(scrollable_frame, text="Tax Rate", 
                                 font=('Arial', 12, 'bold'), bg=self.colors['bg_primary'],
                                 fg=self.colors['text_primary'], relief='solid', bd=1)
        tax_frame.pack(fill='x', padx=10, pady=10)
        
        tax_inner = tk.Frame(tax_frame, bg=self.colors['bg_primary'])
        tax_inner.pack(fill='x', padx=10, pady=10)
        
        tax_row = tk.Frame(tax_inner, bg=self.colors['bg_primary'])
        tax_row.pack(fill='x', pady=5)
        
        tk.Label(tax_row, text="Tax Rate (decimal):", font=('Arial', 10, 'bold'),
                bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=15, anchor='w').pack(side='left')
        tk.Label(tax_row, text="", font=('Arial', 10), bg=self.colors['bg_primary'],
                fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
        
        tax_entry = tk.Entry(tax_row, font=('Arial', 10), width=10, relief='solid', bd=1,
                            bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        tax_entry.insert(0, str(self.tax_rate))
        tax_entry.pack(side='left')
        price_entries[('tax', 'rate')] = tax_entry
        
        tk.Label(tax_row, text=f" (Current: {float(self.tax_rate) * 100:.1f}%)", 
                font=('Arial', 9), bg=self.colors['bg_primary'],
                fg=self.colors['text_secondary']).pack(side='left', padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        button_frame.pack(fill='x', padx=20, pady=20)
        
        def save_prices():
            """Save all prices to database"""
            try:
                errors = []
                
                # Validate and save all prices
                for key, entry in price_entries.items():
                    try:
                        value = entry.get().strip()
                        if not value:
                            if len(key) == 3:  # Topping with size
                                errors.append(f"{key[1]} ({key[2]}): Empty value")
                            else:
                                errors.append(f"{key[1]}: Empty value")
                            continue
                        
                        price_decimal = Decimal(value)
                        if price_decimal < 0:
                            if len(key) == 3:
                                errors.append(f"{key[1]} ({key[2]}): Negative value not allowed")
                            else:
                                errors.append(f"{key[1]}: Negative value not allowed")
                            continue
                        
                        # Update or insert price
                        if len(key) == 3:  # Topping with size
                            category, item_name, size = key
                            self.cursor.execute('''
                                INSERT INTO prices (category, item_name, size, price)
                                VALUES (?, ?, ?, ?)
                                ON CONFLICT(category, item_name, size) DO UPDATE SET
                                    price = excluded.price,
                                    updated_at = CURRENT_TIMESTAMP
                            ''', (category, item_name, size, float(price_decimal)))
                        else:  # Pizza, drink, tax (no size)
                            category, item_name = key
                            self.cursor.execute('''
                                INSERT INTO prices (category, item_name, size, price)
                                VALUES (?, ?, NULL, ?)
                                ON CONFLICT(category, item_name, size) DO UPDATE SET
                                    price = excluded.price,
                                    updated_at = CURRENT_TIMESTAMP
                            ''', (category, item_name, float(price_decimal)))
                        
                    except ValueError:
                        if len(key) == 3:
                            errors.append(f"{key[1]} ({key[2]}): Invalid number format")
                        else:
                            errors.append(f"{key[1]}: Invalid number format")
                    except Exception as e:
                        if len(key) == 3:
                            errors.append(f"{key[1]} ({key[2]}): {str(e)}")
                        else:
                            errors.append(f"{key[1]}: {str(e)}")
                
                if errors:
                    error_msg = "Some prices could not be saved:\n\n" + "\n".join(errors)
                    messagebox.showerror("Save Errors", error_msg)
                    return
                
                self.conn.commit()
                
                # Reload prices
                self.load_prices_from_database()
                
                messagebox.showinfo("Success", 
                                   "Prices updated successfully!\n\n"
                                   "Note: New prices will be applied to all new orders.\n"
                                   "Existing items in carts will use the old prices until the cart is cleared.")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save prices: {str(e)}")
        
        tk.Button(button_frame, text="Save Prices", font=('Arial', 12, 'bold'),
                 bg=self.colors['bg_success'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=save_prices,
                 activebackground=self.colors['bg_success'],
                 activeforeground=self.colors['text_button'],
                 padx=20, pady=10).pack(side='right', padx=10)
        
        tk.Button(button_frame, text="Cancel", font=('Arial', 12),
                 bg=self.colors['bg_danger'], fg=self.colors['text_button'], 
                 relief='raised', bd=2, command=dialog.destroy,
                 activebackground=self.colors['bg_danger'],
                 activeforeground=self.colors['text_button'],
                 padx=20, pady=10).pack(side='right', padx=10)
        
        # Bind mousewheel to canvas (works on Windows and macOS)
        def on_mousewheel(event):
            # Handle both Windows (event.delta) and macOS/Unix (event.delta)
            if event.num == 4 or (hasattr(event, 'delta') and event.delta < 0):
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or (hasattr(event, 'delta') and event.delta > 0):
                canvas.yview_scroll(1, "units")
        
        # Bind for different platforms
        canvas.bind_all("<MouseWheel>", on_mousewheel)  # Windows
        canvas.bind_all("<Button-4>", on_mousewheel)     # macOS/Unix scroll up
        canvas.bind_all("<Button-5>", on_mousewheel)     # macOS/Unix scroll down
    
    def view_orders(self):
        """View order history"""
        self.cursor.execute('''
            SELECT o.id, u.name, u.pin, o.total, o.created_at
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
        orders_window.geometry("700x400")
        
        # Orders list
        orders_frame = tk.Frame(orders_window)
        orders_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Headers
        headers = ["Order ID", "User", "PIN", "Total", "Date"]
        for i, header in enumerate(headers):
            tk.Label(orders_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=i, padx=5, pady=5)
        
        # Order rows
        for row, (order_id, user_name, user_pin, total, created_at) in enumerate(orders, 1):
            display_name = user_name if user_name else f"PIN {user_pin}"
            # Format timestamp properly
            try:
                if isinstance(created_at, str):
                    # Parse SQLite timestamp format
                    dt = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.datetime.fromisoformat(str(created_at))
                formatted_time = dt.strftime('%Y-%m-%d %I:%M %p')
            except:
                formatted_time = str(created_at)
            
            tk.Label(orders_frame, text=str(order_id)).grid(row=row, column=0, padx=5, pady=2)
            tk.Label(orders_frame, text=display_name).grid(row=row, column=1, padx=5, pady=2)
            tk.Label(orders_frame, text=user_pin).grid(row=row, column=2, padx=5, pady=2)
            tk.Label(orders_frame, text=f"${total:.2f}").grid(row=row, column=3, padx=5, pady=2)
            tk.Label(orders_frame, text=formatted_time).grid(row=row, column=4, padx=5, pady=2)
    
    def logout(self):
        """Logout and return to login screen"""
        # Save cart before logging out
        if self.current_user:
            self.save_user_cart()
        self.current_user = None
        self.cart = []
        self.show_login()
    
    def save_user_cart(self):
        """Save current cart for the logged-in user"""
        if not self.current_user:
            return
        import json
        try:
            cart_json = json.dumps(self.cart)
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_carts (user_id, cart_data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (self.current_user['id'], cart_json))
            self.conn.commit()
        except Exception as e:
            print(f"Error saving cart: {e}")
    
    def load_user_cart(self):
        """Load saved cart for the logged-in user"""
        if not self.current_user:
            return
        import json
        try:
            self.cursor.execute('SELECT cart_data FROM user_carts WHERE user_id = ?', (self.current_user['id'],))
            result = self.cursor.fetchone()
            if result and result[0]:
                # Convert price strings back to Decimal
                cart_data = json.loads(result[0])
                self.cart = []
                for item in cart_data:
                    # Convert price back to Decimal if it's a string
                    if 'price' in item:
                        item['price'] = Decimal(str(item['price']))
                    self.cart.append(item)
        except Exception as e:
            print(f"Error loading cart: {e}")
            self.cart = []
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.conn.close()

if __name__ == "__main__":
    app = PizzaPOSApp()
    app.run()

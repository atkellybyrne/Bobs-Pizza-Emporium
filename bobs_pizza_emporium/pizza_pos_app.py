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
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Fix unique constraint issue: SQLite doesn't allow dropping table-level UNIQUE constraints
        # We need to recreate the table if it has the old constraint
        try:
            # Check if table exists and get its schema
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='prices'")
            table_sql = self.cursor.fetchone()
            
            # Check if we need to migrate (old constraint without size, or constraint on category+item_name only)
            needs_migration = False
            if table_sql and table_sql[0]:
                sql_str = table_sql[0].upper()
                # Check if it has UNIQUE constraint on just (category, item_name) without size
                if 'UNIQUE(CATEGORY, ITEM_NAME)' in sql_str or 'UNIQUE(ITEM_NAME, CATEGORY)' in sql_str:
                    if 'UNIQUE(CATEGORY, ITEM_NAME, SIZE)' not in sql_str:
                        needs_migration = True
            
            if needs_migration:
                # Backup existing data
                self.cursor.execute('''
                    CREATE TABLE prices_backup AS 
                    SELECT * FROM prices
                ''')
                
                # Drop old table
                self.cursor.execute('DROP TABLE prices')
                
                # Recreate with correct constraint
                self.cursor.execute('''
                    CREATE TABLE prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        size TEXT,
                        price DECIMAL(10,2) NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(category, item_name, size)
                    )
                ''')
                
                # Restore data (handle case where size column might not exist in backup)
                try:
                    self.cursor.execute('''
                        INSERT INTO prices (category, item_name, size, price, updated_at)
                        SELECT category, item_name, size, price, updated_at FROM prices_backup
                    ''')
                except sqlite3.OperationalError:
                    # If size column doesn't exist in backup, insert without it
                    self.cursor.execute('''
                        INSERT INTO prices (category, item_name, size, price, updated_at)
                        SELECT category, item_name, NULL, price, updated_at FROM prices_backup
                    ''')
                
                # Drop backup table
                self.cursor.execute('DROP TABLE prices_backup')
                self.conn.commit()
                
        except sqlite3.OperationalError as e:
            # If backup table exists from previous failed migration, clean it up
            try:
                self.cursor.execute('DROP TABLE IF EXISTS prices_backup')
                self.conn.commit()
            except:
                pass
        
        # Drop any old indexes
        try:
            self.cursor.execute('DROP INDEX IF EXISTS prices_category_item_name')
        except sqlite3.OperationalError:
            pass
        
        try:
            self.cursor.execute('DROP INDEX IF EXISTS prices_category_item_name_size')
        except sqlite3.OperationalError:
            pass
        
        # Create unique index on (category, item_name, size)
        # This handles NULL values properly
        self.cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS prices_category_item_name_size 
            ON prices(category, item_name, COALESCE(size, ''))
        ''')
        
        # Create carts table for persisting carts per PIN
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cart_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id)
            )
        ''')
        
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
        # Default pizza prices (no size needed, item_name is the size)
        default_pizza = [
            ('pizza', 'small', None, '12.99'),
            ('pizza', 'medium', None, '15.99'),
            ('pizza', 'large', None, '18.99')
        ]
        
        # Default topping prices - different prices per size
        # Small = base price, Medium = 1.2x (20% increase), Large = 1.44x (20% increase from medium)
        default_toppings = [
            # Small size toppings (base prices)
            ('topping', 'Pepperoni', 'small', '1.50'),
            ('topping', 'Sausage', 'small', '1.50'),
            ('topping', 'Bacon', 'small', '2.00'),
            ('topping', 'Pineapple', 'small', '1.00'),
            ('topping', 'Mushrooms', 'small', '1.00'),
            ('topping', 'Onions', 'small', '1.00'),
            # Medium size toppings (20% increase from small)
            ('topping', 'Pepperoni', 'medium', '1.80'),
            ('topping', 'Sausage', 'medium', '1.80'),
            ('topping', 'Bacon', 'medium', '2.40'),
            ('topping', 'Pineapple', 'medium', '1.20'),
            ('topping', 'Mushrooms', 'medium', '1.20'),
            ('topping', 'Onions', 'medium', '1.20'),
            # Large size toppings (20% increase from medium = 44% from small)
            ('topping', 'Pepperoni', 'large', '2.16'),
            ('topping', 'Sausage', 'large', '2.16'),
            ('topping', 'Bacon', 'large', '2.88'),
            ('topping', 'Pineapple', 'large', '1.44'),
            ('topping', 'Mushrooms', 'large', '1.44'),
            ('topping', 'Onions', 'large', '1.44'),
        ]
        
        # Default drink prices (no size)
        default_drinks = [
            ('drink', 'Coca-Cola', None, '2.50'),
            ('drink', 'Pepsi', None, '2.50'),
            ('drink', 'Sprite', None, '2.50'),
            ('drink', 'Water', None, '1.50'),
            ('drink', 'Orange Juice', None, '3.00')
        ]
        
        # Default tax rate (no size)
        default_tax = [('tax', 'rate', None, '0.08')]
        
        # Insert all defaults
        all_defaults = default_pizza + default_toppings + default_drinks + default_tax
        
        for category, item_name, size, price in all_defaults:
            self.cursor.execute('''
                INSERT OR IGNORE INTO prices (category, item_name, size, price)
                VALUES (?, ?, ?, ?)
            ''', (category, item_name, size, price))
        
        # Migrate old topping prices if they exist (without size)
        self.cursor.execute('SELECT item_name, price FROM prices WHERE category = ? AND size IS NULL', ('topping',))
        old_toppings = self.cursor.fetchall()
        if old_toppings:
            # Create size-based prices from old single prices
            for item_name, price in old_toppings:
                price_decimal = Decimal(str(price))
                # Create prices for all sizes based on old price
                for size in ['small', 'medium', 'large']:
                    # Scale prices: small = 0.67x, medium = 1x, large = 1.33x
                    multipliers = {'small': Decimal('0.67'), 'medium': Decimal('1.0'), 'large': Decimal('1.33')}
                    new_price = (price_decimal * multipliers[size]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO prices (category, item_name, size, price)
                        VALUES (?, ?, ?, ?)
                    ''', ('topping', item_name, size, float(new_price)))
                # Delete old price without size
                self.cursor.execute('DELETE FROM prices WHERE category = ? AND item_name = ? AND size IS NULL', 
                                  ('topping', item_name))
    
    def load_prices_from_database(self):
        """Load prices from database"""
        # Load pizza prices
        self.cursor.execute('SELECT item_name, price FROM prices WHERE category = ? AND size IS NULL', ('pizza',))
        pizza_data = self.cursor.fetchall()
        self.pizza_prices = {}
        for size, price in pizza_data:
            self.pizza_prices[size] = Decimal(str(price))
        
        # Load topping prices by size
        self.cursor.execute('SELECT item_name, size, price FROM prices WHERE category = ? AND size IS NOT NULL', ('topping',))
        topping_data = self.cursor.fetchall()
        self.topping_prices = {}
        for name, size, price in topping_data:
            if name not in self.topping_prices:
                self.topping_prices[name] = {}
            # Ensure size is lowercase for consistency
            size_lower = size.lower() if size else None
            self.topping_prices[name][size_lower] = Decimal(str(price))
        
        print(f"DEBUG: Loaded topping prices: {self.topping_prices}")  # Debug line
        
        # If no toppings found with sizes, check for old format and migrate
        if not self.topping_prices:
            self.cursor.execute('SELECT item_name, price FROM prices WHERE category = ? AND size IS NULL', ('topping',))
            old_toppings = self.cursor.fetchall()
            if old_toppings:
                # Migrate old topping prices
                for item_name, price in old_toppings:
                    price_decimal = Decimal(str(price))
                    # Create prices for all sizes based on old price
                    # Use old price as small, then 20% increase for medium, 20% increase for large
                    for size in ['small', 'medium', 'large']:
                        # Scale prices: small = 1x (base), medium = 1.2x (20% increase), large = 1.44x (20% from medium)
                        multipliers = {'small': Decimal('1.0'), 'medium': Decimal('1.2'), 'large': Decimal('1.44')}
                        new_price = (price_decimal * multipliers[size]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO prices (category, item_name, size, price)
                            VALUES (?, ?, ?, ?)
                        ''', ('topping', item_name, size, float(new_price)))
                        if item_name not in self.topping_prices:
                            self.topping_prices[item_name] = {}
                        self.topping_prices[item_name][size] = new_price
                    # Delete old price without size
                    self.cursor.execute('DELETE FROM prices WHERE category = ? AND item_name = ? AND size IS NULL', 
                                      ('topping', item_name))
                self.conn.commit()
        
        # If still no toppings, ensure we have at least the default ones
        if not self.topping_prices:
            # Check if we need to initialize default prices
            self.cursor.execute('SELECT COUNT(*) FROM prices WHERE category = ?', ('topping',))
            topping_count = self.cursor.fetchone()[0]
            if topping_count == 0:
                # No toppings at all, initialize defaults
                self.init_default_prices()
                self.conn.commit()
            # Reload topping prices
            self.cursor.execute('SELECT item_name, size, price FROM prices WHERE category = ? AND size IS NOT NULL', ('topping',))
            topping_data = self.cursor.fetchall()
            for name, size, price in topping_data:
                if name not in self.topping_prices:
                    self.topping_prices[name] = {}
                size_lower = size.lower() if size else None
                self.topping_prices[name][size_lower] = Decimal(str(price))
        
        # Ensure all toppings have prices for all sizes (fix any missing sizes)
        self.ensure_all_topping_sizes()
        
        # Load drink prices
        self.cursor.execute('SELECT item_name, price FROM prices WHERE category = ? AND size IS NULL', ('drink',))
        drink_data = self.cursor.fetchall()
        self.drink_prices = {}
        for name, price in drink_data:
            self.drink_prices[name] = Decimal(str(price))
        
        # Load tax rate
        self.cursor.execute('SELECT price FROM prices WHERE category = ? AND item_name = ? AND size IS NULL', ('tax', 'rate'))
        tax_data = self.cursor.fetchone()
        if tax_data:
            self.tax_rate = Decimal(str(tax_data[0]))
        else:
            self.tax_rate = Decimal('0.08')  # Default 8%
    
    def ensure_all_topping_sizes(self):
        """Ensure all toppings have prices for all three sizes (small, medium, large)"""
        required_sizes = ['small', 'medium', 'large']
        needs_update = False
        
        for topping_name in list(self.topping_prices.keys()):
            topping_sizes = set(self.topping_prices[topping_name].keys())
            missing_sizes = [s for s in required_sizes if s not in topping_sizes]
            
            if missing_sizes:
                # Find a reference price and size (prefer small, then medium, then large)
                reference_price = None
                ref_size = None
                for size in ['small', 'medium', 'large']:
                    if size in self.topping_prices[topping_name]:
                        reference_price = self.topping_prices[topping_name][size]
                        ref_size = size
                        break
                
                if reference_price and ref_size:
                    # Calculate base price (small) from reference size
                    if ref_size == 'small':
                        base_price = reference_price
                    elif ref_size == 'medium':
                        # Medium is 1.2x small, so small = medium / 1.2
                        base_price = reference_price / Decimal('1.2')
                    elif ref_size == 'large':
                        # Large is 1.44x small, so small = large / 1.44
                        base_price = reference_price / Decimal('1.44')
                    else:
                        base_price = None
                    
                    if base_price:
                        # Calculate prices: small = base, medium = 1.2x, large = 1.44x
                        multipliers = {'small': Decimal('1.0'), 'medium': Decimal('1.2'), 'large': Decimal('1.44')}
                        for missing_size in missing_sizes:
                            new_price = (base_price * multipliers[missing_size]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO prices (category, item_name, size, price)
                            VALUES (?, ?, ?, ?)
                        ''', ('topping', topping_name, missing_size, float(new_price)))
                        self.topping_prices[topping_name][missing_size] = new_price
                        needs_update = True
                        print(f"DEBUG: Created missing price for {topping_name} size {missing_size}: ${new_price}")
        
        if needs_update:
            self.conn.commit()
            print("DEBUG: Updated database with missing topping sizes")
    
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
            SELECT id, pin, is_admin FROM users 
            WHERE pin = ?
        ''', (pin,))
        
        user = self.cursor.fetchone()
        
        if user:
            # Get user name if available
            self.cursor.execute('SELECT name FROM users WHERE id = ?', (user[0],))
            name_result = self.cursor.fetchone()
            user_name = name_result[0] if name_result and name_result[0] else None
            
            self.current_user = {
                'id': user[0],
                'pin': user[1],
                'is_admin': bool(user[2]),
                'name': user_name
            }
            # Load saved cart for this user
            self.load_cart_for_user()
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
        user_name = self.current_user.get('name', '')
        display_name = user_name if user_name else f"PIN: {self.current_user['pin']}"
        user_label = tk.Label(header_frame, text=f"{display_name} ({user_type})", 
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
        
        # Update cart display if there are items in cart (from saved cart)
        if self.cart:
            self.update_cart_display()
    
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
        dialog.geometry("1400x900")
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
        
        # Store price labels for updating (initialize before use)
        self.topping_price_labels = {}
        
        # Create topping buttons with +/- controls and icons (like in the image)
        # Ensure topping_prices is initialized
        if not hasattr(self, 'topping_prices') or not isinstance(self.topping_prices, dict):
            self.topping_prices = {}
        
        toppings = list(self.topping_prices.keys())
        print(f"DEBUG: Toppings list: {toppings}")  # Debug line
        
        # If no toppings available, show error message
        if not toppings:
            error_label = tk.Label(toppings_frame, text="No toppings available.\nPlease configure prices in admin settings.", 
                                  font=('Arial', 14), bg=self.colors['bg_secondary'], 
                                  fg=self.colors['text_accent'])
            error_label.pack(expand=True)
            # Still configure grid weights even if empty
            toppings_grid.columnconfigure(0, weight=1)
            toppings_grid.columnconfigure(1, weight=1)
            return
        
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
            topping_label.pack(pady=(0, 2))
            
            # Price label (will be updated based on size)
            # Get initial price for the selected size (medium is default)
            initial_price = ""
            size = self.selected_size.get()  # This should be "medium" by default
            if topping in self.topping_prices and size in self.topping_prices[topping]:
                initial_price = f"${self.topping_prices[topping][size]}"
            
            price_label = tk.Label(topping_frame, text=initial_price, 
                                  font=('Arial', 11, 'bold'), bg=self.colors['topping_bg'], 
                                  fg=self.colors['text_accent'], height=1)
            price_label.pack(pady=(0, 8))
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
        
        # Update price labels based on initial size
        self.update_topping_prices_display()
        
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
        # Update topping price displays
        self.update_topping_prices_display()
        self.update_current_pizza_display()
    
    def update_topping_prices_display(self):
        """Update topping price labels based on selected size"""
        if not hasattr(self, 'topping_price_labels') or not self.topping_price_labels:
            return
        
        if not hasattr(self, 'selected_size'):
            return
        
        size = self.selected_size.get().lower()  # Ensure lowercase for consistency
        print(f"DEBUG: Updating prices for size: {size}")  # Debug line
        
        for topping, price_label in self.topping_price_labels.items():
            if topping in self.topping_prices:
                if size in self.topping_prices[topping]:
                    price = self.topping_prices[topping][size]
                    price_label.config(text=f"${price}")
                    print(f"DEBUG: Updated {topping} price to ${price} for size {size}")  # Debug line
                else:
                    # Calculate the price based on small price if missing
                    # Try to get small price first
                    base_price = None
                    if 'small' in self.topping_prices[topping]:
                        base_price = self.topping_prices[topping]['small']
                    elif 'medium' in self.topping_prices[topping]:
                        # Medium is 1.2x small, so calculate small from medium
                        base_price = self.topping_prices[topping]['medium'] / Decimal('1.2')
                    elif 'large' in self.topping_prices[topping]:
                        # Large is 1.44x small, so calculate small from large
                        base_price = self.topping_prices[topping]['large'] / Decimal('1.44')
                    
                    if base_price:
                        # Calculate price for the requested size
                        multipliers = {'small': Decimal('1.0'), 'medium': Decimal('1.2'), 'large': Decimal('1.44')}
                        if size in multipliers:
                            calculated_price = (base_price * multipliers[size]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                            price_label.config(text=f"${calculated_price}")
                            # Also save it to the dictionary and database for future use
                            self.topping_prices[topping][size] = calculated_price
                            self.cursor.execute('''
                                INSERT OR REPLACE INTO prices (category, item_name, size, price)
                                VALUES (?, ?, ?, ?)
                            ''', ('topping', topping, size, float(calculated_price)))
                            self.conn.commit()
                            print(f"DEBUG: Calculated and saved {topping} price ${calculated_price} for size {size}")  # Debug line
                        else:
                            price_label.config(text="")
                    else:
                        price_label.config(text="")
                        print(f"DEBUG: No base price found for {topping}")  # Debug line
            else:
                price_label.config(text="")
                print(f"DEBUG: {topping} not found in topping_prices")  # Debug line
    
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
                # Add topping price for each quantity using size-based pricing
                if topping in self.topping_prices and size in self.topping_prices[topping]:
                    topping_price_per_unit = self.topping_prices[topping][size]
                    topping_price += topping_price_per_unit * Decimal(str(count))
        
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
            
            # Clear cart and remove saved cart from database
            self.cart = []
            self.cursor.execute('DELETE FROM carts WHERE user_id = ?', (self.current_user['id'],))
            self.conn.commit()
            self.update_cart_display()
    
    def load_users(self):
        """Load users for admin view"""
        self.user_listbox.delete(0, tk.END)
        self.cursor.execute('SELECT pin, COALESCE(name, pin) as name, is_admin FROM users ORDER BY pin')
        users = self.cursor.fetchall()
        
        for pin, name, is_admin in users:
            admin_text = " (Admin)" if is_admin else ""
            display_name = name if name and name != pin else f"PIN: {pin}"
            self.user_listbox.insert(tk.END, f"{display_name}{admin_text}")
    
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
                # Use name if provided, otherwise use PIN
                display_name = name if name else None
                self.cursor.execute('''
                    INSERT INTO users (username, pin, name, is_admin)
                    VALUES (?, ?, ?, ?)
                ''', (pin, pin, display_name, int(is_admin_var.get())))
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
        
        user_text = self.user_listbox.get(selection[0]).split(' (Admin)')[0]
        # Extract PIN from display text (could be "Name" or "PIN: 1234")
        if user_text.startswith('PIN: '):
            old_pin = user_text.replace('PIN: ', '').strip()
        else:
            # Find user by name
            self.cursor.execute('SELECT pin FROM users WHERE name = ?', (user_text,))
            result = self.cursor.fetchone()
            if result:
                old_pin = result[0]
            else:
                old_pin = user_text  # Fallback
        
        # Get user data
        self.cursor.execute('SELECT pin, COALESCE(name, pin) as name, is_admin FROM users WHERE pin = ?', (old_pin,))
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
        name_entry.insert(0, user_data[1] if user_data[1] != user_data[0] else '')
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
            new_name = name_entry.get().strip()
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
                display_name = new_name if new_name else None
                self.cursor.execute('''
                    UPDATE users SET username = ?, pin = ?, name = ?, is_admin = ?
                    WHERE pin = ?
                ''', (new_pin, new_pin, display_name, int(is_admin_var.get()), old_pin))
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
        
        user_text = self.user_listbox.get(selection[0]).split(' (Admin)')[0]
        # Extract PIN from display text
        if user_text.startswith('PIN: '):
            pin = user_text.replace('PIN: ', '').strip()
        else:
            # Find user by name
            self.cursor.execute('SELECT pin FROM users WHERE name = ?', (user_text,))
            result = self.cursor.fetchone()
            if result:
                pin = result[0]
            else:
                pin = user_text  # Fallback
        
        if pin == self.current_user['pin']:
            messagebox.showerror("Error", "You cannot delete your own account")
            return
        
        if messagebox.askyesno("Delete User", f"Are you sure you want to delete user '{user_text}'?"):
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
        
        user_text = self.user_listbox.get(selection[0]).split(' (Admin)')[0]
        # Extract PIN from display text
        if user_text.startswith('PIN: '):
            old_pin = user_text.replace('PIN: ', '').strip()
        else:
            # Find user by name
            self.cursor.execute('SELECT pin FROM users WHERE name = ?', (user_text,))
            result = self.cursor.fetchone()
            if result:
                old_pin = result[0]
            else:
                old_pin = user_text  # Fallback
        
        new_pin = simpledialog.askstring("Reset PIN", f"Enter new 4-digit PIN for user '{user_text}':")
        if new_pin and len(new_pin) == 4 and new_pin.isdigit():
            # Check if new PIN is already in use
            if new_pin != old_pin:
                self.cursor.execute('SELECT COUNT(*) FROM users WHERE pin = ?', (new_pin,))
                if self.cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "This PIN is already in use")
                    return
            self.cursor.execute('UPDATE users SET pin = ?, username = ? WHERE pin = ?', (new_pin, new_pin, old_pin))
            self.conn.commit()
            messagebox.showinfo("Success", f"PIN reset for user '{user_text}'")
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
        
        # Topping Prices Section
        topping_frame = tk.LabelFrame(scrollable_frame, text="Topping Prices", 
                                      font=('Arial', 12, 'bold'), bg=self.colors['bg_primary'],
                                      fg=self.colors['text_primary'], relief='solid', bd=1)
        topping_frame.pack(fill='x', padx=10, pady=10)
        
        topping_inner = tk.Frame(topping_frame, bg=self.colors['bg_primary'])
        topping_inner.pack(fill='x', padx=10, pady=10)
        
        # Function to auto-calculate other sizes when one is changed
        def update_topping_sizes(topping_name, changed_size):
            """Update other size prices when one size is changed (20% increase per size)"""
            try:
                # Get the changed price
                changed_entry = price_entries[('topping', topping_name, changed_size)]
                new_price_str = changed_entry.get().strip()
                if not new_price_str:
                    return
                
                new_price = Decimal(new_price_str)
                
                # Calculate base price (small) from the changed size
                if changed_size == 'small':
                    base_price = new_price
                elif changed_size == 'medium':
                    # Medium is 1.2x small, so small = medium / 1.2
                    base_price = new_price / Decimal('1.2')
                elif changed_size == 'large':
                    # Large is 1.44x small, so small = large / 1.44
                    base_price = new_price / Decimal('1.44')
                else:
                    return
                
                # Update other sizes
                if changed_size != 'small':
                    small_entry = price_entries.get(('topping', topping_name, 'small'))
                    if small_entry:
                        small_entry.delete(0, tk.END)
                        small_entry.insert(0, str(base_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)))
                
                if changed_size != 'medium':
                    medium_entry = price_entries.get(('topping', topping_name, 'medium'))
                    if medium_entry:
                        medium_price = (base_price * Decimal('1.2')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        medium_entry.delete(0, tk.END)
                        medium_entry.insert(0, str(medium_price))
                
                if changed_size != 'large':
                    large_entry = price_entries.get(('topping', topping_name, 'large'))
                    if large_entry:
                        large_price = (base_price * Decimal('1.44')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        large_entry.delete(0, tk.END)
                        large_entry.insert(0, str(large_price))
            except (ValueError, KeyError):
                pass  # Ignore invalid input
        
        # Topping prices by size
        for topping in sorted(self.topping_prices.keys()):
            # Small size
            row = tk.Frame(topping_inner, bg=self.colors['bg_primary'])
            row.pack(fill='x', pady=5)
            
            tk.Label(row, text=f"{topping} (Small):", font=('Arial', 10, 'bold'),
                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=20, anchor='w').pack(side='left')
            tk.Label(row, text="$", font=('Arial', 10), bg=self.colors['bg_primary'],
                    fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
            
            entry = tk.Entry(row, font=('Arial', 10), width=10, relief='solid', bd=1,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
            small_price = self.topping_prices.get(topping, {}).get('small', '0.00')
            entry.insert(0, str(small_price))
            entry.pack(side='left')
            price_entries[('topping', topping, 'small')] = entry
            # Bind to auto-calculate when changed
            entry.bind('<KeyRelease>', lambda e, t=topping, s='small': update_topping_sizes(t, s))
            entry.bind('<FocusOut>', lambda e, t=topping, s='small': update_topping_sizes(t, s))
            
            # Medium size
            row = tk.Frame(topping_inner, bg=self.colors['bg_primary'])
            row.pack(fill='x', pady=5)
            
            tk.Label(row, text=f"{topping} (Medium):", font=('Arial', 10, 'bold'),
                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=20, anchor='w').pack(side='left')
            tk.Label(row, text="$", font=('Arial', 10), bg=self.colors['bg_primary'],
                    fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
            
            entry = tk.Entry(row, font=('Arial', 10), width=10, relief='solid', bd=1,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
            medium_price = self.topping_prices.get(topping, {}).get('medium', '0.00')
            entry.insert(0, str(medium_price))
            entry.pack(side='left')
            price_entries[('topping', topping, 'medium')] = entry
            # Bind to auto-calculate when changed
            entry.bind('<KeyRelease>', lambda e, t=topping, s='medium': update_topping_sizes(t, s))
            entry.bind('<FocusOut>', lambda e, t=topping, s='medium': update_topping_sizes(t, s))
            
            # Large size
            row = tk.Frame(topping_inner, bg=self.colors['bg_primary'])
            row.pack(fill='x', pady=5)
            
            tk.Label(row, text=f"{topping} (Large):", font=('Arial', 10, 'bold'),
                    bg=self.colors['bg_primary'], fg=self.colors['text_primary'], width=20, anchor='w').pack(side='left')
            tk.Label(row, text="$", font=('Arial', 10), bg=self.colors['bg_primary'],
                    fg=self.colors['text_primary']).pack(side='left', padx=(0, 2))
            
            entry = tk.Entry(row, font=('Arial', 10), width=10, relief='solid', bd=1,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
            large_price = self.topping_prices.get(topping, {}).get('large', '0.00')
            entry.insert(0, str(large_price))
            entry.pack(side='left')
            price_entries[('topping', topping, 'large')] = entry
            # Bind to auto-calculate when changed
            entry.bind('<KeyRelease>', lambda e, t=topping, s='large': update_topping_sizes(t, s))
            entry.bind('<FocusOut>', lambda e, t=topping, s='large': update_topping_sizes(t, s))
        
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
                        # Handle different key formats:
                        # - ('pizza', size): pizza prices where item_name is the size
                        # - ('topping', topping_name, size): topping prices with size
                        # - ('drink', drink_name): drink prices (no size)
                        # - ('tax', 'rate'): tax rate (no size)
                        if len(key) == 3:
                            category, item_name, size = key
                        elif len(key) == 2:
                            category, item_name = key
                            # For pizza, item_name is the size, so size should be None
                            if category == 'pizza':
                                size = None
                            else:
                                size = None  # drinks and tax don't have size
                        else:
                            errors.append(f"Invalid key format: {key}")
                            continue
                        
                        value = entry.get().strip()
                        if not value:
                            display_name = f"{item_name}{' (' + size + ')' if size else ''}"
                            errors.append(f"{display_name}: Empty value")
                            continue
                        
                        price_decimal = Decimal(value)
                        if price_decimal < 0:
                            display_name = f"{item_name}{' (' + size + ')' if size else ''}"
                            errors.append(f"{display_name}: Negative value not allowed")
                            continue
                        
                        # Update or insert price
                        # Use a more robust approach that handles the unique constraint
                        # First, try to update existing record
                        if size is None:
                            self.cursor.execute('''
                                UPDATE prices 
                                SET price = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE category = ? AND item_name = ? AND size IS NULL
                            ''', (float(price_decimal), category, item_name))
                        else:
                            self.cursor.execute('''
                                UPDATE prices 
                                SET price = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE category = ? AND item_name = ? AND size = ?
                            ''', (float(price_decimal), category, item_name, size))
                        
                        # If no rows were updated, insert new record
                        if self.cursor.rowcount == 0:
                            self.cursor.execute('''
                                INSERT INTO prices (category, item_name, size, price)
                                VALUES (?, ?, ?, ?)
                            ''', (category, item_name, size, float(price_decimal)))
                        
                    except ValueError as e:
                        display_name = f"{item_name}{' (' + size + ')' if size else ''}"
                        errors.append(f"{display_name}: Invalid number format")
                    except Exception as e:
                        display_name = f"{item_name}{' (' + size + ')' if size else ''}"
                        errors.append(f"{display_name}: {str(e)}")
                
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
            SELECT o.id, u.pin, COALESCE(u.name, u.pin) as user_name, o.total, o.created_at
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
        
        # Orders list with scrollbar
        canvas = tk.Canvas(orders_window)
        scrollbar = tk.Scrollbar(orders_window, orient="vertical", command=canvas.yview)
        orders_frame = tk.Frame(canvas)
        
        orders_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=orders_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Headers
        headers = ["Order ID", "User", "Total", "Date & Time"]
        for i, header in enumerate(headers):
            tk.Label(orders_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=i, padx=5, pady=5, sticky='w')
        
        # Order rows
        for row, (order_id, user_pin, user_name, total, created_at) in enumerate(orders, 1):
            # Format timestamp properly
            try:
                # Parse the timestamp and format it nicely
                if isinstance(created_at, str):
                    # Try to parse the timestamp
                    dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    dt = datetime.datetime.fromtimestamp(created_at)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = str(created_at)
            
            tk.Label(orders_frame, text=str(order_id)).grid(row=row, column=0, padx=5, pady=2, sticky='w')
            tk.Label(orders_frame, text=user_name).grid(row=row, column=1, padx=5, pady=2, sticky='w')
            tk.Label(orders_frame, text=f"${total:.2f}").grid(row=row, column=2, padx=5, pady=2, sticky='w')
            tk.Label(orders_frame, text=formatted_time).grid(row=row, column=3, padx=5, pady=2, sticky='w')
    
    def logout(self):
        """Logout and return to login screen"""
        # Save cart before logging out
        if self.current_user:
            self.save_cart_for_user()
        self.current_user = None
        self.cart = []
        self.show_login()
    
    def save_cart_for_user(self):
        """Save current cart to database for the logged-in user"""
        if not self.current_user or not self.cart:
            # If cart is empty, delete saved cart
            self.cursor.execute('DELETE FROM carts WHERE user_id = ?', (self.current_user['id'],))
            self.conn.commit()
            return
        
        import json
        cart_json = json.dumps(self.cart, default=str)  # default=str handles Decimal serialization
        self.cursor.execute('''
            INSERT INTO carts (user_id, cart_data)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                cart_data = excluded.cart_data,
                updated_at = CURRENT_TIMESTAMP
        ''', (self.current_user['id'], cart_json))
        self.conn.commit()
    
    def load_cart_for_user(self):
        """Load saved cart from database for the logged-in user"""
        if not self.current_user:
            return
        
        self.cursor.execute('SELECT cart_data FROM carts WHERE user_id = ?', (self.current_user['id'],))
        result = self.cursor.fetchone()
        if result:
            import json
            try:
                cart_data = json.loads(result[0])
                # Convert price strings back to Decimal
                for item in cart_data:
                    if 'price' in item:
                        item['price'] = Decimal(str(item['price']))
                self.cart = cart_data
            except (json.JSONDecodeError, KeyError):
                self.cart = []
        else:
            self.cart = []
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.conn.close()

if __name__ == "__main__":
    app = PizzaPOSApp()
    app.run()

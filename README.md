# Bob's Pizza Emporium - Point of Sales System

A comprehensive Point of Sales (POS) application designed for Bob's Pizza Emporium, built with Python and Tkinter. This system provides a user-friendly interface for managing orders, inventory, pricing, and user accounts.

## Features

### Order Management
- **Standard Pizzas**: Quick selection of popular pizza options (Margherita, Pepperoni, Supreme, Hawaiian, Meat Lovers)
- **Custom Pizza Builder**: Interactive interface for creating custom pizzas with:
  - Size selection (Small, Medium, Large)
  - Multiple topping options with quantity controls
  - Real-time price display based on selected size
  - Visual topping selection with icons
- **Drink Selection**: Easy addition of beverages to orders
- **Shopping Cart**: View, modify, and manage items before checkout
- **Order Processing**: Complete order processing with tax calculation and order history

### Pricing System
- **Size-Based Pricing**: 
  - Pizza base prices vary by size
  - Topping prices automatically increase by 20% for each size upgrade:
    - Small = Base price
    - Medium = Small × 1.2 (20% increase)
    - Large = Small × 1.44 (20% increase from medium)
- **Dynamic Price Display**: Topping prices update automatically when pizza size changes
- **Flexible Price Configuration**: Admin can configure all prices with automatic size calculations

### User Management
- **PIN-Based Authentication**: Secure 4-digit PIN login system
- **User Names**: Each PIN can have an associated name for better identification
- **Role-Based Access**:
  - **Employee View**: Order taking and cart management
  - **Admin View**: Full system access including user management and price configuration
- **User Administration**: Add, edit, delete users and reset PINs

### Cart Persistence
- **Per-User Cart Saving**: Shopping carts are automatically saved per PIN
- **Session Continuity**: Cart persists across logouts until order is processed
- **Multi-User Support**: Each employee can maintain their own active cart

### Order History
- **Complete Order Tracking**: View all processed orders with:
  - Order ID
  - User name/PIN
  - Total amount
  - Accurate timestamp
- **Order Details**: Full itemized breakdown of each order

## Requirements

- Python 3.6 or higher
- Tkinter (usually included with Python)
- SQLite3 (included with Python)

## Installation

1. Clone or download this repository
2. Ensure Python 3.6+ is installed
3. Run the application:
   ```bash
   python bobs_pizza_emporium/pizza_pos_app.py
   ```
   
   Or use the launcher:
   ```bash
   python bobs_pizza_emporium/launch.py
   ```

## Default Login Credentials

- **Admin PIN**: `1234` (Administrator access)
- **Employee PIN**: `5678` (Standard employee access)

## Usage

### For Employees

1. **Login**: Enter your 4-digit PIN
2. **Select Items**: 
   - Choose from standard pizzas or create custom pizzas
   - Add drinks as needed
3. **Manage Cart**: Review items, remove unwanted items, or clear the entire cart
4. **Process Order**: Click "Process Order" to complete the transaction
5. **Logout**: Your cart will be saved and available when you log back in

### For Administrators

1. **User Management**:
   - Add new users with custom PINs and names
   - Edit existing user information
   - Delete users (cannot delete your own account)
   - Reset user PINs

2. **Price Configuration**:
   - Configure pizza prices by size
   - Set topping prices (small, medium, large)
     - Changing one size automatically calculates the others with 20% increments
   - Adjust drink prices
   - Modify tax rate

3. **View Orders**: Access complete order history with detailed information

## Custom Pizza Builder

The custom pizza interface provides:
- **Size Selection**: Visual buttons for Small, Medium, and Large
- **Topping Selection**: 
  - Icon-based topping buttons
  - Price display that updates based on selected size
  - Quantity controls (+/-) for each topping
- **Real-Time Preview**: See selected toppings and size in the sidebar
- **Price Calculation**: Automatic calculation including base pizza price and all toppings

## Database

The application uses SQLite for data storage:
- **Location**: 
  - Windows: `%APPDATA%\BobsPizzaEmporium\pizza_pos.db`
  - macOS/Linux: `~/.bobs_pizza_emporium/pizza_pos.db`
- **Tables**:
  - `users`: User accounts and PINs
  - `orders`: Order history
  - `prices`: Configurable pricing for all items
  - `carts`: Saved shopping carts per user

## Technical Details

- **Framework**: Tkinter (Python GUI)
- **Database**: SQLite3
- **Decimal Precision**: Uses Python's `Decimal` class for accurate financial calculations
- **Tax Calculation**: Configurable tax rate (default 8%)
- **Auto-Migration**: Database schema automatically updates when new features are added

## Building Executable

See `bobs_pizza_emporium/BUILD_EXECUTABLE.md` for instructions on creating standalone executables for Windows, macOS, and Linux.

## Features in Detail

### Size-Based Topping Prices
When configuring topping prices:
- Set the **Small** price (base price)
- **Medium** automatically calculates as Small × 1.2
- **Large** automatically calculates as Small × 1.44
- Changing any size recalculates the others to maintain the 20% increment structure

### Cart Persistence
- Carts are saved to the database when you logout
- Each PIN maintains its own cart
- Cart is cleared only when an order is processed
- Allows employees to pause and resume work without losing their current order

### Order Timestamps
- Orders are timestamped with accurate date and time
- Displayed in readable format: `YYYY-MM-DD HH:MM:SS`
- Stored in database for historical tracking

## Support

For issues or questions, please refer to the code comments or contact the development team.

## License

This application is proprietary software for Bob's Pizza Emporium.

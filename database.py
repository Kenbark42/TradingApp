import sqlite3
import pandas as pd
from datetime import datetime
import time
from utils import format_currency, format_percent, format_datetime
from contextlib import contextmanager

DATABASE_FILE = 'trading_simulation.db'

# Cache to avoid frequent database queries for static data
_account_cache = {"timestamp": 0, "data": None}
_positions_cache = {"timestamp": 0, "data": None}
CACHE_TTL = 5  # Cache time-to-live in seconds


@contextmanager
def get_db_connection():
    """Context manager for database connections to ensure proper closing"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        yield conn
    finally:
        if conn:
            conn.close()


def initialize_database():
    """Initializes the SQLite database and creates necessary tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Account table: Stores paper trading balance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY,
                balance REAL NOT NULL,
                initial_balance REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Positions table: Stores currently held stocks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                ticker TEXT PRIMARY KEY,
                quantity INTEGER NOT NULL,
                average_price REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Trades table: Logs all buy/sell transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT NOT NULL,
                order_type TEXT NOT NULL, -- 'BUY' or 'SELL'
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_cost REAL NOT NULL -- (quantity * price)
            )
        """)

        # Initialize account if it doesn't exist
        cursor.execute("SELECT COUNT(*) FROM account")
        if cursor.fetchone()[0] == 0:
            initial_balance = 100000.00  # Starting paper money
            cursor.execute("INSERT INTO account (balance, initial_balance) VALUES (?, ?)",
                           (initial_balance, initial_balance))
            print(f"Initialized account with ${initial_balance:,.2f}")

        conn.commit()

    print("Database initialized successfully.")


def get_account_balance():
    """Retrieves the current account balance with caching."""
    current_time = time.time()

    # Check cache first
    if current_time - _account_cache["timestamp"] < CACHE_TTL and _account_cache["data"] is not None:
        return _account_cache["data"]

    # Cache miss, query database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM account ORDER BY id LIMIT 1")
        result = cursor.fetchone()
        balance = result[0] if result else 0.0

    # Update cache
    _account_cache["timestamp"] = current_time
    _account_cache["data"] = balance

    return balance


def update_account_balance(new_balance):
    """Updates the account balance."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE account SET balance = ?, last_updated = ? WHERE id = (SELECT id FROM account ORDER BY id LIMIT 1)",
                (new_balance, datetime.now())
            )
            conn.commit()

            # Invalidate cache
            _account_cache["timestamp"] = 0
            return True
        except sqlite3.Error as e:
            print(f"Database error updating balance: {e}")
            return False


def log_trade(ticker, order_type, quantity, price):
    """Logs a trade into the trades table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        total_cost = quantity * price
        try:
            cursor.execute("""
                INSERT INTO trades (ticker, order_type, quantity, price, total_cost, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ticker, order_type, quantity, price, total_cost, datetime.now()))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error logging trade: {e}")
            return False


def get_position(ticker):
    """Retrieves the current position for a specific ticker."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT quantity, average_price FROM positions WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()

    return result if result else (0, 0.0)  # quantity, avg_price


def update_position(ticker, new_quantity, new_average_price):
    """Updates or inserts a position."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            if new_quantity > 0:
                # Use REPLACE INTO which is an SQLite extension (UPSERT)
                # It deletes the old row (if exists based on PRIMARY KEY) and inserts the new one.
                cursor.execute("""
                    REPLACE INTO positions (ticker, quantity, average_price, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (ticker, new_quantity, new_average_price, datetime.now()))
                print(
                    f"Position updated for {ticker}: Qty={new_quantity}, AvgPrice={new_average_price:.2f}")
            else:
                # Remove position if quantity is zero or less
                cursor.execute(
                    "DELETE FROM positions WHERE ticker = ?", (ticker,))
                print(f"Position closed for {ticker}")

            conn.commit()

            # Invalidate positions cache
            _positions_cache["timestamp"] = 0
            return True
        except sqlite3.Error as e:
            print(f"Database error updating position: {e}")
            return False


def get_all_positions():
    """Retrieves all current positions as a DataFrame with caching."""
    current_time = time.time()

    # Check cache first
    if current_time - _positions_cache["timestamp"] < CACHE_TTL and _positions_cache["data"] is not None:
        return _positions_cache["data"].copy()

    # Cache miss, query database
    with get_db_connection() as conn:
        try:
            df = pd.read_sql_query(
                "SELECT ticker, quantity, average_price FROM positions", conn)

            # Update cache
            _positions_cache["timestamp"] = current_time
            _positions_cache["data"] = df.copy()

            return df
        except Exception as e:
            print(f"Error reading positions: {e}")
            # Return empty df on error
            return pd.DataFrame(columns=['ticker', 'quantity', 'average_price'])


def get_positions():
    """
    Retrieves current positions in a format suitable for the UI.
    Each position includes current price from stock data module.
    """
    import stock_data as sd  # Import here to avoid circular imports

    try:
        # Get all positions from database as DataFrame
        positions_df = get_all_positions()

        if positions_df.empty:
            return []  # Return empty list if no positions

        # Convert to list of dictionaries for UI consumption
        positions = []

        for _, row in positions_df.iterrows():
            ticker = row['ticker']
            quantity = row['quantity']
            entry_price = row['average_price']

            # Get current price for the ticker (use cached price for better performance)
            try:
                current_price = sd.get_cached_price(ticker) or entry_price
            except:
                # If error getting price, use entry price
                current_price = entry_price

            # Calculate position value and P/L
            position_value = quantity * current_price
            pnl = position_value - (quantity * entry_price)
            pnl_percent = (pnl / (quantity * entry_price)) * \
                100 if entry_price > 0 else 0

            positions.append({
                'symbol': ticker,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'position_value': position_value,
                'pnl': pnl,
                'pnl_percent': pnl_percent
            })

        return positions

    except Exception as e:
        print(f"Error in get_positions: {e}")
        return []


def get_account_info():
    """
    Gets comprehensive account information including:
    - Current cash balance
    - Portfolio value (positions)
    - Total equity
    - Profit/loss metrics
    """
    try:
        import trading_logic as tl  # Import here to avoid circular imports

        # Get the account balance
        cash_balance = get_account_balance()

        # Get the portfolio value
        portfolio_value = tl.get_portfolio_value()

        # Calculate total equity
        total_equity = cash_balance + portfolio_value

        # Get initial balance for P/L calculation
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT initial_balance FROM account ORDER BY id LIMIT 1")
            result = cursor.fetchone()
            initial_balance = result[0] if result else 0.0

        # Calculate P/L
        pnl = total_equity - initial_balance
        pnl_percent = (pnl / initial_balance *
                       100) if initial_balance > 0 else 0

        return {
            'cash_balance': cash_balance,
            'portfolio_value': portfolio_value,
            'total_equity': total_equity,
            'initial_balance': initial_balance,
            'pnl': pnl,
            'pnl_percent': pnl_percent
        }
    except Exception as e:
        print(f"Error getting account info: {e}")
        return {
            'cash_balance': 0.0,
            'portfolio_value': 0.0,
            'total_equity': 0.0,
            'initial_balance': 0.0,
            'pnl': 0.0,
            'pnl_percent': 0.0
        }


def get_trade_history(limit=100):
    """
    Retrieves the trade history ordered by most recent first.

    Args:
        limit (int): Maximum number of trades to retrieve

    Returns:
        list: List of trade dictionaries
    """
    try:
        with get_db_connection() as conn:
            query = """
                SELECT id, timestamp, ticker, order_type, quantity, price, total_cost
                FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))

            if df.empty:
                return []

            # Convert to list of dictionaries
            trades = []
            for _, row in df.iterrows():
                trades.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'symbol': row['ticker'],
                    'side': row['order_type'],
                    'quantity': row['quantity'],
                    'price': row['price'],
                    'total': row['total_cost']
                })

            return trades
    except Exception as e:
        print(f"Error getting trade history: {e}")
        return []


def clear_cache():
    """Clear all database caches"""
    global _account_cache, _positions_cache
    _account_cache = {"timestamp": 0, "data": None}
    _positions_cache = {"timestamp": 0, "data": None}
    print("Database cache cleared")


if __name__ == "__main__":
    # Test initialization and basic operations
    initialize_database()

    print("\n--- Account Balance ---")
    balance = get_account_balance()
    print(f"Current balance: {format_currency(balance)}")

    print("\n--- Positions ---")
    positions = get_positions()
    if positions:
        for pos in positions:
            print(f"{pos['symbol']}: {pos['quantity']} shares @ {format_currency(pos['entry_price'])}, "
                  f"Current: {format_currency(pos['current_price'])}, "
                  f"Value: {format_currency(pos['position_value'])}")
    else:
        print("No positions")

    print("\n--- Trade History ---")
    trades = get_trade_history(5)
    if trades:
        for trade in trades:
            print(f"{trade['timestamp']} - {trade['side']} {trade['quantity']} {trade['symbol']} @ "
                  f"{format_currency(trade['price'])}, Total: {format_currency(trade['total'])}")
    else:
        print("No trade history")

    print("\n--- Account Info ---")
    info = get_account_info()
    print(f"Cash: {format_currency(info['cash_balance'])}")
    print(f"Portfolio: {format_currency(info['portfolio_value'])}")
    print(f"Equity: {format_currency(info['total_equity'])}")
    print(
        f"P/L: {format_currency(info['pnl'])} ({format_percent(info['pnl_percent'])})")

    print("\n--- Testing Cache ---")
    start_time = time.time()
    get_account_balance()  # First call, should hit database
    first_time = time.time() - start_time

    start_time = time.time()
    get_account_balance()  # Second call, should hit cache
    second_time = time.time() - start_time

    print(f"First call: {first_time:.6f}s, Second call: {second_time:.6f}s")
    if second_time > 0:
        print(f"Cache speedup: {first_time/second_time:.1f}x")

    clear_cache()  # Reset cache for normal operations

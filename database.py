import sqlite3
import pandas as pd
from datetime import datetime

DATABASE_FILE = 'trading_simulation.db'


def initialize_database():
    """Initializes the SQLite database and creates necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
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
    conn.close()
    print("Database initialized successfully.")


def get_connection():
    """Returns a connection object to the database."""
    return sqlite3.connect(DATABASE_FILE)


def get_account_balance():
    """Retrieves the current account balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM account ORDER BY id LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0


def update_account_balance(new_balance):
    """Updates the account balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE account SET balance = ?, last_updated = ? WHERE id = (SELECT id FROM account ORDER BY id LIMIT 1)",
                   (new_balance, datetime.now()))
    conn.commit()
    conn.close()


def log_trade(ticker, order_type, quantity, price):
    """Logs a trade into the trades table."""
    conn = get_connection()
    cursor = conn.cursor()
    total_cost = quantity * price
    cursor.execute("""
        INSERT INTO trades (ticker, order_type, quantity, price, total_cost, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ticker, order_type, quantity, price, total_cost, datetime.now()))
    conn.commit()
    conn.close()


def get_position(ticker):
    """Retrieves the current position for a specific ticker."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT quantity, average_price FROM positions WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (0, 0.0)  # quantity, avg_price


def update_position(ticker, new_quantity, new_average_price):
    """Updates or inserts a position."""
    conn = get_connection()
    cursor = conn.cursor()
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
        cursor.execute("DELETE FROM positions WHERE ticker = ?", (ticker,))
        print(f"Position closed for {ticker}")
    conn.commit()
    conn.close()


def get_all_positions():
    """Retrieves all current positions as a DataFrame."""
    conn = get_connection()
    # Use pandas read_sql for convenience
    try:
        df = pd.read_sql_query(
            "SELECT ticker, quantity, average_price FROM positions", conn)
    except Exception as e:
        print(f"Error reading positions: {e}")
        # Return empty df on error
        df = pd.DataFrame(columns=['ticker', 'quantity', 'average_price'])
    finally:
        conn.close()
    return df


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

            # Get current price for the ticker
            try:
                current_price = sd.get_latest_price(ticker) or entry_price
            except:
                # If error getting price, use entry price
                current_price = entry_price

            # Calculate position value and P/L
            position_value = quantity * current_price

            positions.append({
                'symbol': ticker,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'position_value': position_value
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
        # Get the cash balance
        cash_balance = get_account_balance()

        # Get initial balance for P/L calculation
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT initial_balance FROM account LIMIT 1")
        initial_balance = cursor.fetchone()[0]
        conn.close()

        # Calculate portfolio value from positions
        positions = get_positions()
        portfolio_value = sum(pos['position_value'] for pos in positions)

        # Calculate total equity
        total_equity = cash_balance + portfolio_value

        # Calculate P/L
        profit_loss = total_equity - initial_balance
        profit_loss_pct = (profit_loss / initial_balance) * \
            100 if initial_balance > 0 else 0

        return {
            'balance': cash_balance,
            'portfolio_value': portfolio_value,
            'total_equity': total_equity,
            'initial_balance': initial_balance,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'buying_power': cash_balance  # In a cash account, buying power equals cash balance
        }

    except Exception as e:
        print(f"Error in get_account_info: {e}")
        # Return dummy data in case of error to prevent UI crashes
        return {
            'balance': 0.0,
            'portfolio_value': 0.0,
            'total_equity': 0.0,
            'profit_loss': 0.0,
            'profit_loss_pct': 0.0,
            'buying_power': 0.0
        }


def get_trade_history():
    """
    Retrieves trade history in format suitable for the UI.
    """
    try:
        # Get trade history as DataFrame
        history_df = pd.read_sql_query(
            "SELECT id, timestamp, ticker, order_type, quantity, price FROM trades ORDER BY timestamp DESC",
            get_connection()
        )

        if history_df.empty:
            return []

        # Convert to list of dictionaries for UI
        history = []

        for _, row in history_df.iterrows():
            history.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'symbol': row['ticker'],
                'side': row['order_type'].lower(),
                'quantity': row['quantity'],
                'price': row['price']
            })

        return history

    except Exception as e:
        print(f"Error in get_trade_history: {e}")
        return []


# Original get_trade_history function renamed to get_trade_history_df to avoid collision
def get_trade_history_df():
    """Retrieves the trade history as a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT timestamp, ticker, order_type, quantity, price, total_cost FROM trades ORDER BY timestamp DESC", conn)
        # Format timestamp for better readability if needed
        if not df.empty:
            df['timestamp'] = pd.to_datetime(
                df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error reading trade history: {e}")
        df = pd.DataFrame(
            columns=['timestamp', 'ticker', 'order_type', 'quantity', 'price', 'total_cost'])
    finally:
        conn.close()
    return df


if __name__ == '__main__':
    print("Initializing DB for standalone test...")
    initialize_database()
    print(f"Initial Balance: ${get_account_balance():,.2f}")

    # --- Example Interactions (for testing) ---
    # Simulate buying 10 AAPL @ 150
    # log_trade('AAPL', 'BUY', 10, 150.00)
    # update_position('AAPL', 10, 150.00)
    # update_account_balance(get_account_balance() - (10 * 150.00))
    # print(f"Balance after buying AAPL: ${get_account_balance():,.2f}")
    # print("Positions after buying AAPL:")
    # print(get_all_positions())

    # Simulate selling 5 AAPL @ 160
    # current_qty, avg_price = get_position('AAPL')
    # if current_qty >= 5:
    #    log_trade('AAPL', 'SELL', 5, 160.00)
    #    update_position('AAPL', current_qty - 5, avg_price) # Avg price doesn't change on sell
    #    update_account_balance(get_account_balance() + (5 * 160.00))
    #    print(f"Balance after selling AAPL: ${get_account_balance():,.2f}")
    #    print("Positions after selling AAPL:")
    #    print(get_all_positions())
    # else:
    #    print("Not enough AAPL shares to sell.")

    print("\nTrade History:")
    print(get_trade_history())
    print("\nFinal Positions:")
    print(get_all_positions())
    print(f"\nFinal Balance: ${get_account_balance():,.2f}")

import database as db
import stock_data as sd
import pandas as pd

# --- Core Trading Functions ---


def execute_buy(ticker, quantity):
    """Simulates buying a specified quantity of a stock."""
    if not isinstance(quantity, int) or quantity <= 0:
        print("Error: Quantity must be a positive integer.")
        return {"success": False, "message": "Quantity must be a positive integer."}

    print(f"Attempting to buy {quantity} shares of {ticker}...")
    latest_price = sd.get_latest_price(ticker)
    if latest_price is None:
        print(
            f"Error: Could not fetch latest price for {ticker}. Buy order cancelled.")
        return {"success": False, "message": f"Could not fetch price for {ticker}."}

    cost = quantity * latest_price
    current_balance = db.get_account_balance()

    if cost > current_balance:
        print(
            f"Error: Insufficient funds. Need ${cost:.2f}, Balance: ${current_balance:.2f}. Buy order cancelled.")
        return {"success": False, "message": "Insufficient funds."}

    # Update balance
    new_balance = current_balance - cost
    db.update_account_balance(new_balance)

    # Update position
    current_qty, current_avg_price = db.get_position(ticker)
    total_existing_cost = current_qty * current_avg_price
    total_new_cost = cost

    new_quantity = current_qty + quantity
    new_average_price = (total_existing_cost + total_new_cost) / new_quantity
    db.update_position(ticker, new_quantity, new_average_price)

    # Log the trade
    db.log_trade(ticker, 'BUY', quantity, latest_price)

    print(
        f"Successfully executed BUY order: {quantity} {ticker} @ ${latest_price:.2f}")
    print(f"New Balance: ${new_balance:.2f}")

    return {
        "success": True,
        "message": f"Bought {quantity} {ticker} @ ${latest_price:.2f}",
        "ticker": ticker,
        "quantity": quantity,
        "price": latest_price,
        "total_cost": cost,
        "new_balance": new_balance
    }


def execute_sell(ticker, quantity):
    """Simulates selling a specified quantity of a stock."""
    if not isinstance(quantity, int) or quantity <= 0:
        print("Error: Quantity must be a positive integer.")
        return {"success": False, "message": "Quantity must be a positive integer."}

    print(f"Attempting to sell {quantity} shares of {ticker}...")
    current_qty, avg_price = db.get_position(ticker)

    if quantity > current_qty:
        print(
            f"Error: Not enough shares to sell. Position: {current_qty} {ticker}, Trying to sell: {quantity}. Sell order cancelled.")
        return {"success": False, "message": f"Not enough shares of {ticker} to sell."}

    latest_price = sd.get_latest_price(ticker)
    if latest_price is None:
        print(
            f"Error: Could not fetch latest price for {ticker}. Sell order cancelled.")
        return {"success": False, "message": f"Could not fetch price for {ticker}."}

    proceeds = quantity * latest_price

    # Update balance
    current_balance = db.get_account_balance()
    new_balance = current_balance + proceeds
    db.update_account_balance(new_balance)

    # Update position (average price remains the same on sell)
    new_quantity = current_qty - quantity
    # If new_quantity becomes 0, update_position handles removal
    db.update_position(ticker, new_quantity, avg_price)

    # Log the trade
    db.log_trade(ticker, 'SELL', quantity, latest_price)

    # Calculate Profit/Loss for this specific trade (optional, good for logging)
    cost_basis_for_sold_shares = quantity * avg_price
    pnl_trade = proceeds - cost_basis_for_sold_shares

    print(
        f"Successfully executed SELL order: {quantity} {ticker} @ ${latest_price:.2f}")
    print(
        f"Proceeds: ${proceeds:.2f}, Cost Basis: ${cost_basis_for_sold_shares:.2f}, P/L: ${pnl_trade:.2f}")
    print(f"New Balance: ${new_balance:.2f}")

    return {
        "success": True,
        "message": f"Sold {quantity} {ticker} @ ${latest_price:.2f}, P/L: ${pnl_trade:.2f}",
        "ticker": ticker,
        "quantity": quantity,
        "price": latest_price,
        "proceeds": proceeds,
        "pnl": pnl_trade,
        "new_balance": new_balance
    }

# --- Portfolio Calculation ---


def get_portfolio_value():
    """Calculates the total market value of all positions."""
    positions = db.get_all_positions()
    total_value = 0.0
    print("Calculating portfolio value...")

    if positions.empty:
        print("No positions held.")
        return 0.0

    for index, row in positions.iterrows():
        ticker = row['ticker']
        quantity = row['quantity']
        latest_price = sd.get_latest_price(ticker)
        if latest_price is not None:
            position_value = quantity * latest_price
            total_value += position_value
            print(
                f"  {ticker}: {quantity} shares @ ${latest_price:.2f} = ${position_value:.2f}")
        else:
            print(
                f"  Warning: Could not fetch latest price for {ticker}. Skipping for portfolio value calculation.")

    print(f"Total Portfolio Market Value: ${total_value:.2f}")
    return total_value


def get_total_equity():
    """Calculates total equity (cash balance + portfolio value)."""
    cash_balance = db.get_account_balance()
    portfolio_value = get_portfolio_value()
    total_equity = cash_balance + portfolio_value
    print(f"Total Equity (Cash + Positions): ${total_equity:.2f}")
    return total_equity


def get_portfolio_pnl():
    """Calculates the overall profit or loss of the portfolio."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT initial_balance FROM account ORDER BY id LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    initial_balance = result[0] if result else 0.0

    current_equity = get_total_equity()
    pnl = current_equity - initial_balance
    pnl_percent = (pnl / initial_balance * 100) if initial_balance != 0 else 0

    print(f"Overall P/L: ${pnl:.2f} ({pnl_percent:.2f}%)")
    return pnl, pnl_percent


if __name__ == '__main__':
    print("--- Running Trading Logic Standalone Test ---")
    # Ensure DB is initialized (important if running this file directly first)
    db.initialize_database()

    initial_balance = db.get_account_balance()
    print(f"Starting Balance: ${initial_balance:,.2f}")

    # Example Trades (Uncomment to test)
    print("\n--- Test BUY --- ")
    # execute_buy('AAPL', 5) # Buy 5 AAPL
    # time.sleep(1) # Small delay between API calls
    # execute_buy('MSFT', 10)
    # time.sleep(1)
    # execute_buy('INVALIDTICKER', 1) # Test invalid ticker
    # execute_buy('AAPL', 999999) # Test insufficient funds

    print("\n--- Test SELL --- ")
    # execute_sell('AAPL', 2) # Sell 2 AAPL
    # time.sleep(1)
    # execute_sell('MSFT', 15) # Test selling more than owned
    # time.sleep(1)
    # execute_sell('GOOGL', 1) # Test selling stock not owned

    print("\n--- Portfolio Summary --- ")
    # Recalculate portfolio value and PnL after trades
    # final_equity = get_total_equity()
    # pnl, pnl_percent = get_portfolio_pnl()

    print("\n--- Current State (from DB) ---")
    print("Positions:")
    print(db.get_all_positions())
    print("\nTrade History:")
    print(db.get_trade_history().head())  # Show recent trades
    print(f"\nFinal Balance: ${db.get_account_balance():,.2f}")

    print("\n--- Standalone Test Complete ---")
    # Note: The P/L calculation in execute_sell is for that specific trade lot.
    # The get_portfolio_pnl calculates overall account P/L vs initial balance.

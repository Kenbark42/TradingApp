import database as db
import stock_data as sd
import pandas as pd
import time
from utils import format_currency, run_in_thread, retry

# --- Core Trading Functions ---


@retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
def execute_buy(ticker, quantity):
    """Simulates buying a specified quantity of a stock."""
    if not isinstance(quantity, int) or quantity <= 0:
        print("Error: Quantity must be a positive integer.")
        return {"success": False, "message": "Quantity must be a positive integer."}

    print(f"Attempting to buy {quantity} shares of {ticker}...")
    # Use cached price for better performance
    latest_price = sd.get_cached_price(ticker)
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
    if not db.update_account_balance(new_balance):
        return {"success": False, "message": "Database error updating balance."}

    # Update position
    current_qty, current_avg_price = db.get_position(ticker)
    total_existing_cost = current_qty * current_avg_price
    total_new_cost = cost

    new_quantity = current_qty + quantity
    new_average_price = (total_existing_cost + total_new_cost) / new_quantity
    if not db.update_position(ticker, new_quantity, new_average_price):
        # Revert balance change if position update fails
        db.update_account_balance(current_balance)
        return {"success": False, "message": "Database error updating position."}

    # Log the trade
    if not db.log_trade(ticker, 'BUY', quantity, latest_price):
        # We don't revert here since the trade did happen, but we log the error
        print("Warning: Failed to log trade in history.")

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


@retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
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

    # Use cached price for better performance
    latest_price = sd.get_cached_price(ticker)
    if latest_price is None:
        print(
            f"Error: Could not fetch latest price for {ticker}. Sell order cancelled.")
        return {"success": False, "message": f"Could not fetch price for {ticker}."}

    proceeds = quantity * latest_price

    # Update balance
    current_balance = db.get_account_balance()
    new_balance = current_balance + proceeds
    if not db.update_account_balance(new_balance):
        return {"success": False, "message": "Database error updating balance."}

    # Update position (average price remains the same on sell)
    new_quantity = current_qty - quantity
    # If new_quantity becomes 0, update_position handles removal
    if not db.update_position(ticker, new_quantity, avg_price):
        # Revert balance change if position update fails
        db.update_account_balance(current_balance)
        return {"success": False, "message": "Database error updating position."}

    # Log the trade
    if not db.log_trade(ticker, 'SELL', quantity, latest_price):
        # We don't revert here since the trade did happen, but we log the error
        print("Warning: Failed to log trade in history.")

    # Calculate Profit/Loss for this specific trade
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


def execute_buy_async(ticker, quantity, callback=None):
    """Execute a buy order in a background thread"""
    def _execute_and_callback():
        result = execute_buy(ticker, quantity)
        if callback:
            callback(result)

    run_in_thread(_execute_and_callback)


def execute_sell_async(ticker, quantity, callback=None):
    """Execute a sell order in a background thread"""
    def _execute_and_callback():
        result = execute_sell(ticker, quantity)
        if callback:
            callback(result)

    run_in_thread(_execute_and_callback)


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
        # Use cached price for performance
        latest_price = sd.get_cached_price(ticker)
        if latest_price is not None:
            position_value = quantity * latest_price
            total_value += position_value
            print(
                f"  {ticker}: {quantity} shares @ ${latest_price:.2f} = ${position_value:.2f}")
        else:
            print(
                f"  Warning: Could not fetch latest price for {ticker}. Using average price.")
            # Fallback to using average price
            position_value = quantity * row['average_price']
            total_value += position_value
            print(
                f"  {ticker}: {quantity} shares @ ${row['average_price']:.2f} = ${position_value:.2f}")

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
    account_info = db.get_account_info()
    pnl = account_info['pnl']
    pnl_percent = account_info['pnl_percent']

    print(f"Overall P/L: ${pnl:.2f} ({pnl_percent:.2f}%)")
    return pnl, pnl_percent


# --- Auto Trading Strategies ---
# These are simplified simulations; real strategies would be more complex

def execute_momentum_strategy(ticker, quantity=10):
    """
    Simple momentum strategy:
    - If price is higher than 5-day MA, buy
    - If price is lower than 5-day MA, sell
    """
    try:
        data = sd.fetch_stock_data(ticker, period="10d", interval="1d")
        if data.empty:
            return {"success": False, "message": f"No data available for {ticker}"}

        # Calculate 5-day moving average
        data['MA5'] = data['Close'].rolling(window=5).mean()

        # Get last row for comparison
        last_price = data['Close'].iloc[-1]
        ma5 = data['MA5'].iloc[-1]

        # Determine action based on price vs MA
        if last_price > ma5:
            print(
                f"Momentum signal: BUY {ticker} - Price {last_price:.2f} > MA5 {ma5:.2f}")
            return execute_buy(ticker, quantity)
        else:
            print(
                f"Momentum signal: SELL {ticker} - Price {last_price:.2f} < MA5 {ma5:.2f}")
            # Check if we have any shares to sell
            current_qty, _ = db.get_position(ticker)
            if current_qty >= quantity:
                return execute_sell(ticker, quantity)
            else:
                return {"success": False, "message": f"Not enough shares of {ticker} to sell"}

    except Exception as e:
        print(f"Error executing momentum strategy: {e}")
        return {"success": False, "message": f"Strategy error: {e}"}


def execute_mean_reversion_strategy(ticker, quantity=10):
    """
    Simple mean reversion strategy:
    - If price is significantly lower than 20-day MA, buy (expecting rise)
    - If price is significantly higher than 20-day MA, sell (expecting drop)
    """
    try:
        data = sd.fetch_stock_data(ticker, period="30d", interval="1d")
        if data.empty:
            return {"success": False, "message": f"No data available for {ticker}"}

        # Calculate 20-day moving average
        data['MA20'] = data['Close'].rolling(window=20).mean()

        # Get last row for comparison
        last_price = data['Close'].iloc[-1]
        ma20 = data['MA20'].iloc[-1]

        # Calculate percent difference from MA
        percent_diff = ((last_price - ma20) / ma20) * 100

        # Determine action based on deviation from MA
        if percent_diff < -5:  # Price is 5% below MA
            print(
                f"Mean Reversion signal: BUY {ticker} - Price {percent_diff:.2f}% below MA20")
            return execute_buy(ticker, quantity)
        elif percent_diff > 5:  # Price is 5% above MA
            print(
                f"Mean Reversion signal: SELL {ticker} - Price {percent_diff:.2f}% above MA20")
            # Check if we have any shares to sell
            current_qty, _ = db.get_position(ticker)
            if current_qty >= quantity:
                return execute_sell(ticker, quantity)
            else:
                return {"success": False, "message": f"Not enough shares of {ticker} to sell"}
        else:
            return {"success": False, "message": f"No signal for {ticker} - Price is within normal range of MA20"}

    except Exception as e:
        print(f"Error executing mean reversion strategy: {e}")
        return {"success": False, "message": f"Strategy error: {e}"}


# Dictionary mapping strategy names to their functions
STRATEGY_FUNCTIONS = {
    "momentum": execute_momentum_strategy,
    "mean_reversion": execute_mean_reversion_strategy,
    # Other strategies would be added here
}


def execute_strategy(strategy_name, ticker, quantity=10):
    """Execute a named trading strategy"""
    if strategy_name in STRATEGY_FUNCTIONS:
        strategy_func = STRATEGY_FUNCTIONS[strategy_name]
        return strategy_func(ticker, quantity)
    else:
        return {"success": False, "message": f"Unknown strategy: {strategy_name}"}


if __name__ == '__main__':
    print("--- Running Trading Logic Standalone Test ---")
    # Ensure DB is initialized (important if running this file directly first)
    db.initialize_database()

    initial_balance = db.get_account_balance()
    print(f"Starting Balance: ${initial_balance:,.2f}")

    # Example Trades (Uncomment to test)
    print("\n--- Test BUY --- ")
    # execute_buy('AAPL', 5) # Buy 5 AAPL

    # Test asynchronous buying
    # def buy_callback(result):
    #     print(f"Async buy result: {result['message'] if 'message' in result else 'Error'}")
    # execute_buy_async('MSFT', 10, buy_callback)

    print("\n--- Test SELL --- ")
    # execute_sell('AAPL', 2) # Sell 2 AAPL

    print("\n--- Test Strategy ---")
    # execute_strategy('momentum', 'AAPL', 3)
    # time.sleep(1)
    # execute_strategy('mean_reversion', 'MSFT', 3)

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

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time  # Import time for potential retries or delays


def fetch_stock_data(ticker_symbol, period="1mo", interval="1d"):
    """
    Fetches stock data for charting in the app. This is a wrapper around get_stock_data
    that provides the format expected by the chart interface.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').
        period (str): The period to fetch data for (e.g., "1d", "5d", "1mo", "1y").
        interval (str): The data interval (e.g., "1m", "2m", "5m", "1d").

    Returns:
        pandas.DataFrame: Formatted data for charting or empty DataFrame if failed
    """
    try:
        data = get_stock_data(ticker_symbol, period=period, interval=interval)
        if data is None or data.empty:
            print(f"No data available for {ticker_symbol}")
            return pd.DataFrame()

        # Ensure the data is structured as expected by the app
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        return data

    except Exception as e:
        print(f"Error in fetch_stock_data for {ticker_symbol}: {e}")
        return pd.DataFrame()


def get_stock_data(ticker_symbol, period="5d", interval="5m"):
    """
    Fetches historical stock data for the given ticker symbol for a specified period and interval.
    Suitable for fetching intraday data.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').
        period (str): The period to fetch data for (e.g., "1d", "5d", "1mo", "1y").
                      Check yfinance docs for valid periods based on interval.
        interval (str): The data interval (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d").
                        Check yfinance docs for valid intervals. '1m' data is usually only available for the last 7 days.

    Returns:
        pandas.DataFrame: A DataFrame containing the historical stock data (Datetime, Open, High, Low, Close, Volume).
                          Index is Datetime. Returns None if the ticker is invalid or data fetch fails.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        # Fetch history based on period and interval
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            print(
                f"No data found for ticker {ticker_symbol} with period={period} and interval={interval}.")
            return None

        # yfinance intraday data might have timezone info, daily does not always.
        # Ensure index is datetime objects for consistency if needed, though yfinance usually handles this.
        if not isinstance(hist.index, pd.DatetimeIndex):
            hist.index = pd.to_datetime(hist.index)

        # For intraday, moving averages might be less meaningful or calculated differently.
        # We'll skip them for now but could add short-term MAs later.
        # hist['MA5'] = hist['Close'].rolling(window=5).mean()
        # hist['MA20'] = hist['Close'].rolling(window=20).mean()

        # No need to reset_index if we want the Datetime index for plotting time series
        return hist

    except Exception as e:
        print(
            f"Error fetching data for {ticker_symbol} (period={period}, interval={interval}): {e}")
        return None


def get_latest_price(ticker_symbol):
    """
    Fetches the most recent available price for a ticker symbol.
    Tries to get the pre/post market price if available, otherwise the last closing price.

    Args:
        ticker_symbol (str): The stock ticker symbol.

    Returns:
        float: The latest price, or None if fetching fails.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        # Use Ticker.info which is faster for current data points
        info = stock.info

        # Check for different price possibilities
        # 'currentPrice' is often available for actively traded stocks
        if 'currentPrice' in info and info['currentPrice'] is not None:
            return float(info['currentPrice'])
        # 'bid' might be available if 'currentPrice' isn't
        elif 'bid' in info and info['bid'] is not None and info['bid'] > 0:
            return float(info['bid'])  # Use bid if available
        # 'previousClose' as a fallback
        elif 'previousClose' in info and info['previousClose'] is not None:
            print(f"Warning: Using previous close price for {ticker_symbol}")
            return float(info['previousClose'])
        else:
            # Fallback to history if info doesn't have price (less ideal for 'latest')
            hist = stock.history(period="1d", interval="1m")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            else:
                print(
                    f"Could not find any price information for {ticker_symbol} in info or recent history.")
                return None

    except Exception as e:
        print(f"Error fetching latest price for {ticker_symbol}: {e}")
        # Adding a small delay in case of rapid API calls causing issues
        time.sleep(0.5)
        return None


if __name__ == '__main__':
    # Example usage:
    print("\n--- Fetching Intraday Data (MSFT 1 day, 5 min interval) ---")
    msft_data = get_stock_data("MSFT", period="1d", interval="5m")
    if msft_data is not None:
        print("MSFT Intraday Data (Last 5 rows):")
        print(msft_data.tail())

    print("\n--- Fetching Daily Data (GOOGL 1 year) ---")
    googl_data = get_stock_data("GOOGL", period="1y", interval="1d")
    if googl_data is not None:
        print("GOOGL Daily Data (Last 5 rows):")
        print(googl_data.tail())

    print("\n--- Fetching Latest Prices ---")
    latest_aapl = get_latest_price("AAPL")
    if latest_aapl:
        print(f"Latest AAPL Price: {latest_aapl:.2f}")

    latest_invalid = get_latest_price("INVALIDTICKERXYZ")
    if latest_invalid is None:
        print("Successfully handled invalid ticker for latest price.")

    # Example for a potentially less common ticker
    latest_pton = get_latest_price("PTON")
    if latest_pton:
        print(f"Latest PTON Price: {latest_pton:.2f}")
    else:
        print("Could not fetch latest price for PTON.")

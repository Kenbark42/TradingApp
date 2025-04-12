# AlgoTrade Simulator

A paper trading platform with a modern UI built in Python using CustomTkinter.

## Features

- Modern dark/light theme interface
- Real-time stock data visualization
- Paper trading with virtual money
- Position tracking and trade history
- Chart visualization
- Auto-trading configuration options

## Application Highlights

This application has been optimized for performance and maintainability:

- **Modular Architecture**: UI components separated into reusable classes
- **Data Caching**: Optimized database and network access with smart caching
- **Multithreading**: Responsive UI with background operations
- **Error Handling**: Robust error handling throughout
- **Configuration Management**: Settings separated from implementation
- **Utilities**: Common functions extracted to utility modules

## Requirements

- Python 3.7+
- CustomTkinter
- Matplotlib
- Pandas
- yfinance

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python app.py
```

You can also use the launcher:

```bash
python launcher.py
```

Or on Windows, use the PowerShell script:
```bash
.\run_app.ps1
```

## Project Structure

- `app.py` - Main application with modular structure
- `config.py` - Application configuration and constants
- `ui_components.py` - UI component classes
- `utils.py` - Utility functions
- `database.py` - Database access layer
- `stock_data.py` - Stock data fetching and processing
- `trading_logic.py` - Trading algorithms and execution logic
- `launcher.py` - Application launcher

## Screenshots

(Screenshots to be added) 
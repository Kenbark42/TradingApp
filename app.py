import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Menu
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

# Import our custom modules
import database as db
import stock_data as sd
import trading_logic as tl
import utils
from config import COLORS, TRADING_ALGORITHMS, DEFAULT_WINDOW_SIZE, INITIAL_APPEARANCE_MODE, DEFAULT_COLOR_THEME, DEFAULT_CHART_FIGSIZE
from ui_components import (
    SplashScreen, StatusPanel, PositionsPanel, HistoryPanel, ChartPanel,
    AccountInfoPanel, TradingControlsPanel
)

# Set CustomTkinter appearance settings
ctk.set_appearance_mode(INITIAL_APPEARANCE_MODE)
ctk.set_default_color_theme(DEFAULT_COLOR_THEME)


class TradingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Hide the main window until splash screen is done
        self.withdraw()
        print("Main window withdrawn")

        try:
            # Theme state variable
            self.appearance_mode = ctk.StringVar(value=INITIAL_APPEARANCE_MODE)

            # Auto-trading state variables
            self.autotrade_enabled = ctk.BooleanVar(value=False)
            self.selected_algorithm = ctk.StringVar(value="momentum")
            self.scan_interval = ctk.IntVar(value=15)  # minutes
            self.risk_level = ctk.StringVar(value="medium")
            self.autotrade_timer = None  # For tracking the scheduled task
            self.position_refresh_timer = None  # For tracking position updates

            # Set up window
            self.title("AlgoTrade Simulator - Paper Trading Platform")
            self.geometry(DEFAULT_WINDOW_SIZE)
            print("Window configured")

            # Protocol for window closing
            self.protocol("WM_DELETE_WINDOW", self.on_closing)

            # --- Create Menu ---
            self.create_menu()
            print("Menu created")

            # Initialize database
            db.initialize_database()
            print("Database initialized")

            # Create matplotlib figure first, so it's available for theme application
            self.fig, self.ax = plt.subplots(figsize=DEFAULT_CHART_FIGSIZE)
            # Initial minimal setup
            self.ax.set_title("Enter a ticker symbol")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Price")
            print("Chart initialized")

            # --- Main Layout ---
            # Use a main frame to organize the layout
            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Configure grid layout with 2 columns
            self.main_frame.grid_columnconfigure(
                0, weight=1)  # Left column (30%)
            self.main_frame.grid_columnconfigure(
                1, weight=3)  # Right column (70%)
            self.main_frame.grid_rowconfigure(0, weight=1)     # Full height
            print("Main frame configured")

            # --- Left Panel ---
            left_frame = ctk.CTkFrame(self.main_frame)
            left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            left_frame.grid_rowconfigure(0, weight=0)  # Account Info
            left_frame.grid_rowconfigure(1, weight=0)  # Trading Controls
            left_frame.grid_rowconfigure(2, weight=1)  # Status Messages

            # --- Right Panel ---
            right_frame = ctk.CTkFrame(self.main_frame)
            right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            right_frame.grid_rowconfigure(0, weight=2)  # Chart
            right_frame.grid_rowconfigure(
                1, weight=1)  # Positions/History Tabs
            print("Panels configured")

            # --- Initialize UI Components ---
            self.init_ui_components(left_frame, right_frame)
            print("UI components initialized")

            # --- Apply initial theme ---
            self.apply_theme(INITIAL_APPEARANCE_MODE)
            print("Theme applied")

            # --- Initial Data Load ---
            self.update_account_display_threaded()
            self.update_positions_display()
            self.update_history_display()
            print("Initial data loaded")

            # Show splash screen - main window will be shown when splash is done
            self.splash_screen = SplashScreen(self, self.show_main_window)
            self.splash_screen.show()
            print("Splash screen shown")

            print("App Initialized.")

        except Exception as e:
            import traceback
            error_msg = f"Error during app initialization: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)

            # Try to show error dialog
            try:
                from tkinter import messagebox
                self.deiconify()  # Force show window to display the error
                messagebox.showerror("Initialization Error", error_msg)
            except:
                pass

    def init_ui_components(self, left_frame, right_frame):
        """Initialize all UI components"""
        # Account info panel
        self.account_panel = AccountInfoPanel(
            left_frame,
            self.appearance_mode,
            self.update_account_display_threaded
        )

        # Trading controls panel
        self.trading_panel = TradingControlsPanel(
            left_frame,
            self.appearance_mode,
            self.execute_buy_threaded,
            self.execute_sell_threaded
        )

        # Status panel
        self.status_panel = StatusPanel(
            left_frame,
            self.appearance_mode,
            self.autotrade_enabled,
            self.selected_algorithm,
            self.show_autotrade_settings
        )

        # Chart panel
        self.chart_panel = ChartPanel(
            right_frame,
            self.appearance_mode,
            self.fig,
            self.ax,
            self.fetch_chart_data_threaded
        )

        # Positions panel
        tabview = ctk.CTkTabview(right_frame)
        tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        positions_tab = tabview.add("Positions")
        history_tab = tabview.add("History")

        self.positions_panel = PositionsPanel(
            positions_tab,
            self.appearance_mode,
            self.handle_position_refresh
        )

        # History panel
        self.history_panel = HistoryPanel(
            history_tab,
            self.appearance_mode
        )

        # Store references to key UI elements
        self.ticker_entry = self.trading_panel.ticker_entry
        self.quantity_entry = self.trading_panel.quantity_entry
        self.buy_button = self.trading_panel.buy_button
        self.sell_button = self.trading_panel.sell_button
        self.status_text = self.status_panel.status_text
        self.positions_tree = self.positions_panel.tree
        self.history_tree = self.history_panel.tree

    def show_main_window(self):
        """Show main window after splash screen is done"""
        self.deiconify()
        self.update()  # Force update to prevent visual glitches

    def create_menu(self):
        """Create the application menu"""
        menubar = Menu(self)
        self.configure(menu=menubar)

        # File Menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Reset Database",
                              command=self.confirm_reset_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # View Menu
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Data",
                              command=self.refresh_all_data)
        view_menu.add_separator()

        # Theme submenu
        theme_menu = Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(label="Light", variable=self.appearance_mode,
                                   value="light", command=lambda: self.apply_theme("light"))
        theme_menu.add_radiobutton(label="Dark", variable=self.appearance_mode,
                                   value="dark", command=lambda: self.apply_theme("dark"))

        # Help Menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation",
                              command=self.show_documentation)

    def confirm_reset_database(self):
        """Confirm and reset the database"""
        result = messagebox.askyesno(
            "Reset Database", "This will reset ALL trading data including positions and history. Continue?")
        if result:
            self.reset_database()

    def reset_database(self):
        """Reset the database to initial state"""
        try:
            # Close database connections
            db.clear_cache()

            # Force a new database creation
            import os
            if os.path.exists(db.DATABASE_FILE):
                os.remove(db.DATABASE_FILE)

            # Reinitialize database
            db.initialize_database()

            # Refresh all displays
            self.refresh_all_data()

            self.add_status_message("Database reset successfully.")
        except Exception as e:
            self.add_status_message(
                f"Error resetting database: {e}", error=True)

    def refresh_all_data(self):
        """Refresh all data displays"""
        self.update_account_display_threaded()
        self.update_positions_display()
        self.update_history_display()
        self.add_status_message("All data refreshed.")

    def show_about(self):
        """Show about dialog"""
        about_text = (
            "AlgoTrade Simulator\n\n"
            "Version 1.0\n\n"
            "A paper trading platform for algorithmic trading simulation.\n\n"
            "© 2024 AlgoTrade"
        )
        messagebox.showinfo("About AlgoTrade Simulator", about_text)

    def show_documentation(self):
        """Show documentation dialog"""
        doc_text = (
            "AlgoTrade Simulator Documentation\n\n"
            "Quick Start:\n"
            "1. Enter a ticker symbol in the trading panel\n"
            "2. Enter a quantity to buy or sell\n"
            "3. Click BUY or SELL to execute a trade\n"
            "4. View your positions and trade history in the tabs\n\n"
            "Auto-Trading:\n"
            "1. Configure auto-trading settings\n"
            "2. Enable auto-trading to execute trades automatically\n\n"
            "For more information, visit the help website."
        )
        messagebox.showinfo("Documentation", doc_text)

    def apply_theme(self, mode=None):
        """Apply theme to the application"""
        if mode is None:
            mode = self.appearance_mode.get()

        try:
            # Set appearance mode
            ctk.set_appearance_mode(mode)

            # Apply theme to chart
            self.chart_panel.apply_theme(mode)

            # Update autotrade indicator
            self.status_panel.update_indicator()

            # Apply treeview styles
            self.positions_panel.apply_treeview_style()
            self.history_panel.apply_treeview_style()

            self.add_status_message(f"Theme '{mode}' applied.")

            # Force update of UI elements
            self.update()

            # Refresh all treeviews to ensure proper styling
            self.update_positions_display()
            self.update_history_display()

        except Exception as e:
            self.add_status_message(f"Error applying theme: {e}")

    def update_scan_interval_display(self):
        """Update the displayed scan interval"""
        # Update interval display if needed
        pass

    def update_autotrade_indicator(self):
        """Update the autotrade indicator label"""
        self.status_panel.update_indicator()

    def show_autotrade_settings(self):
        """Show auto-trade settings dialog"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Auto-Trading Settings")
        settings_window.geometry("400x350")
        settings_window.transient(self)  # Set to be on top of the main window
        settings_window.grab_set()  # Modal window

        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]
        settings_window.configure(fg_color=colors["bg"])

        # Main frame
        frame = ctk.CTkFrame(
            settings_window, fg_color=colors["bg_widget"], corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Auto-Trading Configuration",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=colors["fg"]
        )
        title.pack(pady=(20, 15))

        # Enable/Disable toggle
        toggle_frame = ctk.CTkFrame(frame, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=20, pady=10)

        toggle_label = ctk.CTkLabel(
            toggle_frame,
            text="Enable Auto-Trading:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["fg"]
        )
        toggle_label.pack(side="left")

        toggle_switch = ctk.CTkSwitch(
            toggle_frame,
            variable=self.autotrade_enabled,
            onvalue=True,
            offvalue=False,
            command=self.update_autotrade_indicator
        )
        toggle_switch.pack(side="right")

        # Algorithm selection
        algo_frame = ctk.CTkFrame(frame, fg_color="transparent")
        algo_frame.pack(fill="x", padx=20, pady=10)

        algo_label = ctk.CTkLabel(
            algo_frame,
            text="Trading Algorithm:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["fg"]
        )
        algo_label.pack(anchor="w")

        # Create algorithm selection dropdown
        algorithms = list(TRADING_ALGORITHMS.keys())
        algo_dropdown = ctk.CTkOptionMenu(
            algo_frame,
            values=algorithms,
            variable=self.selected_algorithm,
            width=200,
            dynamic_resizing=False
        )
        algo_dropdown.pack(anchor="w", pady=(5, 0))

        # Scan interval setting
        interval_frame = ctk.CTkFrame(frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=20, pady=10)

        interval_label = ctk.CTkLabel(
            interval_frame,
            text="Scan Interval (minutes):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["fg"]
        )
        interval_label.pack(anchor="w")

        interval_slider = ctk.CTkSlider(
            interval_frame,
            from_=1,
            to=60,
            variable=self.scan_interval,
            width=200
        )
        interval_slider.pack(anchor="w", pady=(5, 0))

        interval_value = ctk.CTkLabel(
            interval_frame,
            textvariable=self.scan_interval,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["fg"]
        )
        interval_value.pack(anchor="w", pady=(5, 0))

        # Risk level
        risk_frame = ctk.CTkFrame(frame, fg_color="transparent")
        risk_frame.pack(fill="x", padx=20, pady=10)

        risk_label = ctk.CTkLabel(
            risk_frame,
            text="Risk Level:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=colors["fg"]
        )
        risk_label.pack(anchor="w")

        risk_options = ctk.CTkFrame(risk_frame, fg_color="transparent")
        risk_options.pack(anchor="w", pady=(5, 0))

        risk_low = ctk.CTkRadioButton(
            risk_options,
            text="Low",
            variable=self.risk_level,
            value="low"
        )
        risk_low.pack(side="left", padx=(0, 10))

        risk_medium = ctk.CTkRadioButton(
            risk_options,
            text="Medium",
            variable=self.risk_level,
            value="medium"
        )
        risk_medium.pack(side="left", padx=10)

        risk_high = ctk.CTkRadioButton(
            risk_options,
            text="High",
            variable=self.risk_level,
            value="high"
        )
        risk_high.pack(side="left", padx=10)

        # Apply button
        apply_button = ctk.CTkButton(
            frame,
            text="Apply Settings",
            command=lambda: [
                self.update_autotrade_indicator(), settings_window.destroy()]
        )
        apply_button.pack(pady=20)

    def execute_buy_threaded(self):
        """Execute a buy trade in a background thread"""
        ticker = self.ticker_entry.get().strip().upper()
        try:
            quantity = int(self.quantity_entry.get().strip())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError as e:
            self.add_status_message(f"Invalid quantity: {str(e)}", error=True)
            return

        if not ticker:
            self.add_status_message(
                "Please enter a valid ticker symbol", error=True)
            return

        # Disable buttons during operation
        self.buy_button.configure(state="disabled")
        self.sell_button.configure(state="disabled")

        # Show status message
        self.add_status_message(
            f"Executing BUY order for {quantity} shares of {ticker}...")

        # Execute trade in background thread using the utility function
        def callback(result):
            # Handle trade result
            if result and 'success' in result and result['success']:
                message = f"Buy order executed: {quantity} shares of {ticker} at ${result['price']:.2f}"
                is_error = False
            else:
                message = f"Error executing buy order: {result.get('message', 'Unknown error')}"
                is_error = True

            # Update UI in main thread
            self.after(0, lambda: self.add_status_message(
                message, error=is_error))
            self.after(0, lambda: self.update_account_display_threaded())
            self.after(0, lambda: self.update_positions_display())
            self.after(0, lambda: self.update_history_display())
            self.after(0, lambda: self.buy_button.configure(state="normal"))
            self.after(0, lambda: self.sell_button.configure(state="normal"))

        tl.execute_buy_async(ticker, quantity, callback)

    def execute_sell_threaded(self):
        """Execute a sell trade in a background thread"""
        ticker = self.ticker_entry.get().strip().upper()
        try:
            quantity = int(self.quantity_entry.get().strip())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError as e:
            self.add_status_message(f"Invalid quantity: {str(e)}", error=True)
            return

        if not ticker:
            self.add_status_message(
                "Please enter a valid ticker symbol", error=True)
            return

        # Disable buttons during operation
        self.buy_button.configure(state="disabled")
        self.sell_button.configure(state="disabled")

        # Show status message
        self.add_status_message(
            f"Executing SELL order for {quantity} shares of {ticker}...")

        # Execute trade in background thread using the utility function
        def callback(result):
            # Handle trade result
            if result and 'success' in result and result['success']:
                message = f"Sell order executed: {quantity} shares of {ticker} at ${result['price']:.2f}, P/L: ${result['pnl']:.2f}"
                is_error = False
            else:
                message = f"Error executing sell order: {result.get('message', 'Unknown error')}"
                is_error = True

            # Update UI in main thread
            self.after(0, lambda: self.add_status_message(
                message, error=is_error))
            self.after(0, lambda: self.update_account_display_threaded())
            self.after(0, lambda: self.update_positions_display())
            self.after(0, lambda: self.update_history_display())
            self.after(0, lambda: self.buy_button.configure(state="normal"))
            self.after(0, lambda: self.sell_button.configure(state="normal"))

        tl.execute_sell_async(ticker, quantity, callback)

    def fetch_chart_data_threaded(self, event=None):
        """Start data fetching in a background thread"""
        # Get the ticker symbol from the entry field
        ticker = self.ticker_entry.get().strip().upper()

        if not ticker:
            self.add_status_message(
                "Please enter a valid ticker symbol", error=True)
            return

        # Show loading status
        self.add_status_message(f"Fetching data for {ticker}...")

        # Disable the button during data fetch
        self.chart_panel.chart_update_button.configure(state="disabled")

        # Start data fetching in a background thread
        utils.run_in_thread(self._fetch_chart_data, ticker)

    def _fetch_chart_data(self, ticker):
        """Fetch stock data in background thread and update UI in main thread"""
        try:
            # Fetch stock data using our stock_data module
            data = sd.fetch_stock_data(ticker)

            # Update the UI in the main thread
            self.after(0, lambda: self._update_chart(ticker, data))
            self.after(0, lambda: self.add_status_message(
                f"Data loaded for {ticker}"))

        except Exception as e:
            # Handle any errors and update UI
            error_msg = f"Error fetching data for {ticker}: {str(e)}"
            self.after(0, lambda: self.add_status_message(
                error_msg, error=True))

        finally:
            # Re-enable the button
            self.after(
                0, lambda: self.chart_panel.chart_update_button.configure(state="normal"))

    def _update_chart(self, ticker, data):
        """Update the chart with the fetched data"""
        if data.empty:
            self.add_status_message(
                f"No data available for {ticker}", error=True)
            return

        # Clear the previous chart
        self.ax.clear()

        # Get current theme colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Plot the data
        self.ax.plot(data.index, data['Close'],
                     color=colors["plot_line"], linewidth=2)

        # Set title and labels
        self.ax.set_title(f"{ticker} - Price Chart")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Price ($)")

        # Reapply grid settings
        self.ax.grid(True, linestyle='--', alpha=0.3,
                     color=colors["chart_grid"])

        # Format x-axis to show dates nicely
        self.fig.autofmt_xdate()

        # Update the canvas
        self.chart_panel.canvas.draw()

    def update_account_display_threaded(self):
        """Update account information in a background thread"""
        utils.run_in_thread(self._update_account_display)

    def _update_account_display(self):
        """Update account information from the database"""
        try:
            # Get account information from database
            account_info = db.get_account_info()

            # Update UI in main thread
            self.after(
                0, lambda: self.account_panel.update_account_info(account_info))
            self.after(0, lambda: self.add_status_message(
                "Account information updated"))

        except Exception as e:
            error_msg = f"Error updating account info: {str(e)}"
            self.after(0, lambda: self.add_status_message(
                error_msg, error=True))

    def update_positions_display(self):
        """Update the positions treeview with current position data"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)

            # Get current positions from database
            positions = db.get_positions()

            # Add positions to treeview
            for i, position in enumerate(positions):
                symbol = position['symbol']
                quantity = position['quantity']
                entry_price = position['entry_price']
                current_price = position['current_price']
                position_value = position['position_value']
                pnl = position['pnl']
                pnl_percent = position['pnl_percent']

                # Add row to treeview with alternating colors
                tag = 'even' if i % 2 == 0 else 'odd'
                profit_tag = 'gain' if pnl >= 0 else 'loss'
                self.positions_tree.insert('', 'end', values=(
                    symbol,
                    quantity,
                    f"${entry_price:.2f}",
                    f"${current_price:.2f}",
                    f"${position_value:.2f}",
                    f"${pnl:.2f}",
                    f"{pnl_percent:.2f}%"
                ), tags=(tag, profit_tag))

            # Add status message if auto-refresh is enabled
            if self.positions_panel.auto_refresh_enabled.get():
                current_time = time.strftime("%H:%M:%S", time.localtime())
                self.add_status_message(f"Positions updated at {current_time}")

        except Exception as e:
            self.add_status_message(
                f"Error updating positions: {str(e)}", error=True)

    def update_history_display(self):
        """Update the history treeview with trade history data"""
        try:
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            # Get trade history from database
            trades = db.get_trade_history()

            # Add trades to treeview
            for i, trade in enumerate(trades):
                timestamp = trade['timestamp']
                symbol = trade['symbol']
                side = trade['side'].upper()
                quantity = trade['quantity']
                price = trade['price']
                total = trade['total']

                # Add row to treeview with alternating colors
                tag = 'even' if i % 2 == 0 else 'odd'
                side_tag = 'buy' if side == 'BUY' else 'sell'
                self.history_tree.insert('', 'end', values=(
                    timestamp,
                    symbol,
                    side,
                    quantity,
                    f"${price:.2f}",
                    f"${total:.2f}"
                ), tags=(tag, side_tag))

            self.add_status_message("Trade history updated")

        except Exception as e:
            self.add_status_message(
                f"Error updating trade history: {str(e)}", error=True)

    def add_status_message(self, message, error=False):
        """Add a message to the status text widget with timestamp"""
        self.status_panel.add_message(message, error)

    def handle_position_refresh(self, enabled=False, interval=10, single=False):
        """Handle position refresh timer management"""
        # Cancel any existing timer
        if self.position_refresh_timer:
            self.after_cancel(self.position_refresh_timer)
            self.position_refresh_timer = None

        # For a single manual refresh
        if single:
            self.update_positions_display()
            self.add_status_message("Positions manually refreshed")
            return

        # For auto-refresh
        if enabled:
            # Convert interval to milliseconds
            interval_ms = interval * 1000

            # Start the first refresh
            self.update_positions_display()
            self.add_status_message(
                f"Auto-refresh enabled: updating every {interval} seconds")

            # Schedule next refresh
            self.position_refresh_timer = self.after(
                interval_ms, lambda: self.schedule_next_refresh(interval_ms))
        else:
            self.add_status_message("Auto-refresh disabled")

    def schedule_next_refresh(self, interval_ms):
        """Schedule the next position refresh"""
        # Update positions
        self.update_positions_display()

        # Schedule next update if auto-refresh is still enabled
        if self.positions_panel.auto_refresh_enabled.get():
            self.position_refresh_timer = self.after(
                interval_ms, lambda: self.schedule_next_refresh(interval_ms))
        else:
            self.position_refresh_timer = None

    def on_closing(self):
        """Handle application cleanup when closing"""
        try:
            # Cancel any active timers
            if self.autotrade_timer:
                self.after_cancel(self.autotrade_timer)

            if self.position_refresh_timer:
                self.after_cancel(self.position_refresh_timer)

            # Close database connections
            db.clear_cache()

            # Destroy the window
            self.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.destroy()


if __name__ == "__main__":
    app = TradingApp()
    app.mainloop()

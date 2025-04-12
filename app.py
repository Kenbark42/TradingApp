import tkinter as tk
from tkinter import messagebox, simpledialog, Menu, ttk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import threading  # To run data fetching/trading in background threads
import time
import random  # For demo trading algorithms

# Import our custom modules
import database as db
import stock_data as sd
import trading_logic as tl

# Set CustomTkinter appearance settings
ctk.set_appearance_mode("dark")  # Default mode: "dark" or "light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

# Theme Color Constants - Refined for Modern Trading UI
COLORS = {
    "light": {
        "gain": "#00C853",  # Vibrant green for positive values
        "loss": "#FF3D00",  # Vibrant red for negative values
        "chart_grid": "#E0E0E0",  # Subtle grid lines for light mode
        "plot_line": "#1E88E5",  # Refined blue for plot line in light mode
        "bg": "#F9FAFB",  # Slightly off-white background
        "fg": "#1F2937",  # Dark gray text (nearly black)
        "bg_widget": "#FFFFFF",  # Pure white for widget background
        "fg_widget": "#1F2937",  # Consistent text color
        "bg_accent": "#F3F4F6",  # Very light gray accent
        "fg_accent": "#6B7280",  # Medium gray for secondary text
        "button_bg": "#4F46E5",  # Indigo primary button
        "button_fg": "#FFFFFF",  # White button text
        "button_active": "#4338CA",  # Darker indigo for hover
        "focus_color": "#4F46E5",  # Consistent with button color
        "border": "#E5E7EB",  # Very light gray border
        "accent_button_bg": "#4F46E5",  # Same as primary button
        "accent_button_fg": "#FFFFFF",  # White text
    },
    "dark": {
        "gain": "#00E676",  # Electric green for positive values
        "loss": "#FF5252",  # Bright red for negative values
        "chart_grid": "#292D3E",  # Subtle dark grid lines
        "plot_line": "#64B5F6",  # Bright blue plot line for visibility
        "bg": "#0F172A",  # Rich navy blue-black
        "fg": "#E2E8F0",  # Off-white text
        "bg_widget": "#1E293B",  # Slightly lighter navy for widgets
        "fg_widget": "#E2E8F0",  # Consistent text color
        "bg_accent": "#334155",  # Medium slate for accents
        "fg_accent": "#94A3B8",  # Medium gray-blue for secondary text
        "button_bg": "#6366F1",  # Vibrant indigo button
        "button_fg": "#FFFFFF",  # White text
        "button_active": "#4F46E5",  # Slightly darker indigo for hover
        "focus_color": "#6366F1",  # Match button color
        "border": "#334155",  # Medium slate for borders
        "accent_button_bg": "#6366F1",  # Same as primary
        "accent_button_fg": "#FFFFFF",  # White text
    }
}

# Define trading algorithms to use with the autotrade feature
TRADING_ALGORITHMS = {
    "momentum": "Momentum Trading (Follows trends)",
    "mean_reversion": "Mean Reversion (Buys dips, sells rallies)",
    "ml_prediction": "ML-based Prediction (Uses machine learning models)",
    "volatility_breakout": "Volatility Breakout (Triggers on price movements)",
    "pattern_recognition": "Pattern Recognition (Identifies chart patterns)"
}


class TradingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Hide the main window until splash screen is done
        self.withdraw()
        print("Main window withdrawn")

        try:
            # Theme state variable
            self.appearance_mode = ctk.StringVar(value="dark")

            # Auto-trading state variables
            self.autotrade_enabled = ctk.BooleanVar(value=False)
            self.selected_algorithm = ctk.StringVar(value="momentum")
            self.scan_interval = ctk.IntVar(value=15)  # minutes
            self.risk_level = ctk.StringVar(value="medium")
            self.autotrade_timer = None  # For tracking the scheduled task

            # Set up window
            self.title("AlgoTrade Simulator - Paper Trading Platform")
            self.geometry("1200x800")
            print("Window configured")

            # --- Create Menu ---
            self.create_menu()
            print("Menu created")

            # Initialize database
            db.initialize_database()
            print("Database initialized")

            # Create matplotlib figure first, so it's available for theme application
            self.fig, self.ax = plt.subplots(figsize=(8, 4))
            # Initial minimal setup
            self.ax.set_title("Enter a ticker symbol")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Price")
            self.apply_chart_theme("dark")  # Apply initial chart theme
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

            # --- Widgets ---
            self.create_account_info_widgets(left_frame)
            self.create_trading_widgets(left_frame)
            self.create_status_widgets(left_frame)
            self.create_chart_widgets(right_frame)
            self.create_positions_widgets(right_frame)
            self.create_history_widgets(right_frame)
            print("Widgets created")

            # --- Initial Data Load ---
            self.update_account_display_threaded()
            self.update_positions_display()
            self.update_history_display()
            print("Initial data loaded")

            # Show splash screen - main window will be shown when splash is done
            self.show_splash_screen()
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

    def show_splash_screen(self):
        """Display a modern splash screen with animation while the app loads"""
        # Get colors for dark theme
        colors = COLORS["dark"]

        splash = ctk.CTkToplevel(self)
        splash.title("Loading...")
        splash.overrideredirect(True)  # No window decorations
        splash.attributes("-alpha", 0.0)  # Start transparent for fade-in

        # Calculate position for center of screen
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        width = 550
        height = 320
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")

        # Configure dark theme background
        splash.configure(fg_color=colors["bg"])

        # Main content frame with subtle border
        content_frame = ctk.CTkFrame(
            splash, fg_color=colors["bg"], border_width=1, border_color=colors["border"])
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo/name with modern typography
        app_name = ctk.CTkLabel(content_frame, text="ALGOTRADE",
                                font=ctk.CTkFont(
                                    family="Segoe UI", size=32, weight="bold"),
                                text_color=colors["accent_button_bg"])
        app_name.pack(pady=(40, 0))

        simulator_label = ctk.CTkLabel(content_frame, text="SIMULATOR",
                                       font=ctk.CTkFont(
                                           family="Segoe UI", size=14, weight="normal"),
                                       text_color=colors["fg_accent"])
        simulator_label.pack(pady=(0, 20))

        # Divider line
        divider = ctk.CTkFrame(content_frame, height=1,
                               fg_color=colors["border"])
        divider.pack(fill="x", padx=100, pady=10)

        # Tagline with more minimal styling
        tagline = ctk.CTkLabel(content_frame, text="ADVANCED TRADING PLATFORM",
                               font=ctk.CTkFont(family="Segoe UI", size=10),
                               text_color=colors["fg_accent"])
        tagline.pack(pady=(5, 30))

        # Modern progress bar with rounded corners
        progress_container = ctk.CTkFrame(
            content_frame, fg_color="transparent")
        progress_container.pack(fill="x", padx=70, pady=10)

        # Status text
        self.loading_status = ctk.CTkLabel(progress_container, text="INITIALIZING",
                                           font=ctk.CTkFont(
                                               family="Segoe UI", size=10),
                                           text_color=colors["fg_accent"])
        self.loading_status.pack(anchor="w", padx=0, pady=(0, 5))

        # Modern slim progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_container, height=4)
        self.progress_bar.pack(fill="x")
        self.progress_bar.configure(
            mode="indeterminate",
            progress_color=colors["accent_button_bg"],
            fg_color=colors["bg_accent"]
        )

        # Version info
        version = ctk.CTkLabel(content_frame, text="v1.0.0",
                               font=ctk.CTkFont(family="Segoe UI", size=8),
                               text_color=colors["fg_accent"])
        version.pack(side="bottom", pady=15)

        # Start animations
        self._animate_splash_fade_in(splash)
        self.progress_bar.start()
        self._animate_loading_text()

        # Function to properly close splash and show main window after delay
        def close_splash_and_show_main():
            try:
                # Cancel any ongoing animations
                if hasattr(self, '_pulse_after_id'):
                    self.after_cancel(self._pulse_after_id)

                # Fade out the splash screen
                self._animate_splash_fade_out(splash)

                # Show the main window after fade out
                def after_fadeout():
                    splash.destroy()
                    self.deiconify()  # Show the main window
                    self.update()  # Force update to ensure window appears

                    # Center the main window
                    self.center_window()

                    # Display welcome message after a short delay
                    self.after(500, self.show_welcome_dialog)

                    print("Main window displayed.")

                # Wait for fade out animation to complete
                self.after(500, after_fadeout)

            except Exception as e:
                print(f"Error showing main window: {e}")
                # Fallback to ensure main window is shown
                splash.destroy()
                self.deiconify()
                self.update()

        # Display the splash screen for a short time
        self.after(2500, close_splash_and_show_main)

    def _animate_loading_text(self):
        """Animate the loading text with changing messages"""
        loading_messages = [
            "INITIALIZING SYSTEM",
            "LOADING MARKET DATA",
            "CONNECTING TO EXCHANGE",
            "CONFIGURING ALGORITHMS",
            "PREPARING TRADING ENVIRONMENT"
        ]

        current_index = getattr(self, '_loading_msg_index', 0)
        self.loading_status.configure(text=loading_messages[current_index])

        # Update index for next call
        self._loading_msg_index = (current_index + 1) % len(loading_messages)

        # Schedule next update
        self._pulse_after_id = self.after(500, self._animate_loading_text)

    def _animate_splash_fade_in(self, window, from_alpha=0.0, to_alpha=1.0, duration=400, steps=20):
        """Smoothly fade in the splash screen"""
        current_alpha = from_alpha
        alpha_step = (to_alpha - from_alpha) / steps
        step_time = duration // steps

        def _fade_step():
            nonlocal current_alpha
            if current_alpha < to_alpha:
                current_alpha += alpha_step
                window.attributes("-alpha", current_alpha)
                window.after(step_time, _fade_step)

        _fade_step()

    def _animate_splash_fade_out(self, window, from_alpha=1.0, to_alpha=0.0, duration=300, steps=15):
        """Smoothly fade out the splash screen"""
        current_alpha = from_alpha
        alpha_step = (from_alpha - to_alpha) / steps
        step_time = duration // steps

        def _fade_step():
            nonlocal current_alpha
            if current_alpha > to_alpha:
                current_alpha -= alpha_step
                window.attributes("-alpha", current_alpha)
                window.after(step_time, _fade_step)

        _fade_step()

    def center_window(self):
        """Center the application window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"+{x}+{y}")

        # After showing the main window, apply theme
        self.after(100, self.apply_theme)

    def show_welcome_dialog(self):
        """Display a welcome dialog with key features"""
        try:
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

            welcome = ctk.CTkToplevel(self)
            welcome.title("Welcome to AlgoTrade Simulator")
            welcome.configure(fg_color=colors["bg"])
            welcome.transient(self)  # Set to be on top of the main window
            welcome.grab_set()  # Modal window

            # Set size and position
            welcome.geometry("650x500")
            welcome.resizable(False, False)

            # Header
            header_frame = ctk.CTkFrame(
                welcome, fg_color=colors["bg_accent"], height=70)
            header_frame.pack(fill="x")

            header = ctk.CTkLabel(header_frame, text="Welcome to AlgoTrade Simulator",
                                  font=ctk.CTkFont(
                                      family="Segoe UI", size=22, weight="bold"),
                                  text_color=colors["accent_button_bg"])
            header.pack(pady=15)

            # Content
            content_frame = ctk.CTkFrame(
                welcome, fg_color=colors["bg"])
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)

            # Introduction
            intro = ctk.CTkLabel(content_frame,
                                 text="Explore the markets without financial risk using our advanced trading simulator.",
                                 font=ctk.CTkFont(family="Segoe UI", size=11),
                                 text_color=colors["fg"], wraplength=590, justify="left")
            intro.pack(anchor="w", pady=(10, 20))

            # Features list in a modern card-like layout
            features_frame = ctk.CTkFrame(content_frame, fg_color=colors["bg"])
            features_frame.pack(fill="x", pady=10)

            # Create a 2x3 grid of feature cards
            features = [
                {"icon": "🚀", "title": "Paper Trading",
                    "desc": "Execute trades with virtual money"},
                {"icon": "📊", "title": "Real-time Data",
                    "desc": "Visualize intraday price movements"},
                {"icon": "🤖", "title": "Automated Trading",
                    "desc": "Algorithmic trading strategies"},
                {"icon": "💼", "title": "Portfolio Management",
                    "desc": "Track positions and balance"},
                {"icon": "📈", "title": "Performance Tracking",
                    "desc": "Monitor your trading results"},
                {"icon": "🌓", "title": "Light/Dark Mode",
                    "desc": "Customize your environment"}
            ]

            # Configure grid
            features_frame.columnconfigure(0, weight=1)
            features_frame.columnconfigure(1, weight=1)

            # Create feature cards
            row, col = 0, 0
            for feature in features:
                # Card frame with subtle border
                card = ctk.CTkFrame(features_frame, fg_color=colors["bg_widget"],
                                    border_width=1,
                                    border_color=colors["border"])

                # Emoji icon
                icon = ctk.CTkLabel(card, text=feature["icon"],
                                    font=ctk.CTkFont(
                                        family="Segoe UI", size=20),
                                    text_color=colors["accent_button_bg"])
                icon.pack(side=tk.LEFT, padx=(15, 10), pady=12)

                # Text content
                text_frame = ctk.CTkFrame(card, fg_color=colors["bg_widget"])
                text_frame.pack(side=tk.LEFT, fill="x", expand=True)

                title = ctk.CTkLabel(text_frame, text=feature["title"],
                                     font=ctk.CTkFont(
                    family="Segoe UI", size=10, weight="bold"),
                    text_color=colors["fg"], anchor="w")
                title.pack(fill="x")

                desc = ctk.CTkLabel(text_frame, text=feature["desc"],
                                    font=ctk.CTkFont(
                                        family="Segoe UI", size=9),
                                    text_color=colors["fg_accent"], anchor="w")
                desc.pack(fill="x")

                # Position in grid
                card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

                # Update position
                col += 1
                if col > 1:
                    col = 0
                    row += 1

            # Tip section
            tip_frame = ctk.CTkFrame(
                content_frame, fg_color=colors["bg_accent"])
            tip_frame.pack(fill="x", pady=(20, 0), padx=20)

            tip_title = ctk.CTkLabel(tip_frame,
                                     text="Getting Started",
                                     font=ctk.CTkFont(
                                         family="Segoe UI", size=10, weight="bold"),
                                     text_color=colors["fg"], anchor="w")
            tip_title.pack(anchor="w", padx=20)

            tip = ctk.CTkLabel(tip_frame,
                               text="Enter a ticker symbol (e.g., AAPL, MSFT, GOOGL) in the Trade Execution panel and click 'Update Chart' to begin exploring the markets.",
                               font=ctk.CTkFont(family="Segoe UI", size=9),
                               text_color=colors["fg_accent"], wraplength=590, justify="left")
            tip.pack(anchor="w", pady=(5, 0), padx=20)

            # Button frame
            button_frame = ctk.CTkFrame(welcome, fg_color=colors["bg"])
            button_frame.pack(fill="x", pady=20)

            # Use accent button style for a more prominent call to action
            close_button = ctk.CTkButton(button_frame, text="Start Trading",
                                         command=welcome.destroy, fg_color=colors[
                                             "accent_button_bg"], text_color=colors["accent_button_fg"],
                                         hover_color=colors["button_active"],
                                         width=15)
            close_button.pack()

            # After welcome dialog is closed, apply theme
            welcome.protocol("WM_DELETE_WINDOW", lambda: [
                             welcome.destroy(), self.after(100, self.apply_theme)])

        except Exception as e:
            import traceback
            error_msg = f"Error in welcome dialog: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.log_status(error_msg)
            messagebox.showerror("Error", error_msg)

    def force_complete_theme_refresh(self):
        """Force a complete refresh of theme across all widgets"""
        try:
            # Get current theme mode
            mode = self.appearance_mode.get()
            colors = COLORS["dark"] if mode == "dark" else COLORS["light"]

            # Apply theme to main application window and frames
            self.configure(fg_color=colors["bg"])

            # Recursively apply theme to all widgets
            self._apply_theme_recursively(self, colors)

            # Apply theme to chart
            self.apply_chart_theme(mode)

            # Force refresh of all treeviews
            self._apply_treeview_style(self.positions_tree, colors)
            self._apply_treeview_style(self.history_tree, colors)

            # Fix for treeview empty spaces
            self._fix_treeview_empty_space(colors)

            # Refresh all data displays
            self.update_account_display_threaded()
            self.update_positions_display()
            self.update_history_display()

            # Force update to render changes
            self.update_idletasks()

            # Apply theme to the canvas widget again to ensure chart background is correct
            if hasattr(self, 'canvas_widget'):
                self.canvas_widget.configure(bg=colors["bg_widget"])
                self.canvas.draw()

            self.add_status_message(f"Theme refreshed.")

        except Exception as e:
            print(f"Error in force_complete_theme_refresh: {e}")
            self.add_status_message(
                f"Error refreshing theme: {str(e)}", error=True)

    def _fix_treeview_empty_space(self, colors=None):
        """Fix the treeview white background in empty spaces"""
        if colors is None:
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

        # Style already set in _apply_treeview_style, just make sure containers are themed

        # Fix positions tree container
        if hasattr(self, 'positions_tree') and self.positions_tree.master:
            if isinstance(self.positions_tree.master, ctk.CTkFrame):
                self.positions_tree.master.configure(fg_color=colors["bg"])

        # Fix history tree container
        if hasattr(self, 'history_tree') and self.history_tree.master:
            if isinstance(self.history_tree.master, ctk.CTkFrame):
                self.history_tree.master.configure(fg_color=colors["bg"])

    def create_menu(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Demo Data",
                              command=self.load_demo_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Settings Menu
        settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        # Theme Submenu
        theme_menu = Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(
            label="Light", variable=self.appearance_mode, value="light", command=self.apply_theme)
        theme_menu.add_radiobutton(
            label="Dark", variable=self.appearance_mode, value="dark", command=self.apply_theme)

        # AutoTrading Submenu
        settings_menu.add_command(label="AutoTrading Settings",
                                  command=self.show_autotrade_settings)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Show Welcome",
                              command=self.show_welcome_dialog)

    def load_demo_data(self):
        """Load demo data to showcase the app's capabilities."""
        self.log_status("Loading demo data...")

        # Execute demo trades with popular tech stocks
        try:
            # First ensure DB is clean
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades")
            cursor.execute("DELETE FROM positions")
            cursor.execute("UPDATE account SET balance = initial_balance")
            conn.commit()
            conn.close()

            self.log_status("Executing demo trades...")

            # MSFT buy yesterday
            tl.execute_buy('MSFT', 15)

            # AAPL buy earlier, sell some for profit
            tl.execute_buy('AAPL', 20)
            tl.execute_sell('AAPL', 5)

            # GOOGL buy and hold
            tl.execute_buy('GOOGL', 5)

            # NVDA buy, then add more
            tl.execute_buy('NVDA', 10)
            tl.execute_buy('NVDA', 5)

            # META - made a profit
            tl.execute_buy('META', 8)
            tl.execute_sell('META', 8)

            # Tesla - experimented with a smaller position
            tl.execute_buy('TSLA', 3)

            # Update UI
            self.update_account_display()
            self.update_positions_display()
            self.update_history_display()

            # Show a popular ticker
            self.ticker_entry.delete(0, tk.END)
            self.ticker_entry.insert(0, "NVDA")
            self.fetch_chart_data_threaded()

            self.log_status("Demo data loaded successfully!")
            messagebox.showinfo(
                "Demo Data", "Demo trades have been loaded successfully.\n\nYou now have positions in several popular tech stocks and can continue trading.")

        except Exception as e:
            self.log_status(f"Error loading demo data: {e}")
            messagebox.showerror("Error", f"Failed to load demo data: {e}")

    def show_about(self):
        """Display information about the application"""
        try:
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

            about = ctk.CTkToplevel(self)
            about.title("About AlgoTrade Simulator")
            about.configure(fg_color=colors["bg"])
            about.transient(self)

            # Set size and position
            about.geometry("400x300")
            about.resizable(False, False)

            # Logo/Name
            title = ctk.CTkLabel(about, text="AlgoTrade Simulator",
                                 font=ctk.CTkFont(
                                     family="Segoe UI", size=16, weight="bold"),
                                 text_color=colors["accent_button_bg"])
            title.pack(pady=(20, 5))

            # Version
            version = ctk.CTkLabel(about, text="Version 1.0.0",
                                   font=ctk.CTkFont(
                                       family="Segoe UI", size=10),
                                   text_color=colors["fg"])
            version.pack()

            # Description
            description = ctk.CTkLabel(about,
                                       text="A professional paper trading platform for day traders. Analyze market data, execute simulated trades, and track performance without financial risk.",
                                       wraplength=350, justify="center",
                                       font=ctk.CTkFont(
                                           family="Segoe UI", size=10),
                                       text_color=colors["fg"])
            description.pack(pady=20)

            # Copyright
            copyright = ctk.CTkLabel(about, text="© 2024 AlgoTrade Inc.",
                                     font=ctk.CTkFont(
                                         family="Segoe UI", size=8),
                                     text_color=colors["fg"])
            copyright.pack(side="bottom", pady=10)

            # Close button
            close_button = ctk.CTkButton(
                about, text="Close", command=about.destroy)
            close_button.pack(side="bottom", pady=10)

        except Exception as e:
            import traceback
            error_msg = f"Error in about dialog: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.log_status(error_msg)
            messagebox.showerror("Error", error_msg)

    def apply_theme(self, mode=None):
        """Apply theme to the application"""
        if mode is None:
            mode = self.appearance_mode.get()

        colors = COLORS["dark"] if mode == "dark" else COLORS["light"]

        # Apply theme to main application window and frames
        try:
            self.configure(fg_color=colors["bg"])
            self.main_frame.configure(fg_color=colors["bg"])

            # Apply theme to all widgets
            self._apply_theme_recursively(self, colors)

            # Apply theme to chart
            self.apply_chart_theme(mode)

            # Apply theme to menu items
            self._style_menu(self.winfo_children(), colors)

            # Apply theme to treeviews
            if hasattr(self, 'positions_tree') and hasattr(self, 'history_tree'):
                self._apply_treeview_style(self.positions_tree, colors)
                self._apply_treeview_style(self.history_tree, colors)

                # Explicitly set tree container background colors
                if hasattr(self, 'positions_tree') and self.positions_tree.master:
                    if isinstance(self.positions_tree.master, ctk.CTkFrame):
                        self.positions_tree.master.configure(
                            fg_color=colors["bg"])

                if hasattr(self, 'history_tree') and self.history_tree.master:
                    if isinstance(self.history_tree.master, ctk.CTkFrame):
                        self.history_tree.master.configure(
                            fg_color=colors["bg"])

                # Force a redraw of all rows to apply new styling
                for tree in [self.positions_tree, self.history_tree]:
                    items = tree.get_children()
                    for i, item in enumerate(items):
                        values = tree.item(item, 'values')
                        tree.delete(item)
                        tag = 'even' if i % 2 == 0 else 'odd'
                        tree.insert('', i, values=values, tags=(tag,))

            # Apply theme to pnl label
            if hasattr(self, 'pnl_label'):
                self.pnl_label.configure(text_color=colors["fg"])

            # Apply theme to scan interval label
            self.update_scan_interval_display()

            # Apply theme to autotrade indicator
            self.update_autotrade_indicator()

            self.add_status_message(f"Theme '{mode}' applied.")
            # Force update of UI elements
            self.update()

            # Refresh all treeviews to ensure proper styling
            if hasattr(self, 'positions_tree'):
                self.update_positions_display()
            if hasattr(self, 'history_tree'):
                self.update_history_display()

        except Exception as e:
            self.add_status_message(f"Error applying theme: {e}")

    def _style_menu(self, widgets, colors):
        """Apply theme to menu items"""
        for widget in widgets:
            if isinstance(widget, Menu):
                # Standard Tkinter Menu only accepts certain parameters
                # fg_color and text_color are not valid for tk.Menu
                widget.configure(
                    background=colors["bg_widget"],
                    foreground=colors["fg_widget"],
                    activebackground=colors["button_active"],
                    activeforeground=colors["fg_widget"],
                    borderwidth=0,
                    activeborderwidth=0
                )
                # Apply to any cascaded menus
                for i in range(widget.index('end') + 1 if widget.index('end') is not None else 0):
                    try:
                        if widget.type(i) == 'cascade':
                            submenu = widget.nametowidget(
                                widget.entrycget(i, 'menu'))
                            if submenu:
                                self._style_menu([submenu], colors)
                    except Exception as e:
                        self.log_status(f"Error styling menu: {e}")
                        pass

    def _apply_theme_recursively(self, parent, colors):
        """Recursively apply theme to all tkinter widgets"""
        if parent is None:
            return

        # Apply to the parent if it's a standard tkinter widget
        self._apply_theme_to_widget(parent, colors)

        try:
            # Process all children
            for child in parent.winfo_children():
                if child is None:
                    continue

                if isinstance(child, tk.Widget):
                    # For standard Tkinter widgets (not CustomTkinter)
                    try:
                        if hasattr(child, 'configure') and not isinstance(child, ttk.Widget):
                            if 'background' in child.config():
                                child.configure(background=colors["bg_widget"])
                            if 'foreground' in child.config():
                                child.configure(foreground=colors["fg"])
                    except:
                        pass

                # Continue recursive processing
                self._apply_theme_recursively(child, colors)
        except Exception as e:
            print(f"Error in _apply_theme_recursively: {e}")

    def _apply_theme_to_widget(self, widget, colors):
        """Apply theme to a specific widget based on its type"""
        try:
            # Skip certain widget types
            if isinstance(widget, (tk.Menu, Menu)):
                return

            # Apply background to all widgets that support it
            if hasattr(widget, 'configure') and not isinstance(widget, ctk.CTk):
                if 'fg_color' in widget.configure():
                    widget.configure(fg_color=colors["bg"])

                # Handle specific widget types
                if isinstance(widget, ctk.CTkEntry):
                    widget.configure(
                        fg_color=colors["bg_widget"],
                        text_color=colors["fg_widget"],
                        insertbackground=colors["fg_widget"],  # Cursor color
                        highlightbackground=colors["border"],
                        highlightcolor=colors["focus_color"],
                        relief="solid",
                        borderwidth=1
                    )
                elif isinstance(widget, ctk.CTkTextbox):
                    # Custom styling for the status text
                    if hasattr(self, 'status_text') and widget == self.status_text:
                        widget.configure(
                            fg_color=colors["bg"],
                            text_color=colors["fg"],
                            insertbackground=colors["fg_widget"],
                            highlightbackground=colors["border"],
                            highlightcolor=colors["focus_color"],
                            relief="solid",
                            borderwidth=1
                        )
                    else:
                        widget.configure(
                            fg_color=colors["bg_widget"],
                            text_color=colors["fg_widget"],
                            insertbackground=colors["fg_widget"],
                            highlightbackground=colors["border"],
                            highlightcolor=colors["focus_color"]
                        )
                elif isinstance(widget, ctk.CTkLabel):
                    widget.configure(
                        fg_color=colors["fg"],
                        text_color=colors["fg"]
                    )
                elif isinstance(widget, ctk.CTkButton):
                    # Skip styling buy/sell buttons here, they have specific colors
                    if hasattr(self, 'buy_button') and widget == self.buy_button:
                        pass
                    elif hasattr(self, 'sell_button') and widget == self.sell_button:
                        pass
                    # Skip accent buttons like in welcome dialog
                    # Basic check
                    elif hasattr(widget, '_fg_color') and widget._fg_color == colors.get("accent_button_bg"):
                        pass
                    else:
                        widget.configure(
                            fg_color=colors["button_bg"],
                            text_color=colors["button_fg"],
                            # Use hover_color
                            hover_color=colors["button_active"]
                            # highlightbackground=colors["border"] # Not a standard CTkButton param
                        )
                elif isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color=colors["bg"])
                elif isinstance(widget, ctk.CTkToplevel):
                    widget.configure(fg_color=colors["bg"])
                elif isinstance(widget, ctk.CTkCanvas):
                    widget.configure(
                        fg_color=colors["bg_widget"],
                        text_color=colors["fg_widget"],
                        highlightbackground=colors["border"],
                        highlightcolor=colors["focus_color"]
                    )
                elif isinstance(widget, (ctk.CTkCheckButton, ctk.CTkCheckbutton)) or isinstance(widget, (ctk.CTkRadioButton, ctk.CTkRadiobutton)):
                    widget.configure(
                        fg_color=colors["bg"],
                        text_color=colors["fg"],
                        activebackground=colors["bg"],
                        activeforeground=colors["fg"],
                        selectcolor=colors["bg_widget"]
                    )
                elif isinstance(widget, ctk.CTkScale):
                    widget.configure(
                        fg_color=colors["bg"],
                        text_color=colors["fg"],
                        troughcolor=colors["bg_widget"],
                        activebackground=colors["button_active"]
                    )
        except Exception as e:
            # Just log the error but continue
            print(f"Error applying theme to widget {type(widget)}: {e}")

    def _apply_treeview_style(self, tree, colors=None):
        """Apply theme to a ttk.Treeview widget"""
        if colors is None:
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

        # Create a specific unique style for this treeview
        style = ttk.Style()

        # Configure the Treeview colors
        style.configure("Treeview",
                        background=colors["bg"],
                        foreground=colors["fg_widget"],
                        fieldbackground=colors["bg"],
                        borderwidth=0)

        # Configure the header
        style.configure("Treeview.Heading",
                        background=colors["bg_accent"],
                        foreground=colors["fg"],
                        relief="flat")

        # Configure selection colors
        style.map('Treeview',
                  background=[('selected', colors["accent_button_bg"])],
                  foreground=[('selected', colors["accent_button_fg"])])

        # Configure row tags for alternating colors
        tree.tag_configure('even', background=colors["bg"])
        tree.tag_configure('odd', background=colors["bg_accent"])

        # Apply alternating row colors to all items
        children = tree.get_children()
        for i, item in enumerate(children):
            tag = 'even' if i % 2 == 0 else 'odd'
            # Keep any existing tags
            current_tags = list(tree.item(item, 'tags'))
            # Remove even/odd tags
            current_tags = [
                t for t in current_tags if t not in ('even', 'odd')]
            tree.item(item, tags=current_tags + [tag])

    def create_account_info_widgets(self, parent):
        # Get current colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a frame with modern card-like styling
        frame = ctk.CTkFrame(
            parent, fg_color=colors["bg_widget"], corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 15), padx=5)
        frame.grid_columnconfigure(1, weight=1)

        # Add a title label with modern icon prefix
        header_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg_widget"], corner_radius=0)
        header_frame.grid(row=0, column=0, columnspan=2,
                          sticky="ew", padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📊  ACCOUNT SUMMARY",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=colors["fg"]
        )
        title_label.pack(anchor="w")

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, columnspan=2,
                     sticky="ew", padx=15, pady=(0, 10))

        # Create value displays with modern styling
        label_font = ctk.CTkFont(family="Segoe UI", size=11)
        value_font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")

        row_index = 2

        # Balance row
        ctk.CTkLabel(frame, text="Balance:", font=label_font, text_color=colors["fg_accent"]).grid(
            row=row_index, column=0, sticky="w", padx=15, pady=8)
        self.balance_var = ctk.StringVar(value="$...")
        ctk.CTkLabel(frame, textvariable=self.balance_var, font=value_font).grid(
            row=row_index, column=1, sticky="e", padx=15, pady=8)
        row_index += 1

        # Portfolio value row
        ctk.CTkLabel(frame, text="Portfolio Value:", font=label_font, text_color=colors["fg_accent"]).grid(
            row=row_index, column=0, sticky="w", padx=15, pady=8)
        self.portfolio_value_var = ctk.StringVar(value="$...")
        ctk.CTkLabel(frame, textvariable=self.portfolio_value_var, font=value_font).grid(
            row=row_index, column=1, sticky="e", padx=15, pady=8)
        row_index += 1

        # Total equity row
        ctk.CTkLabel(frame, text="Total Equity:", font=label_font, text_color=colors["fg_accent"]).grid(
            row=row_index, column=0, sticky="w", padx=15, pady=8)
        self.total_equity_var = ctk.StringVar(value="$...")
        ctk.CTkLabel(frame, textvariable=self.total_equity_var, font=value_font).grid(
            row=row_index, column=1, sticky="e", padx=15, pady=8)
        row_index += 1

        # PnL row with special styling
        ctk.CTkLabel(frame, text="Overall P/L:", font=label_font, text_color=colors["fg_accent"]).grid(
            row=row_index, column=0, sticky="w", padx=15, pady=8)
        self.pnl_var = ctk.StringVar(value="$...")

        # Create a frame for P/L to add a background highlight
        pnl_display_frame = ctk.CTkFrame(frame, fg_color=colors["bg_widget"])
        pnl_display_frame.grid(row=row_index, column=1,
                               sticky="e", padx=15, pady=8)

        # Store ref to change color later
        self.pnl_label = ctk.CTkLabel(
            pnl_display_frame,
            textvariable=self.pnl_var,
            font=value_font
        )
        self.pnl_label.pack(side="right")
        row_index += 1

        # Add a refresh button with modern styling
        button_frame = ctk.CTkFrame(frame, fg_color=colors["bg_widget"])
        button_frame.grid(row=row_index, column=0, columnspan=2,
                          sticky="ew", padx=15, pady=(15, 15))

        self.refresh_button = ctk.CTkButton(
            button_frame,
            text="REFRESH DATA",
            command=self.update_account_display_threaded,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=32,
            corner_radius=3
        )
        self.refresh_button.pack(fill="x")

    def create_trading_widgets(self, parent):
        # Get current colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a modern card-like frame
        frame = ctk.CTkFrame(
            parent, fg_color=colors["bg_widget"], corner_radius=10)
        frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15), padx=5)
        frame.grid_columnconfigure(1, weight=1)

        # Add a title label with icon
        header_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg_widget"], corner_radius=0)
        header_frame.grid(row=0, column=0, columnspan=3,
                          sticky="ew", padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🔄  TRADE EXECUTION",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=colors["fg"]
        )
        title_label.pack(anchor="w")

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, columnspan=3,
                     sticky="ew", padx=15, pady=(0, 10))

        # Input fields with modern styling
        label_font = ctk.CTkFont(family="Segoe UI", size=11)

        # Ticker row
        ticker_label = ctk.CTkLabel(
            frame, text="Ticker Symbol:", font=label_font, text_color=colors["fg_accent"])
        ticker_label.grid(row=2, column=0, sticky="w", padx=15, pady=8)

        self.ticker_entry = ctk.CTkEntry(
            frame,
            width=120,
            height=35,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            placeholder_text="e.g. AAPL"
        )
        self.ticker_entry.grid(
            row=2, column=1, sticky="ew", padx=(0, 5), pady=8)
        self.ticker_entry.bind("<Return>", self.fetch_chart_data_threaded)

        # Update chart button with modern styling
        self.chart_update_button = ctk.CTkButton(
            frame,
            text="📈",
            command=self.fetch_chart_data_threaded,
            width=40,
            height=35,
            corner_radius=3,
            font=ctk.CTkFont(size=16)
        )
        self.chart_update_button.grid(row=2, column=2, padx=(0, 15), pady=8)

        # Quantity row
        quantity_label = ctk.CTkLabel(
            frame, text="Quantity:", font=label_font, text_color=colors["fg_accent"])
        quantity_label.grid(row=3, column=0, sticky="w", padx=15, pady=8)

        self.quantity_entry = ctk.CTkEntry(
            frame,
            width=120,
            height=35,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            placeholder_text="e.g. 100"
        )
        self.quantity_entry.grid(
            row=3, column=1, columnspan=2, sticky="ew", padx=(0, 15), pady=8)

        # Action buttons with sleek styling
        button_frame = ctk.CTkFrame(frame, fg_color=colors["bg_widget"])
        button_frame.grid(row=4, column=0, columnspan=3,
                          sticky="ew", padx=15, pady=(10, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Modern Buy button
        self.buy_button = ctk.CTkButton(
            button_frame,
            text="BUY",
            command=lambda: self.execute_trade_threaded('BUY'),
            fg_color="#0D904F",  # Darker green for more professional look
            hover_color="#0A7A43",  # Even darker on hover
            height=38,
            corner_radius=3,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.buy_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Modern Sell button
        self.sell_button = ctk.CTkButton(
            button_frame,
            text="SELL",
            command=lambda: self.execute_trade_threaded('SELL'),
            fg_color="#D83A52",  # Darker red for more professional look
            hover_color="#B73146",  # Even darker on hover
            height=38,
            corner_radius=3,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.sell_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def create_status_widgets(self, parent):
        # Get current colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a modern panel
        frame = ctk.CTkFrame(
            parent, fg_color=colors["bg_widget"], corner_radius=10)
        frame.grid(row=2, column=0, sticky="nsew", padx=5)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Add a title with modern styling and icon
        header_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg_widget"], corner_radius=0)
        header_frame.grid(row=0, column=0, columnspan=2,
                          sticky="ew", padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📝  STATUS LOG",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=colors["fg"]
        )
        title_label.pack(anchor="w")

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, columnspan=2,
                     sticky="ew", padx=15, pady=(0, 10))

        # Use modern text display for status with improved styling
        self.status_text = ctk.CTkTextbox(
            frame,
            height=200,
            wrap="word",
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=colors["bg_widget"],
            text_color=colors["fg"],
            border_width=0
        )
        self.status_text.grid(row=2, column=0, sticky="nsew", padx=15, pady=5)

        # Custom scrollbar with modern styling
        scrollbar = ctk.CTkScrollbar(
            frame,
            orientation="vertical",
            command=self.status_text.yview,
            button_color=colors["bg_accent"],
            button_hover_color=colors["accent_button_bg"]
        )
        scrollbar.grid(row=2, column=1, sticky="ns", pady=5, padx=(0, 15))
        self.status_text.configure(yscrollcommand=scrollbar.set)

        # Add modern autotrade indicator in status area
        autotrade_container = ctk.CTkFrame(frame, fg_color=colors["bg_widget"])
        autotrade_container.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 15))

        # More sophisticated indicator with icon
        indicator_frame = ctk.CTkFrame(
            autotrade_container, fg_color=colors["bg_accent"], corner_radius=5, height=28)
        indicator_frame.pack(side=tk.LEFT, fill="y", padx=(0, 10))

        self.autotrade_indicator = ctk.CTkLabel(
            indicator_frame,
            text=" ⚠️ AUTO-TRADING: OFF ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#FF5252",
            padx=10
        )
        self.autotrade_indicator.pack(fill="both", expand=True)

        # Modern configure button
        self.autotrade_toggle = ctk.CTkButton(
            autotrade_container,
            text="CONFIGURE",
            width=110,
            height=28,
            corner_radius=3,
            command=self.show_autotrade_settings,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold")
        )
        self.autotrade_toggle.pack(side=tk.RIGHT)

    def update_autotrade_indicator(self):
        """Update the autotrade indicator label"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        if self.autotrade_enabled.get():
            algorithm_name = self.selected_algorithm.get().replace("_", " ").title()
            self.autotrade_indicator.configure(
                text=f" ✅ AUTO-TRADING: {algorithm_name} ",
                text_color=colors["gain"]
            )
        else:
            self.autotrade_indicator.configure(
                text=" ⚠️ AUTO-TRADING: OFF ",
                text_color=colors["loss"]
            )

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

        # Save button
        save_button = ctk.CTkButton(
            frame,
            text="SAVE SETTINGS",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=settings_window.destroy
        )
        save_button.pack(pady=20)

    def create_chart_widgets(self, parent):
        # Get current colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a card-like frame for the chart
        frame = ctk.CTkFrame(
            parent, fg_color=colors["bg_widget"], corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10), padx=5)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Add a modern header with icon
        header_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg_widget"], corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📈  PRICE CHART",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=colors["fg"]
        )
        title_label.pack(anchor="w")

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Create a frame for the chart with custom styling
        chart_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg"], corner_radius=6)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))
        chart_frame.grid_rowconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(0, weight=1)

        # Create the canvas for the existing figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Draw the initial canvas
        self.canvas.draw()

    def create_positions_widgets(self, parent):
        # Get current colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a modern card-like frame
        frame = ctk.CTkFrame(
            parent, fg_color=colors["bg_widget"], corner_radius=10)
        frame.grid(row=0, column=1, sticky="nsew", padx=(10, 5), pady=(0, 10))
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Add a modern header with icon
        header_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg_widget"], corner_radius=0)
        header_frame.grid(row=0, column=0, columnspan=2,
                          sticky="ew", padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="💼  POSITIONS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=colors["fg"]
        )
        title_label.pack(anchor="w")

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, columnspan=2,
                     sticky="ew", padx=15, pady=(0, 10))

        # Create a container for the Treeview with matching background color
        tree_container = ctk.CTkFrame(
            frame, fg_color=colors["bg"], corner_radius=6)
        tree_container.grid(row=2, column=0, sticky="nsew",
                            padx=15, pady=(5, 15))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Create the tree with ttk.Treeview
        columns = ("symbol", "quantity", "entry_price", "current_price", "pl")
        self.positions_tree = ttk.Treeview(
            tree_container, columns=columns, show="headings", height=10)

        # Configure the headings with better formatting
        self.positions_tree.heading("symbol", text="SYMBOL")
        self.positions_tree.heading("quantity", text="QTY")
        self.positions_tree.heading("entry_price", text="ENTRY")
        self.positions_tree.heading("current_price", text="CURRENT")
        self.positions_tree.heading("pl", text="P/L %")

        # Configure column widths
        self.positions_tree.column("symbol", width=80)
        self.positions_tree.column("quantity", width=65)
        self.positions_tree.column("entry_price", width=80)
        self.positions_tree.column("current_price", width=80)
        self.positions_tree.column("pl", width=80)

        # Position the tree with better padding
        self.positions_tree.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Style the tree immediately
        self._apply_treeview_style(self.positions_tree, colors)

        # Stylish scrollbar
        scrollbar = ctk.CTkScrollbar(
            tree_container, orientation="vertical", command=self.positions_tree.yview,
            button_color=colors["bg_accent"],
            button_hover_color=colors["accent_button_bg"]
        )
        scrollbar.grid(row=0, column=1, sticky="ns",
                       pady=5, padx=(0, 5))
        self.positions_tree.configure(yscrollcommand=scrollbar.set)

    def create_history_widgets(self, parent):
        # Get current colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a modern card-like frame
        frame = ctk.CTkFrame(
            parent, fg_color=colors["bg_widget"], corner_radius=10)
        frame.grid(row=1, column=1, sticky="nsew", padx=(10, 5), pady=(0, 5))
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Add a modern header with icon
        header_frame = ctk.CTkFrame(
            frame, fg_color=colors["bg_widget"], corner_radius=0)
        header_frame.grid(row=0, column=0, columnspan=2,
                          sticky="ew", padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🕒  TRADE HISTORY",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=colors["fg"]
        )
        title_label.pack(anchor="w")

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, columnspan=2,
                     sticky="ew", padx=15, pady=(0, 10))

        # Create a container for the Treeview with matching background
        tree_container = ctk.CTkFrame(
            frame, fg_color=colors["bg"], corner_radius=6)
        tree_container.grid(row=2, column=0, sticky="nsew",
                            padx=15, pady=(5, 15))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Create the tree with ttk.Treeview
        columns = ("timestamp", "symbol", "side", "quantity", "price")
        self.history_tree = ttk.Treeview(
            tree_container, columns=columns, show="headings")

        # Configure headings with better text
        self.history_tree.heading("timestamp", text="TIME")
        self.history_tree.heading("symbol", text="SYMBOL")
        self.history_tree.heading("side", text="SIDE")
        self.history_tree.heading("quantity", text="QTY")
        self.history_tree.heading("price", text="PRICE")

        # Configure column widths
        self.history_tree.column("timestamp", width=140)
        self.history_tree.column("symbol", width=70)
        self.history_tree.column("side", width=70)
        self.history_tree.column("quantity", width=60)
        self.history_tree.column("price", width=70)

        # Position the tree with better padding
        self.history_tree.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Style the tree immediately
        self._apply_treeview_style(self.history_tree, colors)

        # Stylish scrollbar
        scrollbar = ctk.CTkScrollbar(
            tree_container, orientation="vertical", command=self.history_tree.yview,
            button_color=colors["bg_accent"],
            button_hover_color=colors["accent_button_bg"]
        )
        scrollbar.grid(row=0, column=1, sticky="ns",
                       pady=5, padx=(0, 5))
        self.history_tree.configure(yscrollcommand=scrollbar.set)

    def apply_chart_theme(self, mode="dark"):
        """Apply theme to matplotlib chart based on mode"""
        try:
            colors = COLORS["dark"] if mode == "dark" else COLORS["light"]

            # Configure chart appearance - fix white backgrounds
            self.fig.patch.set_facecolor(colors["bg_widget"])
            self.ax.set_facecolor(colors["bg_widget"])

            # Make all axes elements colored correctly
            for item in ([self.ax.title, self.ax.xaxis.label, self.ax.yaxis.label] +
                         self.ax.get_xticklabels() + self.ax.get_yticklabels()):
                item.set_color(colors["fg"])

            # Set grid and spine colors
            self.ax.grid(True, linestyle='--', alpha=0.3,
                         color=colors["chart_grid"])
            for spine in self.ax.spines.values():
                spine.set_color(colors["chart_grid"])

            # Set tick parameters with color
            self.ax.tick_params(
                axis='both', colors=colors["fg_accent"], labelcolor=colors["fg_accent"])

            # Apply the changes if canvas exists
            if hasattr(self, 'canvas'):
                self.canvas.draw()
                # Also make sure the canvas background is themed
                if hasattr(self, 'canvas_widget'):
                    self.canvas_widget.configure(bg=colors["bg_widget"])

        except Exception as e:
            print(f"Error applying chart theme: {str(e)}")
            # No need to re-raise, chart theming is non-critical

    def update_account_display_threaded(self):
        """Update account information in a background thread to avoid UI freezing"""
        # Start the update in a background thread
        threading.Thread(target=self._update_account_display,
                         daemon=True).start()
        self.add_status_message("Account information updated")

    def _update_account_display(self):
        """Fetch account data and update UI elements"""
        try:
            # Simulate a network delay for fetching account data
            time.sleep(0.5)

            # Get account data from database
            account_data = db.get_account_info()

            # Update the UI elements in the main thread
            self.after(0, lambda: self._update_account_ui(account_data))
        except Exception as e:
            error_msg = str(e)  # Store error message in a variable
            self.after(0, lambda error=error_msg: self.add_status_message(
                f"Error updating account: {error}", error=True))

    def _update_account_ui(self, account_data):
        """Update UI with account data (called from main thread)"""
        # Format the balance values with commas and 2 decimal places
        self.balance_var.set(f"${account_data['balance']:,.2f}")

        # Update P/L
        profit_loss = account_data.get('profit_loss', 0.0)
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Format P/L text with sign and percentage
        if profit_loss >= 0:
            pl_text = f"+${profit_loss:,.2f} (+{account_data.get('profit_loss_pct', 0.0):.2f}%)"
            pl_color = colors["gain"]
        else:
            pl_text = f"-${abs(profit_loss):,.2f} (-{abs(account_data.get('profit_loss_pct', 0.0)):.2f}%)"
            pl_color = colors["loss"]

        self.pnl_var.set(pl_text)
        self.pnl_label.configure(text_color=pl_color)

        # Update buying power
        self.portfolio_value_var.set(
            f"${account_data['portfolio_value']:,.2f}")
        self.total_equity_var.set(f"${account_data['total_equity']:,.2f}")

    def add_status_message(self, message, error=False):
        """Add a message to the status text widget with timestamp"""
        # Get current theme colors
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Get current time for timestamp
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # Format the message with timestamp
        formatted_message = f"[{timestamp}] {message}\n"

        # Configure text color based on message type
        text_color = colors["loss"] if error else colors["fg"]

        # Enable editing to insert text
        self.status_text.configure(state="normal")

        # CTkTextbox doesn't support tags like tk.Text does, so we'll just set the text color
        # Insert the message at the end with appropriate color
        # For CTkTextbox we'll just append text, it doesn't have tag support like regular tkinter Text
        current_text = self.status_text.get("0.0", "end")
        self.status_text.delete("0.0", "end")

        if error:
            # For error messages, we'll prepend the existing text and add the new error message
            self.status_text.insert("0.0", current_text)
            self.status_text.insert("end", formatted_message)
        else:
            # For normal messages, we'll just append the message
            self.status_text.insert("0.0", current_text)
            self.status_text.insert("end", formatted_message)

        # Scroll to the bottom to show the latest message
        self.status_text.see("end")

        # Disable editing again to prevent user modification
        self.status_text.configure(state="disabled")

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
        self.chart_update_button.configure(state="disabled")

        # Start data fetching in a background thread
        threading.Thread(target=self._fetch_chart_data,
                         args=(ticker,), daemon=True).start()

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
                0, lambda: self.chart_update_button.configure(state="normal"))

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
        self.canvas.draw()

    def execute_trade_threaded(self, action):
        """Execute a trade (buy/sell) in a background thread"""
        # Get ticker and quantity from entry fields
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
            f"Executing {action} order for {quantity} shares of {ticker}...")

        # Execute trade in background thread
        threading.Thread(
            target=self._execute_trade,
            args=(action, ticker, quantity),
            daemon=True
        ).start()

    def _execute_trade(self, action, ticker, quantity):
        """Execute a trade in the background thread"""
        try:
            # Execute the appropriate trading function
            if action.upper() == 'BUY':
                result = tl.execute_buy(ticker, quantity)
            else:
                result = tl.execute_sell(ticker, quantity)

            # Get the result message
            if result and 'success' in result and result['success']:
                message = f"{action.capitalize()} order executed: {quantity} shares of {ticker} at ${result['price']:.2f}"
                is_error = False
            else:
                message = f"Error executing {action} order: {result.get('message', 'Unknown error')}"
                is_error = True

            # Update UI in main thread
            self.after(0, lambda: self.add_status_message(
                message, error=is_error))

            # Refresh account info and positions
            self.after(0, lambda: self.update_account_display_threaded())
            self.after(0, lambda: self.update_positions_display())
            self.after(0, lambda: self.update_history_display())

        except Exception as e:
            # Handle any errors
            error_msg = f"Error executing {action} order: {str(e)}"
            self.after(0, lambda: self.add_status_message(
                error_msg, error=True))

        finally:
            # Re-enable buttons
            self.after(0, lambda: self.buy_button.configure(state="normal"))
            self.after(0, lambda: self.sell_button.configure(state="normal"))

    def update_scan_interval_display(self):
        """Update the displayed scan interval"""
        pass  # This is a placeholder that can be implemented later if needed

    def update_positions_display(self):
        """Update the positions treeview with current position data"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)

            # Get current positions from database
            positions = db.get_positions()

            # Get current theme colors
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

            # Populate the treeview with position data
            for position in positions:
                # Calculate P/L
                entry_price = position['entry_price']
                current_price = position['current_price']
                pl_pct = ((current_price - entry_price) /
                          entry_price) * 100 if entry_price > 0 else 0

                # Format P/L text with sign and color
                if pl_pct >= 0:
                    pl_text = f"+{pl_pct:.2f}%"
                    pl_tag = f"gain_{position['symbol']}"
                    self.positions_tree.tag_configure(
                        pl_tag, foreground=colors["gain"])
                else:
                    pl_text = f"{pl_pct:.2f}%"
                    pl_tag = f"loss_{position['symbol']}"
                    self.positions_tree.tag_configure(
                        pl_tag, foreground=colors["loss"])

                # Insert the position with appropriate formatting
                values = (
                    position['symbol'],
                    position['quantity'],
                    f"${entry_price:.2f}",
                    f"${current_price:.2f}",
                    pl_text
                )

                self.positions_tree.insert(
                    "", "end", values=values, tags=(pl_tag,))

            # Apply the modern Treeview style
            self._apply_treeview_style(self.positions_tree)

            # Add a status message
            self.add_status_message("Positions updated")

        except Exception as e:
            self.add_status_message(
                f"Error updating positions: {str(e)}", error=True)

    def update_history_display(self):
        """Update the trade history treeview with latest trades"""
        try:
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            # Get trade history from database
            history = db.get_trade_history()

            # Get current theme colors
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

            # Populate the treeview with trade history
            for trade in history:
                # Format the timestamp nicely
                timestamp = trade['timestamp'].strftime(
                    "%Y-%m-%d %H:%M") if hasattr(trade['timestamp'], 'strftime') else trade['timestamp']

                # Set tag based on trade side (buy/sell)
                if trade['side'].lower() == 'buy':
                    tag = f"buy_{trade['id']}"
                    self.history_tree.tag_configure(
                        tag, foreground=colors["gain"])
                else:
                    tag = f"sell_{trade['id']}"
                    self.history_tree.tag_configure(
                        tag, foreground=colors["loss"])

                # Insert the trade with appropriate formatting
                values = (
                    timestamp,
                    trade['symbol'],
                    trade['side'].upper(),
                    trade['quantity'],
                    f"${trade['price']:.2f}"
                )

                self.history_tree.insert("", 0, values=values, tags=(tag,))

            # Apply the modern Treeview style
            self._apply_treeview_style(self.history_tree)

            # Add a status message
            self.add_status_message("Trade history updated")

        except Exception as e:
            self.add_status_message(
                f"Error updating trade history: {str(e)}", error=True)


# Main execution block
if __name__ == "__main__":
    app = TradingApp()
    app.mainloop()

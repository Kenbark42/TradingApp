import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import time
from config import COLORS
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SplashScreen:
    """Modern splash screen with animation"""

    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.splash = None
        self.progress_bar = None
        self.progress_var = None

    def show(self):
        # Get colors for dark theme
        colors = COLORS["dark"]

        self.splash = ctk.CTkToplevel(self.parent)
        self.splash.title("Loading...")
        self.splash.overrideredirect(True)  # No window decorations
        self.splash.attributes("-alpha", 0.0)  # Start transparent for fade-in

        # Calculate position for center of screen
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        width = 550
        height = 320
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.splash.geometry(f"{width}x{height}+{x}+{y}")

        # Configure dark theme background
        self.splash.configure(fg_color=colors["bg"])

        # Main content frame with subtle border
        content_frame = ctk.CTkFrame(
            self.splash, fg_color=colors["bg"], border_width=1, border_color=colors["border"])
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

        # Modern tagline
        tagline = ctk.CTkLabel(content_frame, text="Test your trading strategies without risk",
                               font=ctk.CTkFont(
                                   family="Segoe UI", size=12, weight="normal", slant="italic"),
                               text_color=colors["fg_accent"])
        tagline.pack(pady=(0, 20))

        # Modern progress bar with gradient effect
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ctk.CTkProgressBar(content_frame, width=400, height=10,
                                               variable=self.progress_var,
                                               progress_color=colors["accent_button_bg"],
                                               corner_radius=2)
        self.progress_bar.pack(pady=(20, 10))

        # Status message
        self.status_label = ctk.CTkLabel(content_frame, text="Loading...",
                                         font=ctk.CTkFont(
                                             family="Segoe UI", size=11),
                                         text_color=colors["fg_accent"])
        self.status_label.pack(pady=(0, 10))

        # Fade in animation
        self._fade_in()

    def _fade_in(self):
        """Animate transparency from 0 to 1"""
        alpha = self.splash.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.05
            self.splash.attributes("-alpha", alpha)
            self.splash.after(20, self._fade_in)
        else:
            self._start_progress()

    def _start_progress(self):
        """Animate progress bar"""
        self.splash.after(100, self._update_progress_bar)

    def _update_progress_bar(self, current_value=0.0):
        """Updates the progress bar with appropriate steps and status messages"""
        if current_value <= 0.3:
            self.status_label.configure(text="Loading application...")
        elif current_value <= 0.6:
            self.status_label.configure(text="Connecting to data services...")
        elif current_value <= 0.9:
            self.status_label.configure(
                text="Preparing trading environment...")
        else:
            self.status_label.configure(text="Ready to launch...")

        if current_value < 1.0:
            current_value += 0.01
            self.progress_var.set(current_value)
            self.splash.after(
                20, lambda: self._update_progress_bar(current_value))
        else:
            # Finished loading
            self.splash.after(200, self._complete_splash)

    def _complete_splash(self):
        """Complete splash screen and show main application"""
        # Start fade out animation
        self._fade_out()

    def _fade_out(self, alpha=1.0):
        """Animate transparency from 1 to 0"""
        if alpha > 0:
            alpha -= 0.05
            self.splash.attributes("-alpha", alpha)
            self.splash.after(20, lambda: self._fade_out(alpha))
        else:
            # Destroy splash and show main app
            self.splash.destroy()
            self.callback()  # Run the callback function to show main app


class StatusPanel:
    """Status message panel with text display and autotrade indicator"""

    def __init__(self, parent, appearance_mode, autotrade_enabled, selected_algorithm, show_settings_callback):
        self.parent = parent
        self.appearance_mode = appearance_mode
        self.autotrade_enabled = autotrade_enabled
        self.selected_algorithm = selected_algorithm
        self.show_settings_callback = show_settings_callback
        self.status_text = None
        self.autotrade_indicator = None
        self.create_widgets()

    def create_widgets(self):
        """Create status panel with text display"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a frame with modern card-like design
        frame = ctk.CTkFrame(self.parent, corner_radius=10)
        frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)  # For scrollbar

        # Add a title with icon
        title_label = ctk.CTkLabel(
            frame,
            text=" 📋 Status Messages",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))

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

        # Configure grid for the container
        autotrade_container.grid_columnconfigure(0, weight=1)  # For indicator
        autotrade_container.grid_columnconfigure(1, weight=0)  # For button

        # More sophisticated indicator with icon
        indicator_frame = ctk.CTkFrame(
            autotrade_container, fg_color=colors["bg_accent"], corner_radius=5, height=28)
        indicator_frame.grid(row=0, column=0, sticky="w", padx=(0, 10))
        indicator_frame.grid_columnconfigure(0, weight=1)
        indicator_frame.grid_rowconfigure(0, weight=1)

        self.autotrade_indicator = ctk.CTkLabel(
            indicator_frame,
            text=" ⚠️ AUTO-TRADING: OFF ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#FF5252",
            padx=10
        )
        self.autotrade_indicator.grid(row=0, column=0, sticky="nsew")

        # Modern configure button
        self.autotrade_toggle = ctk.CTkButton(
            autotrade_container,
            text="CONFIGURE",
            width=110,
            height=28,
            corner_radius=3,
            command=self.show_settings_callback,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold")
        )
        self.autotrade_toggle.grid(row=0, column=1, sticky="e")

    def update_indicator(self):
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

    def add_message(self, message, error=False):
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


class TreeviewPanel:
    """Base class for treeview-based panels (positions and history)"""

    def __init__(self, parent, appearance_mode):
        self.parent = parent
        self.appearance_mode = appearance_mode
        self.tree = None

    def apply_treeview_style(self, tree=None, colors=None):
        """Apply a modern theme to the treeview"""
        if tree is None:
            tree = self.tree

        if colors is None:
            colors = COLORS["dark"] if self.appearance_mode.get(
            ) == 'dark' else COLORS["light"]

        # Configure the treeview style
        style = ttk.Style()

        # Configure the Treeview
        style.configure("Treeview",
                        background=colors["bg_widget"],
                        foreground=colors["fg_widget"],
                        rowheight=28,
                        fieldbackground=colors["bg_widget"],
                        borderwidth=0,
                        font=('Segoe UI', 10))

        # Configure the Treeview.Heading
        style.configure("Treeview.Heading",
                        background=colors["bg_accent"],
                        foreground=colors["fg"],
                        relief="flat",
                        font=('Segoe UI', 10, 'bold'))

        # Map the Treeview for selection styling
        style.map('Treeview',
                  background=[('selected', colors["accent_button_bg"])],
                  foreground=[('selected', colors["accent_button_fg"])])

        # Set up alternating row colors and profit/loss colors
        if tree:
            # Create even and odd tags
            tree.tag_configure('even', background=colors["bg_widget"])
            tree.tag_configure('odd', background=colors["bg_accent"])

            # Configure gain/loss tags for profit/loss coloring
            tree.tag_configure('gain', foreground=colors["gain"])
            tree.tag_configure('loss', foreground=colors["loss"])

            # Apply tags to existing rows
            items = tree.get_children()
            for i, item in enumerate(items):
                tag = 'even' if i % 2 == 0 else 'odd'
                # Keep any existing tags like gain/loss
                current_tags = tree.item(item, 'tags')
                if current_tags and len(current_tags) > 1:
                    tree.item(item, tags=(tag, current_tags[1]))

    def create_frame(self, title, icon="📊"):
        """Create a modern card-like frame for a treeview"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a frame with modern card-like design
        frame = ctk.CTkFrame(self.parent, corner_radius=10)
        frame.grid_columnconfigure(0, weight=1)

        # Add a title with icon
        title_label = ctk.CTkLabel(
            frame,
            text=f" {icon} {title}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))

        # Add a subtle divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 10))

        return frame


class PositionsPanel(TreeviewPanel):
    """Panel for displaying current positions"""

    def __init__(self, parent, appearance_mode, update_callback=None):
        super().__init__(parent, appearance_mode)
        self.update_callback = update_callback
        self.auto_refresh_enabled = ctk.BooleanVar(value=False)
        self.refresh_interval = ctk.IntVar(value=10)  # seconds
        self.create_widgets()

    def create_widgets(self):
        """Create positions treeview panel"""
        frame = self.create_frame("Current Positions", "💼")
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Add refresh controls above the treeview
        controls_frame = ctk.CTkFrame(frame, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 5))
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=0)

        # Auto-refresh toggle with label
        auto_refresh_frame = ctk.CTkFrame(
            controls_frame, fg_color="transparent")
        auto_refresh_frame.grid(row=0, column=0, sticky="w")

        refresh_label = ctk.CTkLabel(
            auto_refresh_frame,
            text="Auto-refresh:",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=colors["fg_accent"]
        )
        refresh_label.grid(row=0, column=0, padx=(0, 5))

        auto_refresh_toggle = ctk.CTkSwitch(
            auto_refresh_frame,
            text="",
            variable=self.auto_refresh_enabled,
            command=self.toggle_auto_refresh,
            width=40,
            height=18
        )
        auto_refresh_toggle.grid(row=0, column=1, padx=(0, 5))

        interval_label = ctk.CTkLabel(
            auto_refresh_frame,
            text="Interval:",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=colors["fg_accent"]
        )
        interval_label.grid(row=0, column=2, padx=(5, 5))

        interval_dropdown = ctk.CTkOptionMenu(
            auto_refresh_frame,
            values=["5", "10", "15", "30", "60"],
            variable=self.refresh_interval,
            command=self.change_interval,
            width=60,
            height=20,
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        interval_dropdown.grid(row=0, column=3, padx=(0, 5))

        seconds_label = ctk.CTkLabel(
            auto_refresh_frame,
            text="seconds",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=colors["fg_accent"]
        )
        seconds_label.grid(row=0, column=4, padx=(0, 5))

        # Manual refresh button
        refresh_button = ctk.CTkButton(
            controls_frame,
            text="↻",
            width=25,
            height=25,
            command=self.manual_refresh,
            corner_radius=5,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        refresh_button.grid(row=0, column=1, padx=(0, 0), sticky="e")

        # Create treeview for positions inside a container frame for proper scrollbar positioning
        tree_container = ctk.CTkFrame(frame, fg_color="transparent")
        tree_container.grid(row=3, column=0, sticky="nsew",
                            padx=15, pady=(0, 15))
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        # Create Treeview
        self.tree = ttk.Treeview(
            tree_container,
            columns=("symbol", "quantity", "entry_price",
                     "current_price", "position_value", "pnl", "pnl_percent"),
            show="headings",
            selectmode="browse",
            height=10
        )

        # Set column headings with modern formatting
        self.tree.heading("symbol", text="Symbol")
        self.tree.heading("quantity", text="Qty")
        self.tree.heading("entry_price", text="Entry")
        self.tree.heading("current_price", text="Current")
        self.tree.heading("position_value", text="Value")
        self.tree.heading("pnl", text="P/L $")
        self.tree.heading("pnl_percent", text="P/L %")

        # Configure column widths and alignment
        self.tree.column("symbol", width=80, anchor="center")
        self.tree.column("quantity", width=70, anchor="center")
        self.tree.column("entry_price", width=90, anchor="center")
        self.tree.column("current_price", width=90, anchor="center")
        self.tree.column("position_value", width=100, anchor="center")
        self.tree.column("pnl", width=90, anchor="center")
        self.tree.column("pnl_percent", width=90, anchor="center")

        # Add custom scrollbar
        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview,
                                     button_color=colors["bg_accent"],
                                     button_hover_color=colors["accent_button_bg"])
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Attach scrollbar to treeview
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Apply modern styling
        self.apply_treeview_style()

    def toggle_auto_refresh(self):
        """Toggle auto-refresh state and start/stop timer"""
        if self.update_callback:
            if self.auto_refresh_enabled.get():
                self.update_callback(True, self.refresh_interval.get())
            else:
                self.update_callback(False)

    def change_interval(self, interval):
        """Update the refresh interval"""
        try:
            # Update interval variable
            self.refresh_interval.set(int(interval))
            # If auto-refresh is enabled, restart timer with new interval
            if self.auto_refresh_enabled.get() and self.update_callback:
                self.update_callback(True, self.refresh_interval.get())
        except ValueError:
            pass

    def manual_refresh(self):
        """Trigger a manual refresh"""
        if self.update_callback:
            self.update_callback(single=True)


class HistoryPanel(TreeviewPanel):
    """Panel for displaying trade history"""

    def __init__(self, parent, appearance_mode):
        super().__init__(parent, appearance_mode)
        self.create_widgets()

    def create_widgets(self):
        """Create history treeview panel"""
        frame = self.create_frame("Trade History", "📜")
        frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create treeview for history inside a container frame
        tree_container = ctk.CTkFrame(frame, fg_color="transparent")
        tree_container.grid(row=2, column=0, sticky="nsew",
                            padx=15, pady=(0, 15))
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        # Create Treeview
        self.tree = ttk.Treeview(
            tree_container,
            columns=("timestamp", "symbol", "side",
                     "quantity", "price", "total"),
            show="headings",
            selectmode="browse",
            height=10
        )

        # Set column headings
        self.tree.heading("timestamp", text="Time")
        self.tree.heading("symbol", text="Symbol")
        self.tree.heading("side", text="Side")
        self.tree.heading("quantity", text="Qty")
        self.tree.heading("price", text="Price")
        self.tree.heading("total", text="Total")

        # Configure column widths and alignment
        self.tree.column("timestamp", width=140, anchor="center")
        self.tree.column("symbol", width=80, anchor="center")
        self.tree.column("side", width=70, anchor="center")
        self.tree.column("quantity", width=70, anchor="center")
        self.tree.column("price", width=90, anchor="center")
        self.tree.column("total", width=100, anchor="center")

        # Add custom scrollbar
        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview,
                                     button_color=colors["bg_accent"],
                                     button_hover_color=colors["accent_button_bg"])
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Attach scrollbar to treeview
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Apply modern styling
        self.apply_treeview_style()


class ChartPanel:
    """Panel for displaying stock charts"""

    def __init__(self, parent, appearance_mode, fig, ax, fetch_data_callback):
        self.parent = parent
        self.appearance_mode = appearance_mode
        self.fig = fig
        self.ax = ax
        self.fetch_data_callback = fetch_data_callback
        self.canvas = None
        self.ticker_entry = None
        self.chart_update_button = None
        self.create_widgets()

    def create_widgets(self):
        """Create chart panel with input controls"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a frame with modern card-like design
        frame = ctk.CTkFrame(self.parent, corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)  # Chart area takes most space

        # Top controls bar
        controls_frame = ctk.CTkFrame(frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="ew",
                            padx=15, pady=(10, 0))
        controls_frame.grid_columnconfigure(0, weight=1)  # For title
        controls_frame.grid_columnconfigure(1, weight=0)  # For controls

        # Chart title
        title_label = ctk.CTkLabel(
            controls_frame,
            text="📈 Price Chart",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Right side controls
        input_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        input_frame.grid(row=0, column=1, sticky="e")

        # Configure input frame columns
        input_frame.grid_columnconfigure(0, weight=0)  # Label
        input_frame.grid_columnconfigure(1, weight=0)  # Entry
        input_frame.grid_columnconfigure(2, weight=0)  # Button

        # Ticker entry and update button
        ticker_label = ctk.CTkLabel(input_frame, text="Symbol:")
        ticker_label.grid(row=0, column=0, padx=(0, 5))

        self.ticker_entry = ctk.CTkEntry(input_frame, width=100)
        self.ticker_entry.grid(row=0, column=1, padx=(0, 10))

        self.chart_update_button = ctk.CTkButton(
            input_frame,
            text="Update Chart",
            width=110,
            height=30,
            command=self.fetch_data_callback
        )
        self.chart_update_button.grid(row=0, column=2)

        # Add divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 5))

        # Create chart area
        chart_frame = ctk.CTkFrame(frame, fg_color=colors["bg_widget"])
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        # Create matplotlib canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

    def apply_theme(self, mode=None):
        """Apply theme to chart"""
        if mode is None:
            mode = self.appearance_mode.get()

        colors = COLORS["dark"] if mode == "dark" else COLORS["light"]

        # Set figure facecolor
        self.fig.set_facecolor(colors["bg_widget"])
        self.ax.set_facecolor(colors["bg_widget"])

        # Set text colors
        self.ax.title.set_color(colors["fg"])
        self.ax.xaxis.label.set_color(colors["fg_accent"])
        self.ax.yaxis.label.set_color(colors["fg_accent"])

        # Set tick colors
        self.ax.tick_params(axis='x', colors=colors["fg_accent"])
        self.ax.tick_params(axis='y', colors=colors["fg_accent"])

        # Set grid
        self.ax.grid(True, linestyle='--', alpha=0.3,
                     color=colors["chart_grid"])

        # Set spine colors
        for spine in self.ax.spines.values():
            spine.set_color(colors["border"])

        # Redraw canvas
        self.canvas.draw()


class AccountInfoPanel:
    """Panel for displaying account information"""

    def __init__(self, parent, appearance_mode, refresh_callback):
        self.parent = parent
        self.appearance_mode = appearance_mode
        self.refresh_callback = refresh_callback
        self.account_label = None
        self.balance_label = None
        self.portfolio_label = None
        self.equity_label = None
        self.pnl_label = None
        self.create_widgets()

    def create_widgets(self):
        """Create account info panel"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a frame with modern card-like design
        frame = ctk.CTkFrame(self.parent, corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(4, weight=1)  # Make the PnL section expandable

        # Add title and refresh button in a row
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        title_label = ctk.CTkLabel(
            header_frame,
            text="💰 Account Summary",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")

        refresh_button = ctk.CTkButton(
            header_frame,
            text="↻",
            width=30,
            height=30,
            command=self.refresh_callback,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        )
        refresh_button.grid(row=0, column=1, sticky="e")

        # Add divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 10))

        # Account ID display
        self.account_label = ctk.CTkLabel(
            frame,
            text="Paper Trading Account",
            font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
            text_color=colors["fg_accent"]
        )
        self.account_label.grid(
            row=2, column=0, sticky="w", padx=15, pady=(0, 10))

        # Account balance info in grid layout
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))

        # Cash Balance
        balance_title = ctk.CTkLabel(
            info_frame,
            text="Cash Balance",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w"
        )
        balance_title.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.balance_label = ctk.CTkLabel(
            info_frame,
            text="$0.00",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            anchor="e"
        )
        self.balance_label.grid(row=0, column=1, sticky="e", pady=(0, 5))

        # Portfolio Value
        portfolio_title = ctk.CTkLabel(
            info_frame,
            text="Portfolio Value",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w"
        )
        portfolio_title.grid(row=1, column=0, sticky="w", pady=5)

        self.portfolio_label = ctk.CTkLabel(
            info_frame,
            text="$0.00",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            anchor="e"
        )
        self.portfolio_label.grid(row=1, column=1, sticky="e", pady=5)

        # Total Equity
        equity_title = ctk.CTkLabel(
            info_frame,
            text="Total Equity",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w"
        )
        equity_title.grid(row=2, column=0, sticky="w", pady=5)

        self.equity_label = ctk.CTkLabel(
            info_frame,
            text="$0.00",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            anchor="e"
        )
        self.equity_label.grid(row=2, column=1, sticky="e", pady=5)

        # Configure grid
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)

        # Add second divider
        divider2 = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider2.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Overall P/L
        pnl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pnl_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 15))
        pnl_frame.grid_columnconfigure(0, weight=1)
        pnl_frame.grid_columnconfigure(1, weight=1)

        pnl_title = ctk.CTkLabel(
            pnl_frame,
            text="Overall P/L",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w"
        )
        pnl_title.grid(row=0, column=0, sticky="w")

        self.pnl_label = ctk.CTkLabel(
            pnl_frame,
            text="$0.00 (0.00%)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=colors["fg"],
            anchor="e"
        )
        self.pnl_label.grid(row=0, column=1, sticky="e")

    def update_account_info(self, account_info):
        """Update account information display"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Update balance
        self.balance_label.configure(
            text=f"${account_info['cash_balance']:,.2f}")

        # Update portfolio value
        self.portfolio_label.configure(
            text=f"${account_info['portfolio_value']:,.2f}")

        # Update equity
        self.equity_label.configure(
            text=f"${account_info['total_equity']:,.2f}")

        # Update P/L with color
        pnl = account_info['pnl']
        pnl_percent = account_info['pnl_percent']
        pnl_color = colors["gain"] if pnl >= 0 else colors["loss"]
        pnl_sign = "+" if pnl > 0 else ""

        self.pnl_label.configure(
            text=f"{pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)",
            text_color=pnl_color
        )


class TradingControlsPanel:
    """Panel for trading controls"""

    def __init__(self, parent, appearance_mode, buy_callback, sell_callback):
        self.parent = parent
        self.appearance_mode = appearance_mode
        self.buy_callback = buy_callback
        self.sell_callback = sell_callback
        self.ticker_entry = None
        self.quantity_entry = None
        self.buy_button = None
        self.sell_button = None
        self.create_widgets()

    def create_widgets(self):
        """Create trading controls panel"""
        colors = COLORS["dark"] if self.appearance_mode.get(
        ) == 'dark' else COLORS["light"]

        # Create a frame with modern card-like design
        frame = ctk.CTkFrame(self.parent, corner_radius=10)
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)  # For button frame

        # Add title
        title_label = ctk.CTkLabel(
            frame,
            text="🛒 Trade Execution",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))

        # Add divider
        divider = ctk.CTkFrame(frame, height=1, fg_color=colors["border"])
        divider.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 10))

        # Input fields
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

        # Symbol
        ticker_label = ctk.CTkLabel(
            input_frame,
            text="Symbol:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=70
        )
        ticker_label.grid(row=0, column=0, sticky="w", pady=5)

        self.ticker_entry = ctk.CTkEntry(input_frame, width=120)
        self.ticker_entry.grid(row=0, column=1, sticky="w", pady=5)

        # Quantity
        quantity_label = ctk.CTkLabel(
            input_frame,
            text="Quantity:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=70
        )
        quantity_label.grid(row=1, column=0, sticky="w", pady=5)

        self.quantity_entry = ctk.CTkEntry(input_frame, width=120)
        self.quantity_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.quantity_entry.insert(0, "10")  # Default value

        # Configure grid
        input_frame.grid_columnconfigure(0, weight=0)
        input_frame.grid_columnconfigure(1, weight=1)

        # Action buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        button_frame.grid_columnconfigure(0, weight=0)
        button_frame.grid_columnconfigure(1, weight=0)
        button_frame.grid_columnconfigure(2, weight=1)  # Empty space

        # Buy button with green styling
        self.buy_button = ctk.CTkButton(
            button_frame,
            text="BUY",
            command=lambda: self.buy_callback(),
            width=100,
            height=35,
            fg_color="#00C853",  # Green
            hover_color="#00B048",  # Darker green
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        )
        self.buy_button.grid(row=0, column=0, padx=(0, 10))

        # Sell button with red styling
        self.sell_button = ctk.CTkButton(
            button_frame,
            text="SELL",
            command=lambda: self.sell_callback(),
            width=100,
            height=35,
            fg_color="#FF3D00",  # Red
            hover_color="#DD3000",  # Darker red
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        )
        self.sell_button.grid(row=0, column=1)

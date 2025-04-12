# Configuration settings for the TradingApp

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

# App settings
DEFAULT_WINDOW_SIZE = "1200x800"
INITIAL_APPEARANCE_MODE = "dark"
DEFAULT_COLOR_THEME = "blue"

# Chart settings
DEFAULT_CHART_FIGSIZE = (8, 4)

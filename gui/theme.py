"""
Modern sleek theme for Mini OS Simulator.
Provides consistent colors, fonts, and styling across the application.
"""

# Color Palette - Modern Dark Theme
COLORS = {
    # Backgrounds
    "bg_dark": "#0f1117",
    "bg_panel": "#1a1d27",
    "bg_card": "#242836",
    "bg_hover": "#2e3245",
    "bg_input": "#1e2130",
    "bg_titlebar": "#161822",
    
    # Accents
    "accent": "#6c8cff",
    "accent_hover": "#8aa3ff",
    "accent_dim": "#3d5a99",
    
    # Text
    "text_primary": "#e4e6eb",
    "text_secondary": "#8b90a0",
    "text_muted": "#5a5f70",
    
    # Status
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#f87171",
    "info": "#60a5fa",
    
    # Borders
    "border": "#2a2e3d",
    "border_light": "#353a4f",
    
    # Desktop
    "desktop_bg": "#0a0c10",
}

# Fonts
FONTS = {
    "title": ("Segoe UI", 16, "bold"),
    "heading": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
    "mono_small": ("Consolas", 9),
    "button": ("Segoe UI", 10),
}

# Spacing
SPACING = {
    "xs": 2,
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "xxl": 24,
}

# Border radius (for ttk styling)
RADIUS = 8

# Module color accents
MODULE_COLORS = {
    "cpu_scheduler": "#6c8cff",
    "deadlock": "#f87171",
    "memory": "#4ade80",
    "disk_scheduling": "#fbbf24",
    "process_manager": "#a78bfa",
    "system_monitor": "#60a5fa",
}

MODULE_ICONS = {
    "cpu_scheduler": "CPU",
    "deadlock": "DLK",
    "memory": "MEM",
    "disk_scheduling": "DSK",
    "process_manager": "PRC",
    "system_monitor": "MON",
}


def apply_ttk_style(root):
    """Apply modern ttk styling to the application."""
    style = ttk.Style(root)
    style.theme_use("clam")
    
    # General
    style.configure(".", background=COLORS["bg_panel"], foreground=COLORS["text_primary"],
                    font=FONTS["body"], borderwidth=0)
    
    # Frames
    style.configure("TFrame", background=COLORS["bg_panel"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
    
    # LabelFrame
    style.configure("TLabelframe", background=COLORS["bg_panel"], borderwidth=1,
                    relief="solid", bordercolor=COLORS["border"])
    style.configure("TLabelframe.Label", background=COLORS["bg_panel"], 
                    foreground=COLORS["accent"], font=FONTS["heading"])
    
    # Labels
    style.configure("TLabel", background=COLORS["bg_panel"], foreground=COLORS["text_primary"])
    style.configure("Muted.TLabel", foreground=COLORS["text_secondary"], font=FONTS["small"])
    style.configure("Title.TLabel", font=FONTS["title"], foreground=COLORS["text_primary"])
    style.configure("Heading.TLabel", font=FONTS["heading"], foreground=COLORS["accent"])
    
    # Buttons
    style.configure("TButton", background=COLORS["bg_card"], foreground=COLORS["text_primary"],
                    font=FONTS["button"], borderwidth=0, padding=(12, 6))
    style.map("TButton",
              background=[("active", COLORS["bg_hover"]), ("pressed", COLORS["accent_dim"])],
              foreground=[("active", COLORS["text_primary"])])
    
    # Accent button
    style.configure("Accent.TButton", background=COLORS["accent"], foreground="#ffffff",
                    font=FONTS["button"], borderwidth=0, padding=(12, 6))
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent_dim"])],
              foreground=[("active", "#ffffff")])
    
    # Danger button
    style.configure("Danger.TButton", background=COLORS["danger"], foreground="#ffffff",
                    font=FONTS["button"], borderwidth=0, padding=(12, 6))
    style.map("Danger.TButton",
              background=[("active", "#ef4444"), ("pressed", "#dc2626")])
    
    # Entry
    style.configure("TEntry", fieldbackground=COLORS["bg_input"], foreground=COLORS["text_primary"],
                    borderwidth=1, relief="solid", bordercolor=COLORS["border"], padding=4)
    style.map("TEntry", bordercolor=[("focus", COLORS["accent"])])
    
    # Spinbox
    style.configure("TSpinbox", fieldbackground=COLORS["bg_input"], foreground=COLORS["text_primary"],
                    borderwidth=1, relief="solid", bordercolor=COLORS["border"], padding=4)
    
    # Combobox
    style.configure("TCombobox", fieldbackground=COLORS["bg_input"], foreground=COLORS["text_primary"],
                    borderwidth=1, relief="solid", bordercolor=COLORS["border"])
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["bg_input"])])
    
    # Checkbutton
    style.configure("TCheckbutton", background=COLORS["bg_panel"], foreground=COLORS["text_primary"])
    
    # Radiobutton
    style.configure("TRadiobutton", background=COLORS["bg_panel"], foreground=COLORS["text_primary"])
    
    # Notebook
    style.configure("TNotebook", background=COLORS["bg_panel"], borderwidth=0)
    style.configure("TNotebook.Tab", background=COLORS["bg_card"], foreground=COLORS["text_secondary"],
                    padding=(16, 8), font=FONTS["body"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["bg_panel"]), ("active", COLORS["bg_hover"])],
              foreground=[("selected", COLORS["accent"]), ("active", COLORS["text_primary"])])
    
    # Treeview
    style.configure("Treeview", background=COLORS["bg_input"], foreground=COLORS["text_primary"],
                    fieldbackground=COLORS["bg_input"], borderwidth=0, rowheight=24,
                    font=FONTS["small"])
    style.configure("Treeview.Heading", background=COLORS["bg_card"], foreground=COLORS["accent"],
                    font=FONTS["small"], borderwidth=0, relief="flat")
    style.map("Treeview", background=[("selected", COLORS["accent_dim"])],
              foreground=[("selected", "#ffffff")])
    
    # Scale
    style.configure("TScale", background=COLORS["bg_panel"], troughcolor=COLORS["bg_input"])
    
    # Progressbar
    style.configure("TProgressbar", background=COLORS["accent"], troughcolor=COLORS["bg_input"],
                    borderwidth=0, thickness=6)
    
    # Scrollbar
    style.configure("TScrollbar", background=COLORS["bg_card"], troughcolor=COLORS["bg_panel"],
                    borderwidth=0, arrowsize=12)
    style.map("TScrollbar", background=[("active", COLORS["bg_hover"])])
    
    # Separator
    style.configure("TSeparator", background=COLORS["border"])
    
    return style

"""
Desktop environment for Mini OS Simulator.
Implements an OS-inspired desktop with icons, taskbar, and window management.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable
import uuid
import os
import glob
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
from gui.theme import COLORS, FONTS, MODULE_COLORS, apply_ttk_style

# Import module factories
from modules.cpu_scheduling.gui import create_cpu_scheduling_module
from modules.deadlock.gui import create_deadlock_module
from modules.memory.gui import create_memory_module
from modules.disk_scheduling.gui import create_disk_scheduling_module
from modules.process_manager.gui import create_process_manager_module
from modules.system_monitor.gui import create_system_monitor_module


class Window:
    """Base class for simulation module windows."""
    
    def __init__(self, parent: tk.Widget, title: str, width: int = 800, height: int = 600):
        self.window_id = str(uuid.uuid4())[:8]
        self.title = title
        self.width = width
        self.height = height
        self.is_minimized = False
        self.is_maximized = False
        self.parent = parent
        self.frame: Optional[tk.Toplevel] = None
        self.content_frame: Optional[tk.Frame] = None
        self.title_bar: Optional[tk.Frame] = None
        self._create_window()
    
    def _create_window(self):
        self.frame = tk.Toplevel(self.parent)
        self.frame.title(self.title)
        self.frame.geometry(f"{self.width}x{self.height}")
        self.frame.protocol("WM_DELETE_WINDOW", self.close)
        self.frame.withdraw()  # Hide initially
        
        # Title bar
        self.title_bar = tk.Frame(self.frame, bg=COLORS["bg_titlebar"], height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)
        
        # Title label
        title_label = tk.Label(
            self.title_bar, 
            text=self.title, 
            bg=COLORS["bg_titlebar"], 
            fg=COLORS["text_primary"],
            font=("Segoe UI", 9, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Window controls
        controls_frame = tk.Frame(self.title_bar, bg=COLORS["bg_titlebar"])
        controls_frame.pack(side=tk.RIGHT, padx=5)
        
        # Minimize button
        minimize_btn = tk.Button(
            controls_frame,
            text="—",
            width=3,
            bg=COLORS["bg_titlebar"],
            fg=COLORS["text_primary"],
            bd=0,
            activebackground=COLORS["bg_hover"],
            command=self.minimize
        )
        minimize_btn.pack(side=tk.LEFT, padx=2)
        
        # Maximize button
        self.maximize_btn = tk.Button(
            controls_frame,
            text="□",
            width=3,
            bg=COLORS["bg_titlebar"],
            fg=COLORS["text_primary"],
            bd=0,
            activebackground=COLORS["bg_hover"],
            command=self.toggle_maximize
        )
        self.maximize_btn.pack(side=tk.LEFT, padx=2)
        
        # Close button
        close_btn = tk.Button(
            controls_frame,
            text="×",
            width=3,
            bg=COLORS["bg_titlebar"],
            fg=COLORS["text_primary"],
            bd=0,
            activebackground=COLORS["danger"],
            command=self.close
        )
        close_btn.pack(side=tk.LEFT, padx=2)
        
        # Content area
        self.content_frame = tk.Frame(self.frame, bg=COLORS["bg_panel"])
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bind events for dragging
        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._on_drag)
        
        self._drag_data = {"x": 0, "y": 0}
    
    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
    
    def _on_drag(self, event):
        x = self.frame.winfo_x() + (event.x_root - self._drag_data["x"])
        y = self.frame.winfo_y() + (event.y_root - self._drag_data["y"])
        self.frame.geometry(f"+{x}+{y}")
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
    
    def show(self):
        """Show and maximize the window within the desktop workspace."""
        self._apply_maximized_geometry()
        self.frame.deiconify()
        self.frame.lift()
        self.frame.focus_force()
        self.is_minimized = False
        self.is_maximized = True
        self.maximize_btn.config(text="❐")
    
    def hide(self):
        self.frame.withdraw()
    
    def minimize(self):
        self.hide()
        self.is_minimized = True
        self.is_maximized = False
        self.maximize_btn.config(text="□")
    
    def toggle_maximize(self):
        if self.is_maximized:
            self.frame.geometry(f"{self.width}x{self.height}")
            self.maximize_btn.config(text="□")
            self.is_maximized = False
        else:
            self._apply_maximized_geometry()
            self.maximize_btn.config(text="❐")
            self.is_maximized = True
    
    def _apply_maximized_geometry(self):
        """Size the window to fill the desktop workspace below the taskbar."""
        screen_w = self.parent.winfo_screenwidth()
        screen_h = self.parent.winfo_screenheight()
        taskbar_h = 40  # matches the taskbar frame height in _setup_taskbar
        available_h = screen_h - taskbar_h
        
        self.frame.geometry(f"{screen_w}x{available_h}+0+0")
    
    def close(self):
        self.frame.destroy()
        self.frame = None
        self.content_frame = None
    
    def get_content_frame(self) -> tk.Frame:
        return self.content_frame
    
    def set_title(self, title: str):
        self.title = title
        for widget in self.title_bar.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(text=title)
                break


class DesktopIcon:
    """Represents an icon on the desktop."""
    
    def __init__(
        self, 
        canvas: tk.Canvas, 
        x: int, 
        y: int, 
        text: str, 
        icon_color: str,
        command: Callable,
        desktop_app: 'DesktopApp'
    ):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.text = text
        self.icon_color = icon_color
        self.command = command
        self.desktop_app = desktop_app
        self.is_selected = False
        self.is_hovered = False
        self.icon_id = None
        self.image_id = None
        self.text_id = None
        self.icon_photo = None
        self._draw()
        self._bind_events()
    
    def _create_icon_image(self):
        """Draw a simple desktop shortcut icon using PIL."""
        from PIL import ImageDraw
        
        size = 56
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw module-specific icon
        if self.text == "CPU Scheduler":
            self._draw_cpu_icon(draw, size)
        elif self.text == "Deadlock Manager":
            self._draw_deadlock_icon(draw, size)
        elif self.text == "Memory Manager":
            self._draw_memory_icon(draw, size)
        elif self.text == "Disk Scheduler":
            self._draw_disk_icon(draw, size)
        elif self.text == "Process Manager":
            self._draw_process_icon(draw, size)
        elif self.text == "System Monitor":
            self._draw_monitor_icon(draw, size)
        
        return ImageTk.PhotoImage(img)
    
    def _draw_cpu_icon(self, draw, size):
        """CPU chip: rectangle with corner pins."""
        pad = 8
        # Chip body
        draw.rectangle([pad, pad, size-pad, size-pad], fill="#ffffff", outline=self.icon_color, width=2)
        # Corner pins
        pin = 4
        for cx, cy in [(pad, pad), (size-pad, pad), (pad, size-pad), (size-pad, size-pad)]:
            draw.rectangle([cx-pin//2, cy-pin//2, cx+pin//2, cy+pin//2], fill="#ffffff")
        # Center lines
        draw.line([pad+10, pad+10, size-pad-10, size-pad-10], fill="#ffffff", width=2)
        draw.line([size-pad-10, pad+10, pad+10, size-pad-10], fill="#ffffff", width=2)
    
    def _draw_deadlock_icon(self, draw, size):
        """Deadlock: two interlocking circles with center lock symbol."""
        pad = 8
        r = size // 5
        # Circle 1 (left)
        cx1, cy1 = pad + r + 4, pad + r + 4
        draw.ellipse([cx1-r, cy1-r, cx1+r, cy1+r], outline="#ffffff", width=3)
        # Circle 2 (right)
        cx2, cy2 = size-pad-r-4, size-pad-r-4
        draw.ellipse([cx2-r, cy2-r, cx2+r, cy2+r], outline="#ffffff", width=3)
        # Center lock padlock
        lx, ly = size // 2, size // 2
        lw, lh = 10, 14
        draw.rectangle([lx-lw//2, ly-lh//2, lx+lw//2, ly+lh//2], fill="#ffffff")
        draw.rectangle([lx-lw//2-2, ly-lh//2-2, lx+lw//2+2, ly-lh//2+2], fill="#ffffff")
    
    def _draw_memory_icon(self, draw, size):
        """Memory: stick with line pattern."""
        pad = 8
        # Stick body
        draw.rectangle([pad+8, pad, size-pad-8, size-pad], fill="#ffffff", outline=self.icon_color, width=2)
        # Contact pins at bottom
        for i in range(4):
            px = pad + 12 + i * 10
            draw.line([px, size-pad, px+4, size-pad], fill="#ffffff", width=3)
        # Data lines
        draw.line([pad+12, pad+12, size-pad-12, pad+12], fill="#ffffff", width=2)
        draw.line([pad+12, size-pad-12, size-pad-12, size-pad-12], fill="#ffffff", width=2)
    
    def _draw_disk_icon(self, draw, size):
        """Disk: drive with platters."""
        pad = 8
        # Drive body
        draw.rectangle([pad+4, pad+4, size-pad-4, size-pad-4], fill="#ffffff", outline=self.icon_color, width=2)
        # Platters (concentric circles)
        cx, cy = size // 2, size // 2
        for r in range(6, size // 2 - 6, 8):
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="#ffffff", width=2)
        # Center dot
        draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill="#ffffff")
    
    def _draw_process_icon(self, draw, size):
        """Process: rectangles with arrow (process flow)."""
        pad = 8
        # Process blocks
        draw.rectangle([pad+4, pad+6, pad+26, size-pad-6], fill="#ffffff", outline=self.icon_color, width=2)
        draw.rectangle([size-pad-26, pad+6, size-pad-4, size-pad-6], fill="#ffffff", outline=self.icon_color, width=2)
        # Arrow between them
        draw.line([pad+28, size//2, size-pad-28, size//2], fill="#ffffff", width=3)
        draw.polygon([size-pad-28, size//2-6, size-pad-28, size//2+6, size-pad-20, size//2], fill="#ffffff")
    
    def _draw_monitor_icon(self, draw, size):
        """Monitor: bar chart."""
        pad = 8
        bar_width = 6
        gap = 4
        heights = [14, 22, 10, 18]
        base_y = size - pad - 4
        colors_cycle = ["#ffffff", "#cccccc", "#ffffff", "#cccccc"]
        for i, h in enumerate(heights):
            x = pad + i * (bar_width + gap)
            y = base_y - h
            draw.rectangle([x, y, x+bar_width, base_y], fill=colors_cycle[i % 4])
    
    def _draw(self):
        # Use module color for icon background so each shortcut is distinct
        self.icon_id = self.canvas.create_rectangle(
            self.x, self.y, 
            self.x + 74, self.y + 74,
            fill=self.icon_color, outline=COLORS["border"], width=2,
            tags="icon"
        )
        
        # Draw actual icon graphic using PIL
        self.icon_photo = self._create_icon_image()
        self.image_id = self.canvas.create_image(
            self.x + 37, self.y + 37,
            image=self.icon_photo,
            tags="icon_symbol"
        )
        
        # Icon text label (beneath the icon)
        self.text_id = self.canvas.create_text(
            self.x + 37, self.y + 93,
            text=self.text,
            fill="#ffffff",
            font=("Segoe UI", 9, "bold"),
            width=74,
            justify=tk.CENTER,
            tags="icon_text"
        )
    
    def _bind_events(self):
        # Single click selects, double click launches
        self.canvas.tag_bind(self.icon_id, "<Button-1>", self._on_click)
        self.canvas.tag_bind(self.text_id, "<Button-1>", self._on_click)
        self.canvas.tag_bind(self.image_id, "<Button-1>", self._on_click)
        self.canvas.tag_bind(self.icon_id, "<Double-Button-1>", self._on_double_click)
        self.canvas.tag_bind(self.text_id, "<Double-Button-1>", self._on_double_click)
        self.canvas.tag_bind(self.image_id, "<Double-Button-1>", self._on_double_click)
        # Hover effects
        self.canvas.tag_bind(self.icon_id, "<Enter>", self._on_enter)
        self.canvas.tag_bind(self.text_id, "<Enter>", self._on_enter)
        self.canvas.tag_bind(self.image_id, "<Enter>", self._on_enter)
        self.canvas.tag_bind(self.icon_id, "<Leave>", self._on_leave)
        self.canvas.tag_bind(self.text_id, "<Leave>", self._on_leave)
        self.canvas.tag_bind(self.image_id, "<Leave>", self._on_leave)
    
    def _on_click(self, event):
        self.desktop_app.select_icon(self)
    
    def _on_double_click(self, event):
        self.command()
    
    def _on_enter(self, event):
        self.is_hovered = True
        self._update_appearance()
    
    def _on_leave(self, event):
        self.is_hovered = False
        self._update_appearance()
    
    def _update_appearance(self):
        """Update icon appearance based on hover and selection state."""
        base_color = self.icon_color
        if self.is_selected:
            outline = COLORS["accent"]
            width = 3
        elif self.is_hovered:
            outline = COLORS["border_light"]
            width = 3
        else:
            outline = COLORS["border"]
            width = 2
        
        self.canvas.itemconfig(self.icon_id, outline=outline, width=width, fill=base_color)
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_appearance()
    
    def get_bounds(self):
        return (self.x, self.y, self.x + 74, self.y + 115)


class TaskbarButton:
    """Button on the taskbar representing an open window."""
    
    def __init__(self, parent: tk.Frame, window: Window, desktop_app: 'DesktopApp'):
        self.window = window
        self.desktop_app = desktop_app
        
        self.button = tk.Button(
            parent,
            text=window.title,
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            bd=0,
            padx=15,
            pady=5,
            font=("Segoe UI", 9),
            activebackground=COLORS["bg_hover"],
            command=self._on_click
        )
        self.button.pack(side=tk.LEFT, padx=2, pady=2)
    
    def _on_click(self):
        if self.window.is_minimized:
            self.window.show()
        elif not (self.window.frame and self.window.frame.winfo_viewable()):
            self.window.show()
        else:
            # Toggle: if visible, bring to front
            self.window.frame.lift()
            self.window.frame.focus_force()
    
    def update_state(self):
        if self.window.is_minimized or not (self.window.frame and self.window.frame.winfo_viewable()):
            self.button.config(bg=COLORS["bg_card"])
        else:
            self.button.config(bg=COLORS["accent"])
    
    def destroy(self):
        self.button.destroy()


class StartMenu:
    """Start menu for launching applications."""
    
    def __init__(self, root: tk.Tk, desktop_app: 'DesktopApp'):
        self.root = root
        self.desktop_app = desktop_app
        self.menu_window: Optional[tk.Toplevel] = None
        self.is_open = False
    
    def toggle(self, x: int, y: int):
        if self.is_open:
            self.close()
        else:
            self.open(x, y)
    
    def open(self, x: int, y: int):
        self.menu_window = tk.Toplevel(self.root)
        self.menu_window.overrideredirect(True)
        self.menu_window.geometry(f"220x350+{x}+{y-350}")
        self.menu_window.configure(bg=COLORS["bg_titlebar"])
        self.menu_window.attributes("-topmost", True)
        
        # Header
        header = tk.Frame(self.menu_window, bg=COLORS["bg_panel"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, 
            text="Mini OS", 
            bg=COLORS["bg_panel"], 
            fg=COLORS["text_primary"], 
            font=("Segoe UI", 12, "bold")
        ).pack(pady=10)
        
        # Separator
        tk.Frame(self.menu_window, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=5)
        
        # App list
        apps = [
            ("CPU Scheduler", "🖥️", lambda: self.desktop_app.open_module("cpu_scheduler")),
            ("Deadlock Manager", "🔒", lambda: self.desktop_app.open_module("deadlock")),
            ("Memory Manager", "🧠", lambda: self.desktop_app.open_module("memory")),
            ("Disk Scheduler", "💽", lambda: self.desktop_app.open_module("disk_scheduling")),
            ("Process Manager", "⚙️", lambda: self.desktop_app.open_module("process_manager")),
        ]
        
        for name, icon, cmd in apps:
            btn = tk.Button(
                self.menu_window,
                text=f"  {icon}  {name}",
                bg=COLORS["bg_titlebar"],
                fg=COLORS["text_primary"],
                bd=0,
                anchor="w",
                padx=20,
                pady=10,
                font=("Segoe UI", 10),
                activebackground=COLORS["bg_hover"],
                command=lambda c=cmd: [c(), self.close()]
            )
            btn.pack(fill=tk.X)
        
        # Separator
        tk.Frame(self.menu_window, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=5, pady=5)
        
        # Exit button
        exit_btn = tk.Button(
            self.menu_window,
            text="  ⏻  Exit",
            bg=COLORS["bg_titlebar"],
            fg=COLORS["text_primary"],
            bd=0,
            anchor="w",
            padx=20,
            pady=10,
            font=("Segoe UI", 10),
            activebackground=COLORS["danger"],
            command=self.desktop_app.quit
        )
        exit_btn.pack(fill=tk.X)
        
        self.is_open = True
        self.menu_window.bind("<FocusOut>", lambda e: self.close())
        self.menu_window.focus_set()
    
    def close(self):
        if self.menu_window:
            self.menu_window.destroy()
            self.menu_window = None
        self.is_open = False


class DesktopApp:
    """Main desktop application managing the OS-like interface."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Mini OS Simulator")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS["desktop_bg"])
        self._maximize_root_window()
        
        # Window tracking
        self.windows: Dict[str, Window] = {}
        self.taskbar_buttons: Dict[str, TaskbarButton] = {}
        self.next_icon_position = [20, 20]
        self.desktop_icons: List[DesktopIcon] = []
        self.wallpaper_image = None
        self.wallpaper_photo = None
        
        # Setup UI
        self._setup_taskbar()
        self._setup_desktop()
        self._setup_start_menu()
        self._create_desktop_icons()
        
        # Bind events
        self.root.bind("<Configure>", self._on_resize)
        self.desktop_canvas.bind("<Button-1>", self._on_desktop_click)
    
    def _setup_desktop(self):
        """Create the desktop background and canvas."""
        self.desktop_frame = tk.Frame(self.root, bg=COLORS["desktop_bg"])
        self.desktop_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for desktop icons and wallpaper
        self.desktop_canvas = tk.Canvas(
            self.desktop_frame,
            bg=COLORS["desktop_bg"],
            highlightthickness=0
        )
        self.desktop_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Load and draw wallpaper
        self._load_wallpaper()
    
    def _maximize_root_window(self):
        """Maximize the root window to fill the screen (Linux-compatible)."""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")

    def _find_wallpaper(self):
        """Auto-detect a JPG/PNG wallpaper in the project root directory."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            matches = glob.glob(os.path.join(project_root, ext))
            if matches:
                return matches[0]
        return None

    def _load_wallpaper(self):
        """Load the desktop wallpaper image if PIL is available."""
        if not PIL_AVAILABLE:
            return
        wallpaper_path = self._find_wallpaper()
        if not wallpaper_path:
            return
        try:
            self.wallpaper_image = Image.open(wallpaper_path)
            self._draw_wallpaper()
        except Exception:
            self.wallpaper_image = None

    def _draw_wallpaper(self):
        """Draw the wallpaper covering the canvas with aspect-aware crop."""
        if not self.wallpaper_image or not self.desktop_canvas.winfo_exists():
            return

        canvas_w = self.desktop_canvas.winfo_width()
        canvas_h = self.desktop_canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            # Canvas not yet laid out; retry shortly
            self.root.after(50, self._draw_wallpaper)
            return

        # Calculate crop box to cover canvas while maintaining aspect ratio
        img_w, img_h = self.wallpaper_image.size
        canvas_ratio = canvas_w / canvas_h
        img_ratio = img_w / img_h

        if img_ratio > canvas_ratio:
            # Image is wider than canvas: crop left/right
            new_w = int(img_h * canvas_ratio)
            x = (img_w - new_w) // 2
            crop_box = (x, 0, x + new_w, img_h)
        else:
            # Image is taller than canvas: crop top/bottom
            new_h = int(img_w / canvas_ratio)
            y = (img_h - new_h) // 2
            crop_box = (0, y, img_w, y + new_h)

        cropped = self.wallpaper_image.crop(crop_box)
        resized = cropped.resize((canvas_w, canvas_h), Image.LANCZOS)
        self.wallpaper_photo = ImageTk.PhotoImage(resized)

        # Remove old wallpaper and draw new one as bottom layer
        self.desktop_canvas.delete("wallpaper")
        self.desktop_canvas.create_image(
            0, 0, image=self.wallpaper_photo, anchor=tk.NW, tags="wallpaper"
        )
        self.desktop_canvas.tag_lower("wallpaper")

    def _setup_taskbar(self):
        """Create the taskbar at the bottom."""
        self.taskbar = tk.Frame(self.root, bg=COLORS["bg_panel"], height=40)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.taskbar.pack_propagate(False)
        self.taskbar.lift()  # Ensure taskbar stays on top of desktop canvas
        
        # Start button
        self.start_button = tk.Button(
            self.taskbar,
            text="⊞  Start",
            bg=COLORS["bg_panel"],
            fg=COLORS["text_primary"],
            bd=0,
            padx=20,
            pady=5,
            font=("Segoe UI", 10, "bold"),
            activebackground="#333333",
            command=self._toggle_start_menu
        )
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Taskbar buttons container
        self.taskbar_buttons_frame = tk.Frame(self.taskbar, bg=COLORS["bg_panel"])
        self.taskbar_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # System tray (right side)
        self.system_tray = tk.Frame(self.taskbar, bg=COLORS["bg_panel"])
        self.system_tray.pack(side=tk.RIGHT, padx=10)
        
        # Clock
        self.clock_label = tk.Label(
            self.system_tray,
            text="",
            bg=COLORS["bg_panel"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 9)
        )
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self._update_clock()
    
    def _update_clock(self):
        import time
        self.clock_label.config(text=time.strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)
    
    def _setup_start_menu(self):
        """Initialize the start menu."""
        self.start_menu = StartMenu(self.root, self)
    
    def _toggle_start_menu(self):
        x = self.start_button.winfo_rootx()
        y = self.start_button.winfo_rooty()
        self.start_menu.toggle(x, y)
    
    def _create_desktop_icons(self):
        """Create desktop icons arranged vertically along the left side."""
        modules = [
            ("CPU Scheduler", "cpu_scheduler", lambda: self.open_module("cpu_scheduler")),
            ("Deadlock Manager", "deadlock", lambda: self.open_module("deadlock")),
            ("Memory Manager", "memory", lambda: self.open_module("memory")),
            ("Disk Scheduler", "disk_scheduling", lambda: self.open_module("disk_scheduling")),
            ("Process Manager", "process_manager", lambda: self.open_module("process_manager")),
        ]

        # Vertical column on left side of desktop
        icon_w = 74
        icon_h = 115  # includes text below icon
        v_gap = 20  # vertical gap between shortcuts
        x = 22  # left margin
        y = 70  # start from top area

        self.desktop_icons = []
        for idx, (name, module_key, cmd) in enumerate(modules):
            y_pos = y + idx * (icon_h + v_gap)
            color = MODULE_COLORS.get(module_key, COLORS["accent"])
            icon = DesktopIcon(self.desktop_canvas, x, y_pos, name, color, cmd, self)
            self.desktop_icons.append(icon)
    
    def _on_desktop_click(self, event):
        """Deselect icons when clicking on empty desktop."""
        self.deselect_all_icons()
        self.start_menu.close()
    
    def _on_resize(self, event):
        """Handle window resize."""
        if event.widget == self.root:
            self._draw_wallpaper()
    
    def select_icon(self, icon: DesktopIcon):
        """Select a desktop icon."""
        self.deselect_all_icons()
        icon.set_selected(True)
        self.selected_icon = icon
    
    def deselect_all_icons(self):
        """Deselect all desktop icons."""
        if hasattr(self, 'desktop_icons'):
            for icon in self.desktop_icons:
                icon.set_selected(False)
    
    def open_module(self, module_name: str):
        """Open a simulation module window."""
        if module_name in self.windows:
            window = self.windows[module_name]
            if window.frame and window.frame.winfo_exists():
                window.show()
                return
        
        # Create new window based on module
        window = self._create_module_window(module_name)
        if window:
            self.windows[module_name] = window
            window.show()
            self._add_taskbar_button(window)
    
    def _create_module_window(self, module_name: str) -> Optional[Window]:
        """Create a window for the specified module."""
        module_configs = {
            "cpu_scheduler": ("CPU Scheduler", 1000, 700),
            "deadlock": ("Deadlock Manager", 1000, 700),
            "memory": ("Memory Manager", 1000, 700),
            "disk_scheduling": ("Disk Scheduler", 1000, 700),
            "process_manager": ("Process Manager", 1000, 700),
            "system_monitor": ("System Monitor", 800, 600),
        }
        
        if module_name not in module_configs:
            return None
        
        title, width, height = module_configs[module_name]
        window = Window(self.root, title, width, height)
        
        # Create module content
        content = window.get_content_frame()
        
        module_factories = {
            "cpu_scheduler": create_cpu_scheduling_module,
            "deadlock": create_deadlock_module,
            "memory": create_memory_module,
            "disk_scheduling": create_disk_scheduling_module,
            "process_manager": create_process_manager_module,
            "system_monitor": create_system_monitor_module,
        }
        
        if module_name in module_factories:
            try:
                module_factories[module_name](self.root, content)
            except Exception as e:
                # Fallback to placeholder on error
                label = tk.Label(
                    content,
                    text=f"{title} Module\n\nError loading module:\n{e}",
                    bg=COLORS["bg_panel"],
                    fg="#ff4444",
                    font=("Segoe UI", 12)
                )
                label.pack(expand=True)
        else:
            label = tk.Label(
                content,
                text=f"{title} Module\n\nNot implemented yet",
                bg=COLORS["bg_panel"],
                fg=COLORS["text_primary"],
                font=("Segoe UI", 14)
            )
            label.pack(expand=True)
        
        return window
    
    def _add_taskbar_button(self, window: Window):
        """Add a button to the taskbar for the window."""
        button = TaskbarButton(self.taskbar_buttons_frame, window, self)
        self.taskbar_buttons[window.window_id] = button
        window.frame.protocol("WM_DELETE_WINDOW", lambda w=window: self._on_window_close(w))
    
    def _on_window_close(self, window: Window):
        """Handle window close."""
        window.close()
        if window.window_id in self.taskbar_buttons:
            self.taskbar_buttons[window.window_id].destroy()
            del self.taskbar_buttons[window.window_id]
        # Find and remove from windows dict
        for key, w in list(self.windows.items()):
            if w == window:
                del self.windows[key]
                break
    
    def quit(self):
        """Quit the application."""
        self.root.quit()
        self.root.destroy()
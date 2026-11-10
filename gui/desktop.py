"""
Desktop environment for Mini OS Simulator.
Implements an OS-inspired desktop with icons, taskbar, and window management.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable
import uuid

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
        self.title_bar = tk.Frame(self.frame, bg="#2d2d2d", height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)
        
        # Title label
        title_label = tk.Label(
            self.title_bar, 
            text=self.title, 
            bg="#2d2d2d", 
            fg="#ffffff",
            font=("Segoe UI", 9, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Window controls
        controls_frame = tk.Frame(self.title_bar, bg="#2d2d2d")
        controls_frame.pack(side=tk.RIGHT, padx=5)
        
        # Minimize button
        minimize_btn = tk.Button(
            controls_frame,
            text="—",
            width=3,
            bg="#2d2d2d",
            fg="#ffffff",
            bd=0,
            activebackground="#3d3d3d",
            command=self.minimize
        )
        minimize_btn.pack(side=tk.LEFT, padx=2)
        
        # Maximize button
        self.maximize_btn = tk.Button(
            controls_frame,
            text="□",
            width=3,
            bg="#2d2d2d",
            fg="#ffffff",
            bd=0,
            activebackground="#3d3d3d",
            command=self.toggle_maximize
        )
        self.maximize_btn.pack(side=tk.LEFT, padx=2)
        
        # Close button
        close_btn = tk.Button(
            controls_frame,
            text="×",
            width=3,
            bg="#2d2d2d",
            fg="#ffffff",
            bd=0,
            activebackground="#e81123",
            command=self.close
        )
        close_btn.pack(side=tk.LEFT, padx=2)
        
        # Content area
        self.content_frame = tk.Frame(self.frame, bg="#1e1e1e")
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
        self.frame.deiconify()
        self.frame.lift()
        self.is_minimized = False
    
    def hide(self):
        self.frame.withdraw()
    
    def minimize(self):
        self.hide()
        self.is_minimized = True
    
    def toggle_maximize(self):
        if self.is_maximized:
            self.frame.geometry(f"{self.width}x{self.height}")
            self.maximize_btn.config(text="□")
            self.is_maximized = False
        else:
            self.frame.geometry(f"{self.parent.winfo_screenwidth()}x{self.parent.winfo_screenheight()}+0+0")
            self.maximize_btn.config(text="❐")
            self.is_maximized = True
    
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
        self.icon_id = None
        self.text_id = None
        self._draw()
        self._bind_events()
    
    def _draw(self):
        # Icon background
        self.icon_id = self.canvas.create_rectangle(
            self.x, self.y, 
            self.x + 80, self.y + 80,
            fill=self.icon_color, outline="#555555", width=2,
            tags="icon"
        )
        # Icon text
        self.text_id = self.canvas.create_text(
            self.x + 40, self.y + 95,
            text=self.text,
            fill="#ffffff",
            font=("Segoe UI", 8),
            width=80,
            tags="icon_text"
        )
    
    def _bind_events(self):
        self.canvas.tag_bind(self.icon_id, "<Button-1>", self._on_click)
        self.canvas.tag_bind(self.text_id, "<Button-1>", self._on_click)
        self.canvas.tag_bind(self.icon_id, "<Double-Button-1>", self._on_double_click)
        self.canvas.tag_bind(self.text_id, "<Double-Button-1>", self._on_double_click)
    
    def _on_click(self, event):
        self.desktop_app.select_icon(self)
    
    def _on_double_click(self, event):
        self.command()
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.canvas.itemconfig(self.icon_id, outline="#0078d7", width=3)
        else:
            self.canvas.itemconfig(self.icon_id, outline="#555555", width=2)
    
    def get_bounds(self):
        return (self.x, self.y, self.x + 80, self.y + 115)


class TaskbarButton:
    """Button on the taskbar representing an open window."""
    
    def __init__(self, parent: tk.Frame, window: Window, desktop_app: 'DesktopApp'):
        self.window = window
        self.desktop_app = desktop_app
        
        self.button = tk.Button(
            parent,
            text=window.title,
            bg="#333333",
            fg="#ffffff",
            bd=0,
            padx=15,
            pady=5,
            font=("Segoe UI", 9),
            activebackground="#444444",
            command=self._on_click
        )
        self.button.pack(side=tk.LEFT, padx=2, pady=2)
    
    def _on_click(self):
        if self.window.is_minimized:
            self.window.show()
        elif self.window.frame and self.window.frame.winfo_viewable():
            self.window.hide()
        else:
            self.window.show()
    
    def update_state(self):
        if self.window.is_minimized or not (self.window.frame and self.window.frame.winfo_viewable()):
            self.button.config(bg="#333333")
        else:
            self.button.config(bg="#0078d7")
    
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
        self.menu_window.configure(bg="#2d2d2d")
        self.menu_window.attributes("-topmost", True)
        
        # Header
        header = tk.Frame(self.menu_window, bg="#1e1e1e", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, 
            text="Mini OS", 
            bg="#1e1e1e", 
            fg="#ffffff", 
            font=("Segoe UI", 12, "bold")
        ).pack(pady=10)
        
        # Separator
        tk.Frame(self.menu_window, bg="#555555", height=1).pack(fill=tk.X, padx=5)
        
        # App list
        apps = [
            ("CPU Scheduler", "🖥️", lambda: self.desktop_app.open_module("cpu_scheduler")),
            ("Deadlock Manager", "🔒", lambda: self.desktop_app.open_module("deadlock")),
            ("Memory Manager", "🧠", lambda: self.desktop_app.open_module("memory")),
            ("Disk Scheduler", "💽", lambda: self.desktop_app.open_module("disk_scheduling")),
            ("Process Manager", "⚙️", lambda: self.desktop_app.open_module("process_manager")),
            ("System Monitor", "📊", lambda: self.desktop_app.open_module("system_monitor")),
        ]
        
        for name, icon, cmd in apps:
            btn = tk.Button(
                self.menu_window,
                text=f"  {icon}  {name}",
                bg="#2d2d2d",
                fg="#ffffff",
                bd=0,
                anchor="w",
                padx=20,
                pady=10,
                font=("Segoe UI", 10),
                activebackground="#3d3d3d",
                command=lambda c=cmd: [c(), self.close()]
            )
            btn.pack(fill=tk.X)
        
        # Separator
        tk.Frame(self.menu_window, bg="#555555", height=1).pack(fill=tk.X, padx=5, pady=5)
        
        # Exit button
        exit_btn = tk.Button(
            self.menu_window,
            text="  ⏻  Exit",
            bg="#2d2d2d",
            fg="#ffffff",
            bd=0,
            anchor="w",
            padx=20,
            pady=10,
            font=("Segoe UI", 10),
            activebackground="#e81123",
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
        self.root.configure(bg="#0078d7")
        self.root.state("zoomed")  # Maximize on Windows/Linux
        
        # Window tracking
        self.windows: Dict[str, Window] = {}
        self.taskbar_buttons: Dict[str, TaskbarButton] = {}
        self.next_icon_position = [20, 20]
        
        # Setup UI
        self._setup_desktop()
        self._setup_taskbar()
        self._setup_start_menu()
        self._create_desktop_icons()
        
        # Bind events
        self.root.bind("<Configure>", self._on_resize)
        self.desktop_canvas.bind("<Button-1>", self._on_desktop_click)
    
    def _setup_desktop(self):
        """Create the desktop background and canvas."""
        self.desktop_frame = tk.Frame(self.root, bg="#0078d7")
        self.desktop_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for desktop icons
        self.desktop_canvas = tk.Canvas(
            self.desktop_frame,
            bg="#0078d7",
            highlightthickness=0
        )
        self.desktop_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw a subtle grid pattern
        self._draw_background()
    
    def _draw_background(self):
        """Draw a subtle background pattern."""
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        for x in range(0, width, 50):
            self.desktop_canvas.create_line(x, 0, x, height, fill="#0066b8", width=1)
        for y in range(0, height, 50):
            self.desktop_canvas.create_line(0, y, width, y, fill="#0066b8", width=1)
    
    def _setup_taskbar(self):
        """Create the taskbar at the bottom."""
        self.taskbar = tk.Frame(self.root, bg="#1e1e1e", height=40)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.taskbar.pack_propagate(False)
        
        # Start button
        self.start_button = tk.Button(
            self.taskbar,
            text="⊞  Start",
            bg="#1e1e1e",
            fg="#ffffff",
            bd=0,
            padx=20,
            pady=5,
            font=("Segoe UI", 10, "bold"),
            activebackground="#333333",
            command=self._toggle_start_menu
        )
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Taskbar buttons container
        self.taskbar_buttons_frame = tk.Frame(self.taskbar, bg="#1e1e1e")
        self.taskbar_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # System tray (right side)
        self.system_tray = tk.Frame(self.taskbar, bg="#1e1e1e")
        self.system_tray.pack(side=tk.RIGHT, padx=10)
        
        # Clock
        self.clock_label = tk.Label(
            self.system_tray,
            text="",
            bg="#1e1e1e",
            fg="#ffffff",
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
        """Create desktop icons for each simulation module."""
        modules = [
            ("CPU Scheduler", "#0078d7", lambda: self.open_module("cpu_scheduler")),
            ("Deadlock Manager", "#e81123", lambda: self.open_module("deadlock")),
            ("Memory Manager", "#00b294", lambda: self.open_module("memory")),
            ("Disk Scheduler", "#ff8c00", lambda: self.open_module("disk_scheduling")),
            ("Process Manager", "#8764b8", lambda: self.open_module("process_manager")),
            ("System Monitor", "#e67e22", lambda: self.open_module("system_monitor")),
        ]
        
        x, y = 20, 20
        for name, color, cmd in modules:
            icon = DesktopIcon(self.desktop_canvas, x, y, name, color, cmd, self)
            x += 100
            if x > 600:
                x = 20
                y += 130
    
    def _on_desktop_click(self, event):
        """Deselect icons when clicking on empty desktop."""
        self.deselect_all_icons()
        self.start_menu.close()
    
    def _on_resize(self, event):
        """Handle window resize."""
        if event.widget == self.root:
            self.desktop_canvas.delete("background")
            self._draw_background()
    
    def select_icon(self, icon: DesktopIcon):
        """Select a desktop icon."""
        self.deselect_all_icons()
        icon.set_selected(True)
        self.selected_icon = icon
    
    def deselect_all_icons(self):
        """Deselect all desktop icons."""
        # This would need access to all icons - simplified for now
        pass
    
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
                    bg="#1e1e1e",
                    fg="#ff4444",
                    font=("Segoe UI", 12)
                )
                label.pack(expand=True)
        else:
            label = tk.Label(
                content,
                text=f"{title} Module\n\nNot implemented yet",
                bg="#1e1e1e",
                fg="#ffffff",
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
"""
System Monitor GUI Module for Mini OS Simulator.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import time
from gui.theme import COLORS, FONTS


class SystemMonitorWindow:
    """System Monitor window showing simulated system status."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        self.running = True
        self.update_after_id = None
        
        # Simulated system state
        self.system_state = {
            "total_processes": 0,
            "running": 0,
            "ready": 0,
            "waiting": 0,
            "terminated": 0,
            "cpu_util": 0.0,
            "memory_used": 0,
            "memory_total": 1024,
            "available_resources": [5, 3, 2],
        }
        
        self.history = {
            "cpu": [],
            "memory": [],
            "time": [],
        }
        
        self._setup_ui()
        self._start_updates()
    
    def _setup_ui(self):
        """Setup the UI components."""
        main_paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - System Overview
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_overview_panel(left)
        self._create_process_panel(left)
        self._create_resource_panel(left)
        
        # Right - Charts
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_charts_panel(right)
    
    def _create_overview_panel(self, parent):
        """Create system overview panel."""
        frame = ttk.LabelFrame(parent, text="System Overview", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid of metrics
        metrics = [
            ("Total Processes", "total_processes", "--"),
            ("Running", "running", "--"),
            ("Ready", "ready", "--"),
            ("Waiting", "waiting", "--"),
            ("Terminated", "terminated", "--"),
            ("CPU Utilization", "cpu_util", "--%"),
        ]
        
        self.metric_labels = {}
        for i, (label, key, default) in enumerate(metrics):
            row, col = divmod(i, 2)
            f = ttk.Frame(frame)
            f.grid(row=row, column=col, padx=10, pady=5, sticky=tk.W)
            ttk.Label(f, text=f"{label}:", font=FONTS["body"]).pack(side=tk.LEFT)
            self.metric_labels[key] = ttk.Label(f, text=default, font=FONTS["body"])
            self.metric_labels[key].pack(side=tk.LEFT, padx=10)
    
    def _create_process_panel(self, parent):
        """Create process list panel."""
        frame = ttk.LabelFrame(parent, text="Process List", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("PID", "State", "CPU %", "Memory", "Priority", "Core")
        self.process_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=80, anchor=tk.CENTER)
        self.process_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_tree.configure(yscrollcommand=scroll.set)
    
    def _create_resource_panel(self, parent):
        """Create resource panel."""
        frame = ttk.LabelFrame(parent, text="Resources", padding=10)
        frame.pack(fill=tk.X)
        
        # Memory
        mem_frame = ttk.Frame(frame)
        mem_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mem_frame, text="Memory:").pack(side=tk.LEFT)
        self.memory_bar = ttk.Progressbar(mem_frame, length=200, mode='determinate')
        self.memory_bar.pack(side=tk.LEFT, padx=10)
        self.memory_label = ttk.Label(mem_frame, text="0 / 1024 MB")
        self.memory_label.pack(side=tk.LEFT, padx=5)
        
        # Available resources
        res_frame = ttk.Frame(frame)
        res_frame.pack(fill=tk.X, pady=5)
        ttk.Label(res_frame, text="Available:").pack(side=tk.LEFT)
        self.resource_labels = []
        for i in range(3):
            lbl = ttk.Label(res_frame, text=f"R{i}: --", font=FONTS["small"])
            lbl.pack(side=tk.LEFT, padx=10)
            self.resource_labels.append(lbl)
    
    def _create_charts_panel(self, parent):
        """Create charts panel."""
        frame = ttk.LabelFrame(parent, text="Performance Charts", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS['bg_panel'])
        
        # CPU Usage chart
        self.cpu_ax = self.fig.add_subplot(211)
        self.cpu_ax.set_facecolor(COLORS['bg_panel'])
        self.cpu_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.cpu_ax.spines.values():
            spine.set_color(COLORS['border'])
        self.cpu_ax.set_title('CPU Utilization', color='white')
        self.cpu_ax.set_ylabel('%', color='white')
        self.cpu_ax.set_ylim(0, 100)
        
        # Memory Usage chart
        self.mem_ax = self.fig.add_subplot(212)
        self.mem_ax.set_facecolor(COLORS['bg_panel'])
        self.mem_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.mem_ax.spines.values():
            spine.set_color(COLORS['border'])
        self.mem_ax.set_title('Memory Usage', color='white')
        self.mem_ax.set_ylabel('MB', color='white')
        self.mem_ax.set_ylim(0, 1024)
        
        self.fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _start_updates(self):
        """Start periodic updates."""
        self._update()
    
    def _update(self):
        """Update system monitor."""
        if not self.running:
            return
        
        # Simulate system activity
        self._simulate_activity()
        self._update_ui()
        
        self.update_after_id = self.parent.after(1000, self._update)
    
    def _simulate_activity(self):
        """Simulate system activity for demo."""
        # Randomly vary metrics
        self.system_state["cpu_util"] = max(0, min(100, 
            self.system_state["cpu_util"] + random.uniform(-5, 5)))
        
        # Memory fluctuates
        self.system_state["memory_used"] = max(0, min(self.system_state["memory_total"],
            self.system_state["memory_used"] + random.randint(-20, 20)))
        
        # Process counts
        total = self.system_state["total_processes"]
        if total > 0:
            # Redistribute
            running = max(1, min(total, int(total * self.system_state["cpu_util"] / 100)))
            ready = max(0, total - running - self.system_state["waiting"] - self.system_state["terminated"])
            self.system_state["running"] = running
            self.system_state["ready"] = ready
        
        # Resources
        for i in range(3):
            self.system_state["available_resources"][i] = max(0, 
                self.system_state["available_resources"][i] + random.randint(-1, 1))
        
        # History
        current_time = time.time()
        self.history["time"].append(current_time)
        self.history["cpu"].append(self.system_state["cpu_util"])
        self.history["memory"].append(self.system_state["memory_used"])
        
        # Keep last 60 seconds
        if len(self.history["time"]) > 60:
            self.history["time"] = self.history["time"][-60:]
            self.history["cpu"] = self.history["cpu"][-60:]
            self.history["memory"] = self.history["memory"][-60:]
    
    def _update_ui(self):
        """Update UI elements."""
        # Metrics
        self.metric_labels["total_processes"].config(text=str(self.system_state["total_processes"]))
        self.metric_labels["running"].config(text=str(self.system_state["running"]))
        self.metric_labels["ready"].config(text=str(self.system_state["ready"]))
        self.metric_labels["waiting"].config(text=str(self.system_state["waiting"]))
        self.metric_labels["terminated"].config(text=str(self.system_state["terminated"]))
        self.metric_labels["cpu_util"].config(text=f"{self.system_state['cpu_util']:.1f}%")
        
        # Memory bar
        mem_pct = (self.system_state["memory_used"] / self.system_state["memory_total"]) * 100
        self.memory_bar['value'] = mem_pct
        self.memory_label.config(text=f"{self.system_state['memory_used']} / {self.system_state['memory_total']} MB")
        
        # Resources
        for i, lbl in enumerate(self.resource_labels):
            lbl.config(text=f"R{i}: {self.system_state['available_resources'][i]}")
        
        # Process list (simulated)
        self._update_process_list()
        
        # Charts
        self._update_charts()
    
    def _update_process_list(self):
        """Update process list with simulated data."""
        # Clear
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # Generate simulated processes
        states = ["RUNNING", "READY", "WAITING"]
        for i in range(self.system_state["total_processes"]):
            if i < self.system_state["running"]:
                state = "RUNNING"
                cpu = random.uniform(5, 50)
                core = random.randint(0, 3)
            elif i < self.system_state["running"] + self.system_state["ready"]:
                state = "READY"
                cpu = 0.0
                core = -1
            else:
                state = "WAITING"
                cpu = 0.0
                core = -1
            
            self.process_tree.insert("", tk.END, values=(
                f"P{i+1}", state, f"{cpu:.1f}%", 
                f"{random.randint(10, 100)}MB", random.randint(0, 5), 
                core if core >= 0 else "-"
            ))
    
    def _update_charts(self):
        """Update charts."""
        self.cpu_ax.clear()
        self.cpu_ax.set_facecolor(COLORS['bg_panel'])
        self.cpu_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.cpu_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.mem_ax.clear()
        self.mem_ax.set_facecolor(COLORS['bg_panel'])
        self.mem_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.mem_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if len(self.history["time"]) > 1:
            # Relative time
            times = [t - self.history["time"][0] for t in self.history["time"]]
            
            self.cpu_ax.plot(times, self.history["cpu"], color=COLORS['accent'], linewidth=2)
            self.cpu_ax.fill_between(times, self.history["cpu"], alpha=0.3, color=COLORS['accent'])
            self.cpu_ax.set_ylim(0, 100)
            self.cpu_ax.set_title('CPU Utilization', color='white')
            self.cpu_ax.set_ylabel('%', color='white')
            
            self.mem_ax.plot(times, self.history["memory"], color=COLORS['success'], linewidth=2)
            self.mem_ax.fill_between(times, self.history["memory"], alpha=0.3, color=COLORS['success'])
            self.mem_ax.set_ylim(0, self.system_state["memory_total"])
            self.mem_ax.set_title('Memory Usage', color='white')
            self.mem_ax.set_ylabel('MB', color='white')
            self.mem_ax.set_xlabel('Time (s)', color='white')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def set_system_state(self, state: dict):
        """Update system state from actual simulation."""
        self.system_state.update(state)
        self._update_ui()
    
    def stop(self):
        """Stop updates."""
        self.running = False
        if self.update_after_id:
            self.parent.after_cancel(self.update_after_id)


def create_system_monitor_module(parent_window, content_frame):
    """Factory function to create system monitor module."""
    return SystemMonitorWindow(parent_window, content_frame)
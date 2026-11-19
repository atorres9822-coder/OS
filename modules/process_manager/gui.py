"""
Process Manager GUI Module for Mini OS Simulator.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import COLORS, FONTS
from modules.process_manager.algorithms import (
    ProcessManager, SimulatedProcess, ProcessState, TransitionReason,
    MultiprogrammingResult, MultiprocessingResult, CPUScheduleEvent,
    generate_sample_processes
)


class ProcessManagerWindow:
    """Process Manager simulation window."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        self.mp_result: Optional[MultiprogrammingResult] = None
        self.mpc_result: Optional[MultiprocessingResult] = None
        self.playback_time = 0.0
        self.playback_running = False
        self.playback_speed = 1.0
        self.playback_after_id = None
        
        self._setup_ui()
        self._load_sample_data()
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Notebook for multiprogramming vs multiprocessing
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Multiprogramming
        self.mp_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mp_frame, text="Multiprogramming (Single CPU)")
        self._create_multiprogramming_tab()
        
        # Tab 2: Multiprocessing
        self.mpc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mpc_frame, text="Multiprocessing (Multi-Core)")
        self._create_multiprocessing_tab()
    
    # ==================== MULTIPROGRAMMING TAB ====================
    
    def _create_multiprogramming_tab(self):
        """Create multiprogramming tab."""
        main_paned = ttk.PanedWindow(self.mp_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Configuration
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_mp_config(left)
        self._create_mp_controls(left)
        self._create_mp_results(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_mp_visualization(right)
    
    def _create_mp_config(self, parent):
        """Create multiprogramming configuration."""
        frame = ttk.LabelFrame(parent, text="Process Configuration", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Process list
        columns = ("PID", "Arrival", "Burst", "I/O Freq", "Priority")
        self.mp_tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.mp_tree.heading(col, text=col)
            self.mp_tree.column(col, width=70, anchor=tk.CENTER)
        self.mp_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add process form
        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(form, text="PID:").grid(row=0, column=0, padx=2)
        self.mp_pid_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.mp_pid_var, width=8).grid(row=0, column=1, padx=2)
        
        ttk.Label(form, text="Arrival:").grid(row=0, column=2, padx=2)
        self.mp_arrival_var = tk.DoubleVar(value=0.0)
        ttk.Entry(form, textvariable=self.mp_arrival_var, width=8).grid(row=0, column=3, padx=2)
        
        ttk.Label(form, text="Burst:").grid(row=0, column=4, padx=2)
        self.mp_burst_var = tk.DoubleVar(value=10.0)
        ttk.Entry(form, textvariable=self.mp_burst_var, width=8).grid(row=0, column=5, padx=2)
        
        ttk.Label(form, text="I/O Freq:").grid(row=0, column=6, padx=2)
        self.mp_io_var = tk.DoubleVar(value=0.0)
        ttk.Entry(form, textvariable=self.mp_io_var, width=8).grid(row=0, column=7, padx=2)
        
        ttk.Label(form, text="Priority:").grid(row=0, column=8, padx=2)
        self.mp_priority_var = tk.IntVar(value=0)
        ttk.Entry(form, textvariable=self.mp_priority_var, width=5).grid(row=0, column=9, padx=2)
        
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=0, column=10, padx=5)
        ttk.Button(btn_frame, text="Add", command=self._mp_add_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._mp_remove_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", command=self._mp_clear_processes).pack(side=tk.LEFT, padx=2)
        
        self.mp_tree.bind("<<TreeviewSelect>>", self._mp_on_select)
        
        # Simulation params
        param_frame = ttk.LabelFrame(frame, text="Simulation Parameters", padding=5)
        param_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(param_frame, text="Time Slice:").pack(side=tk.LEFT, padx=5)
        self.mp_timeslice_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(param_frame, from_=0.1, to=10.0, increment=0.1, 
                   textvariable=self.mp_timeslice_var, width=8).pack(side=tk.LEFT, padx=5)
    
    def _create_mp_controls(self, parent):
        """Create simulation controls."""
        frame = ttk.LabelFrame(parent, text="Simulation Controls", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Playback controls
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill=tk.X)
        
        ttk.Button(ctrl_frame, text="▶ Run", command=self._mp_run).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏸ Pause", command=self._mp_pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏹ Stop", command=self._mp_stop).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏮ Reset", command=self._mp_reset).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(ctrl_frame, text="Speed:").pack(side=tk.LEFT, padx=(20, 5))
        self.mp_speed_var = tk.DoubleVar(value=1.0)
        ttk.Scale(ctrl_frame, from_=0.1, to=5.0, variable=self.mp_speed_var, 
                 orient=tk.HORIZONTAL, length=100).pack(side=tk.LEFT, padx=5)
        
        # Current time display
        self.mp_time_label = ttk.Label(ctrl_frame, text="Time: 0.00")
        self.mp_time_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_mp_results(self, parent):
        """Create results panel."""
        frame = ttk.LabelFrame(parent, text="Results", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Metrics
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mp_metrics = {}
        for i, (label, key) in enumerate([
            ("CPU Utilization", "cpu_util"), ("Throughput", "throughput"),
            ("Avg Turnaround", "avg_turnaround"), ("Avg Waiting", "avg_waiting"),
            ("Avg Response", "avg_response"), ("Context Switches", "ctx_switches"),
            ("Max Multiprogramming", "max_mp")
        ]):
            row, col = divmod(i, 3)
            f = ttk.Frame(metrics_frame)
            f.grid(row=row, column=col, padx=8, pady=3, sticky=tk.W)
            ttk.Label(f, text=f"{label}:", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
            self.mp_metrics[key] = ttk.Label(f, text="--", font=("Segoe UI", 8))
            self.mp_metrics[key].pack(side=tk.LEFT, padx=3)
        
        # Schedule log
        self.mp_log = tk.Text(frame, height=10, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono_small"])
        self.mp_log.pack(fill=tk.BOTH, expand=True)
    
    def _create_mp_visualization(self, parent):
        """Create Gantt chart visualization."""
        frame = ttk.LabelFrame(parent, text="CPU Timeline", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.mp_fig = Figure(figsize=(8, 4), dpi=100, facecolor=COLORS['bg_panel'])
        self.mp_ax = self.mp_fig.add_subplot(111)
        self.mp_ax.set_facecolor(COLORS['bg_panel'])
        self.mp_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.mp_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.mp_canvas = FigureCanvasTkAgg(self.mp_fig, master=frame)
        self.mp_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # ==================== MULTIPROCESSING TAB ====================
    
    def _create_multiprocessing_tab(self):
        """Create multiprocessing tab."""
        main_paned = ttk.PanedWindow(self.mpc_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Configuration
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_mpc_config(left)
        self._create_mpc_controls(left)
        self._create_mpc_results(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_mpc_visualization(right)
    
    def _create_mpc_config(self, parent):
        """Create multiprocessing configuration."""
        frame = ttk.LabelFrame(parent, text="Process Configuration", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Process list (shared with MP)
        columns = ("PID", "Arrival", "Burst", "I/O Freq", "Priority")
        self.mpc_tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.mpc_tree.heading(col, text=col)
            self.mpc_tree.column(col, width=70, anchor=tk.CENTER)
        self.mpc_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add process form
        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(form, text="PID:").grid(row=0, column=0, padx=2)
        self.mpc_pid_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.mpc_pid_var, width=8).grid(row=0, column=1, padx=2)
        
        ttk.Label(form, text="Arrival:").grid(row=0, column=2, padx=2)
        self.mpc_arrival_var = tk.DoubleVar(value=0.0)
        ttk.Entry(form, textvariable=self.mpc_arrival_var, width=8).grid(row=0, column=3, padx=2)
        
        ttk.Label(form, text="Burst:").grid(row=0, column=4, padx=2)
        self.mpc_burst_var = tk.DoubleVar(value=10.0)
        ttk.Entry(form, textvariable=self.mpc_burst_var, width=8).grid(row=0, column=5, padx=2)
        
        ttk.Label(form, text="I/O Freq:").grid(row=0, column=6, padx=2)
        self.mpc_io_var = tk.DoubleVar(value=0.0)
        ttk.Entry(form, textvariable=self.mpc_io_var, width=8).grid(row=0, column=7, padx=2)
        
        ttk.Label(form, text="Priority:").grid(row=0, column=8, padx=2)
        self.mpc_priority_var = tk.IntVar(value=0)
        ttk.Entry(form, textvariable=self.mpc_priority_var, width=5).grid(row=0, column=9, padx=2)
        
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=0, column=10, padx=5)
        ttk.Button(btn_frame, text="Add", command=self._mpc_add_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._mpc_remove_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", command=self._mpc_clear_processes).pack(side=tk.LEFT, padx=2)
        
        self.mpc_tree.bind("<<TreeviewSelect>>", self._mpc_on_select)
        
        # Simulation params
        param_frame = ttk.LabelFrame(frame, text="Simulation Parameters", padding=5)
        param_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(param_frame, text="Cores:").pack(side=tk.LEFT, padx=5)
        self.mpc_cores_var = tk.IntVar(value=2)
        ttk.Spinbox(param_frame, from_=1, to=16, textvariable=self.mpc_cores_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_frame, text="Time Slice:").pack(side=tk.LEFT, padx=5)
        self.mpc_timeslice_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(param_frame, from_=0.1, to=10.0, increment=0.1,
                   textvariable=self.mpc_timeslice_var, width=8).pack(side=tk.LEFT, padx=5)
    
    def _create_mpc_controls(self, parent):
        """Create multiprocessing controls."""
        frame = ttk.LabelFrame(parent, text="Simulation Controls", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill=tk.X)
        
        ttk.Button(ctrl_frame, text="▶ Run", command=self._mpc_run).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏸ Pause", command=self._mpc_pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏹ Stop", command=self._mpc_stop).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏮ Reset", command=self._mpc_reset).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(ctrl_frame, text="Speed:").pack(side=tk.LEFT, padx=(20, 5))
        self.mpc_speed_var = tk.DoubleVar(value=1.0)
        ttk.Scale(ctrl_frame, from_=0.1, to=5.0, variable=self.mpc_speed_var,
                 orient=tk.HORIZONTAL, length=100).pack(side=tk.LEFT, padx=5)
        
        self.mpc_time_label = ttk.Label(ctrl_frame, text="Time: 0.00")
        self.mpc_time_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_mpc_results(self, parent):
        """Create multiprocessing results."""
        frame = ttk.LabelFrame(parent, text="Results", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mpc_metrics = {}
        for i, (label, key) in enumerate([
            ("Overall CPU Util", "overall_util"), ("Throughput", "throughput"),
            ("Avg Turnaround", "avg_turnaround"), ("Avg Waiting", "avg_waiting"),
            ("Avg Response", "avg_response"), ("Total Time", "total_time")
        ]):
            row, col = divmod(i, 3)
            f = ttk.Frame(metrics_frame)
            f.grid(row=row, column=col, padx=8, pady=3, sticky=tk.W)
            ttk.Label(f, text=f"{label}:", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
            self.mpc_metrics[key] = ttk.Label(f, text="--", font=("Segoe UI", 8))
            self.mpc_metrics[key].pack(side=tk.LEFT, padx=3)
        
        # Per-core utilization
        self.mpc_core_labels = {}
        core_frame = ttk.LabelFrame(frame, text="Per-Core Utilization", padding=5)
        core_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mpc_core_frame = core_frame
        
        # Schedule log
        self.mpc_log = tk.Text(frame, height=10, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono_small"])
        self.mpc_log.pack(fill=tk.BOTH, expand=True)
    
    def _create_mpc_visualization(self, parent):
        """Create multiprocessing visualization."""
        frame = ttk.LabelFrame(parent, text="Multi-Core Timeline", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.mpc_fig = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS['bg_panel'])
        self.mpc_ax = self.mpc_fig.add_subplot(111)
        self.mpc_ax.set_facecolor(COLORS['bg_panel'])
        self.mpc_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.mpc_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.mpc_canvas = FigureCanvasTkAgg(self.mpc_fig, master=frame)
        self.mpc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _load_sample_data(self):
        """Load sample processes."""
        sample = generate_sample_processes()
        
        # Multiprogramming tab
        for p in sample:
            self.mp_tree.insert("", tk.END, values=(p.pid, p.arrival_time, p.burst_time, p.io_frequency, p.priority))
        
        # Multiprocessing tab
        for p in sample:
            self.mpc_tree.insert("", tk.END, values=(p.pid, p.arrival_time, p.burst_time, p.io_frequency, p.priority))


def create_process_manager_module(parent_window, content_frame):
    """Factory function to create process manager module."""
    return ProcessManagerWindow(parent_window, content_frame)
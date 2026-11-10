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
        
        # Tab 3: Process State Diagram
        self.state_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.state_frame, text="State Transitions")
        self._create_state_diagram_tab()
    
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
        self.mp_log = tk.Text(frame, height=10, bg="#1e1e1e", fg="#ffffff", font=("Consolas", 8))
        self.mp_log.pack(fill=tk.BOTH, expand=True)
    
    def _create_mp_visualization(self, parent):
        """Create Gantt chart visualization."""
        frame = ttk.LabelFrame(parent, text="CPU Timeline", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.mp_fig = Figure(figsize=(8, 4), dpi=100, facecolor='#1e1e1e')
        self.mp_ax = self.mp_fig.add_subplot(111)
        self.mp_ax.set_facecolor('#1e1e1e')
        self.mp_ax.tick_params(colors='white')
        for spine in self.mp_ax.spines.values():
            spine.set_color('#555555')
        
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
        self.mpc_log = tk.Text(frame, height=10, bg="#1e1e1e", fg="#ffffff", font=("Consolas", 8))
        self.mpc_log.pack(fill=tk.BOTH, expand=True)
    
    def _create_mpc_visualization(self, parent):
        """Create multiprocessing visualization."""
        frame = ttk.LabelFrame(parent, text="Multi-Core Timeline", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.mpc_fig = Figure(figsize=(8, 5), dpi=100, facecolor='#1e1e1e')
        self.mpc_ax = self.mpc_fig.add_subplot(111)
        self.mpc_ax.set_facecolor('#1e1e1e')
        self.mpc_ax.tick_params(colors='white')
        for spine in self.mpc_ax.spines.values():
            spine.set_color('#555555')
        
        self.mpc_canvas = FigureCanvasTkAgg(self.mpc_fig, master=frame)
        self.mpc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # ==================== STATE DIAGRAM TAB ====================
    
    def _create_state_diagram_tab(self):
        """Create process state diagram tab."""
        frame = ttk.Frame(self.state_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Process State Transition Diagram", 
                 font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Canvas for diagram
        self.state_canvas = tk.Canvas(frame, bg="#1e1e1e", highlightthickness=0)
        self.state_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Explanation
        exp_frame = ttk.LabelFrame(frame, text="State Descriptions", padding=10)
        exp_frame.pack(fill=tk.X, pady=(10, 0))
        
        explanations = {
            "NEW": "Process is being created; PCB allocated but not yet in memory.",
            "READY": "Process is in memory, waiting for CPU assignment.",
            "RUNNING": "Process is currently executing on CPU.",
            "WAITING": "Process is blocked waiting for I/O or event.",
            "TERMINATED": "Process has finished execution; resources released."
        }
        
        for state, desc in explanations.items():
            f = ttk.Frame(exp_frame)
            f.pack(fill=tk.X, pady=2)
            ttk.Label(f, text=f"{state}:", font=("Segoe UI", 9, "bold"), width=12).pack(side=tk.LEFT)
            ttk.Label(f, text=desc, font=("Segoe UI", 9), wraplength=600).pack(side=tk.LEFT, padx=5)
        
        # Transitions
        trans_frame = ttk.LabelFrame(frame, text="Transitions", padding=10)
        trans_frame.pack(fill=tk.X, pady=(10, 0))
        
        transitions = [
            ("NEW → READY", "Admitted / Loaded into memory"),
            ("READY → RUNNING", "Scheduler dispatches process"),
            ("RUNNING → READY", "Time slice expired / Preempted"),
            ("RUNNING → WAITING", "I/O request / Event wait"),
            ("WAITING → READY", "I/O complete / Event signaled"),
            ("RUNNING → TERMINATED", "Process exits / Killed"),
        ]
        
        for trans, desc in transitions:
            f = ttk.Frame(trans_frame)
            f.pack(fill=tk.X, pady=2)
            ttk.Label(f, text=f"{trans}:", font=("Segoe UI", 9, "bold"), width=22).pack(side=tk.LEFT)
            ttk.Label(f, text=desc, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        
        # Draw diagram after window is ready
        self.parent.after(100, self._draw_state_diagram)
    
    def _draw_state_diagram(self):
        """Draw the process state transition diagram."""
        c = self.state_canvas
        c.delete("all")
        width = c.winfo_width() or 800
        height = c.winfo_height() or 400
        
        # State positions (x, y)
        states = {
            "NEW": (100, height // 2),
            "READY": (280, height // 2),
            "RUNNING": (460, height // 2),
            "WAITING": (460, height // 2 - 120),
            "TERMINATED": (640, height // 2),
        }
        
        colors = {
            "NEW": "#8764b8",
            "READY": "#0078d7",
            "RUNNING": "#00b294",
            "WAITING": "#ff8c00",
            "TERMINATED": "#e81123",
        }
        
        # Draw states
        for state, (x, y) in states.items():
            color = colors[state]
            # Rounded rectangle
            w, h = 120, 50
            c.create_oval(x, y, x + w, y + h, fill=color, outline="white", width=2)
            c.create_text(x + w//2, y + h//2, text=state, fill="white", font=("Segoe UI", 10, "bold"))
        
        # Draw transitions
        transitions = [
            ("NEW", "READY", "Admitted", "bottom"),
            ("READY", "RUNNING", "Dispatch", "bottom"),
            ("RUNNING", "READY", "Timeout/Preempt", "top"),
            ("RUNNING", "WAITING", "I/O Request", "right"),
            ("WAITING", "READY", "I/O Complete", "left"),
            ("RUNNING", "TERMINATED", "Exit", "bottom"),
        ]
        
        for from_state, to_state, label, pos in transitions:
            fx, fy = states[from_state]
            tx, ty = states[to_state]
            
            # Calculate edge points
            w, h = 120, 50
            if from_state == "NEW" and to_state == "READY":
                sx, sy = fx + w, fy + h//2
                ex, ey = tx, ty + h//2
            elif from_state == "READY" and to_state == "RUNNING":
                sx, sy = fx + w, fy + h//2
                ex, ey = tx, ty + h//2
            elif from_state == "RUNNING" and to_state == "READY":
                sx, sy = fx, fy + h//2
                ex, ey = tx + w, ty + h//2
            elif from_state == "RUNNING" and to_state == "WAITING":
                sx, sy = fx + w//2, fy
                ex, ey = tx + w//2, ty + h
            elif from_state == "WAITING" and to_state == "READY":
                sx, sy = fx + w//2, fy + h
                ex, ey = tx + w//2, ty
            elif from_state == "RUNNING" and to_state == "TERMINATED":
                sx, sy = fx + w, fy + h//2
                ex, ey = tx, ty + h//2
            else:
                continue
            
            # Draw arrow
            c.create_line(sx, sy, ex, ey, fill="white", width=2, arrow=tk.LAST, arrowshape=(15, 18, 6))
            
            # Label
            lx, ly = (sx + ex) // 2, (sy + ey) // 2
            if from_state == "RUNNING" and to_state == "WAITING":
                lx += 60
            elif from_state == "WAITING" and to_state == "READY":
                lx -= 60
            elif from_state == "RUNNING" and to_state == "READY":
                ly -= 30
            
            c.create_text(lx, ly, text=label, fill="#ff8c00", font=("Segoe UI", 8))
    
    # ==================== MULTIPROGRAMMING METHODS ====================
    
    def _mp_add_process(self):
        """Add process to multiprogramming list."""
        try:
            pid = self.mp_pid_var.get().strip()
            arrival = self.mp_arrival_var.get()
            burst = self.mp_burst_var.get()
            io_freq = self.mp_io_var.get()
            priority = self.mp_priority_var.get()
            
            if not pid:
                messagebox.showerror("Error", "Process ID required")
                return
            
            if any(self.mp_tree.item(item)['values'][0] == pid for item in self.mp_tree.get_children()):
                messagebox.showerror("Error", f"Process {pid} already exists")
                return
            
            if arrival < 0 or burst <= 0 or io_freq < 0:
                messagebox.showerror("Error", "Invalid values")
                return
            
            self.mp_tree.insert("", tk.END, values=(pid, arrival, burst, io_freq, priority))
            self._mp_clear_form()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _mp_remove_process(self):
        """Remove selected process."""
        selection = self.mp_tree.selection()
        if selection:
            self.mp_tree.delete(selection[0])
    
    def _mp_clear_processes(self):
        """Clear all processes."""
        for item in self.mp_tree.get_children():
            self.mp_tree.delete(item)
    
    def _mp_clear_form(self):
        """Clear input form."""
        self.mp_pid_var.set("")
        self.mp_arrival_var.set(0.0)
        self.mp_burst_var.set(10.0)
        self.mp_io_var.set(0.0)
        self.mp_priority_var.set(0)
    
    def _mp_on_select(self, event):
        """Handle selection."""
        selection = self.mp_tree.selection()
        if selection:
            vals = self.mp_tree.item(selection[0])['values']
            self.mp_pid_var.set(vals[0])
            self.mp_arrival_var.set(vals[1])
            self.mp_burst_var.set(vals[2])
            self.mp_io_var.set(vals[3])
            self.mp_priority_var.set(vals[4])
    
    def _mp_run(self):
        """Run multiprogramming simulation."""
        processes = self._get_mp_processes()
        if not processes:
            messagebox.showerror("Error", "No processes defined")
            return
        
        time_slice = self.mp_timeslice_var.get()
        
        try:
            self.mp_result = ProcessManager.simulate_multiprogramming(processes, time_slice)
            self._display_mp_results()
            self._mp_start_playback()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _get_mp_processes(self) -> List[SimulatedProcess]:
        """Get processes from tree."""
        processes = []
        for item in self.mp_tree.get_children():
            vals = self.mp_tree.item(item)['values']
            processes.append(SimulatedProcess(
                pid=vals[0], arrival_time=vals[1], burst_time=vals[2],
                io_frequency=vals[3], priority=vals[4]
            ))
        return processes
    
    def _display_mp_results(self):
        """Display multiprogramming results."""
        if not self.mp_result:
            return
        
        r = self.mp_result
        self.mp_metrics["cpu_util"].config(text=f"{r.cpu_utilization:.1f}%")
        self.mp_metrics["throughput"].config(text=f"{r.throughput:.3f} proc/unit")
        self.mp_metrics["avg_turnaround"].config(text=f"{r.avg_turnaround:.2f}")
        self.mp_metrics["avg_waiting"].config(text=f"{r.avg_waiting:.2f}")
        self.mp_metrics["avg_response"].config(text=f"{r.avg_response:.2f}")
        self.mp_metrics["ctx_switches"].config(text=str(r.context_switches))
        self.mp_metrics["max_mp"].config(text=str(r.degree_of_multiprogramming))
        
        # Log
        self.mp_log.delete(1.0, tk.END)
        for event in r.schedule:
            self.mp_log.insert(tk.END, f"[{event.time:6.2f}] {event.process_id:>4} | {event.event_type:<10} | {event.details}\n")
        
        self._draw_mp_gantt()
    
    def _draw_mp_gantt(self):
        """Draw multiprogramming Gantt chart."""
        self.mp_ax.clear()
        self.mp_ax.set_facecolor('#1e1e1e')
        self.mp_ax.tick_params(colors='white')
        for spine in self.mp_ax.spines.values():
            spine.set_color('#555555')
        
        if not self.mp_result:
            self.mp_canvas.draw()
            return
        
        r = self.mp_result
        
        # Build timeline from schedule
        events = r.schedule
        if not events:
            self.mp_canvas.draw()
            return
        
        # Group by process
        proc_intervals = {}
        current_proc = None
        start_time = 0
        
        for event in events:
            if event.event_type == "start":
                if current_proc:
                    if current_proc not in proc_intervals:
                        proc_intervals[current_proc] = []
                    proc_intervals[current_proc].append((start_time, event.time))
                current_proc = event.process_id
                start_time = event.time
            elif event.event_type in ("preempt", "io", "complete"):
                if current_proc:
                    if current_proc not in proc_intervals:
                        proc_intervals[current_proc] = []
                    proc_intervals[current_proc].append((start_time, event.time))
                current_proc = None
        
        # Colors
        procs = list(proc_intervals.keys())
        colors = ['#0078d7', '#e81123', '#00b294', '#ff8c00', '#8764b8', '#e67e22']
        color_map = {p: colors[i % len(colors)] for i, p in enumerate(procs)}
        
        y = 0.5
        for proc, intervals in proc_intervals.items():
            for start, end in intervals:
                self.mp_ax.barh(y, end - start, left=start, height=0.6,
                               color=color_map[proc], edgecolor='white', linewidth=0.5)
                if end - start > 1:
                    self.mp_ax.text(start + (end-start)/2, y, proc, ha='center', va='center',
                                   color='white', fontsize=8, fontweight='bold')
            y += 1
        
        self.mp_ax.set_ylim(0, len(procs) + 0.5)
        self.mp_ax.set_xlim(0, r.total_time * 1.05)
        self.mp_ax.set_yticks([i + 0.5 for i in range(len(procs))])
        self.mp_ax.set_yticklabels(procs)
        self.mp_ax.set_xlabel('Time', color='white')
        self.mp_ax.set_title('Multiprogramming CPU Timeline', color='white')
        
        self.mp_fig.tight_layout()
        self.mp_canvas.draw()
    
    def _mp_start_playback(self):
        """Start playback animation."""
        self.playback_running = True
        self.playback_time = 0.0
        self._mp_playback_step()
    
    def _mp_playback_step(self):
        """Playback step."""
        if not self.playback_running or not self.mp_result:
            return
        
        self.playback_time += 0.1 * self.playback_speed
        if self.playback_time > self.mp_result.total_time:
            self.playback_time = self.mp_result.total_time
            self.playback_running = False
        
        self.mp_time_label.config(text=f"Time: {self.playback_time:.2f}")
        self._draw_mp_playback()
        
        if self.playback_running:
            self.playback_after_id = self.parent.after(50, self._mp_playback_step)
    
    def _draw_mp_playback(self):
        """Draw current playback state."""
        self._draw_mp_gantt()
        # Add vertical line at current time
        self.mp_ax.axvline(x=self.playback_time, color='yellow', linewidth=2, linestyle='--')
        self.mp_canvas.draw()
    
    def _mp_pause(self):
        """Pause playback."""
        self.playback_running = False
        if self.playback_after_id:
            self.parent.after_cancel(self.playback_after_id)
    
    def _mp_stop(self):
        """Stop playback."""
        self._mp_pause()
        self.playback_time = 0.0
        self.mp_time_label.config(text="Time: 0.00")
        self._draw_mp_gantt()
    
    def _mp_reset(self):
        """Reset simulation."""
        self._mp_stop()
        self.mp_result = None
        for key in self.mp_metrics:
            self.mp_metrics[key].config(text="--")
        self.mp_log.delete(1.0, tk.END)
        self.mp_ax.clear()
        self.mp_canvas.draw()
    
    # ==================== MULTIPROCESSING METHODS ====================
    
    def _mpc_add_process(self):
        """Add process to multiprocessing list."""
        try:
            pid = self.mpc_pid_var.get().strip()
            arrival = self.mpc_arrival_var.get()
            burst = self.mpc_burst_var.get()
            io_freq = self.mpc_io_var.get()
            priority = self.mpc_priority_var.get()
            
            if not pid:
                messagebox.showerror("Error", "Process ID required")
                return
            
            if any(self.mpc_tree.item(item)['values'][0] == pid for item in self.mpc_tree.get_children()):
                messagebox.showerror("Error", f"Process {pid} already exists")
                return
            
            if arrival < 0 or burst <= 0 or io_freq < 0:
                messagebox.showerror("Error", "Invalid values")
                return
            
            self.mpc_tree.insert("", tk.END, values=(pid, arrival, burst, io_freq, priority))
            self._mpc_clear_form()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _mpc_remove_process(self):
        """Remove selected process."""
        selection = self.mpc_tree.selection()
        if selection:
            self.mpc_tree.delete(selection[0])
    
    def _mpc_clear_processes(self):
        """Clear all processes."""
        for item in self.mpc_tree.get_children():
            self.mpc_tree.delete(item)
    
    def _mpc_clear_form(self):
        """Clear input form."""
        self.mpc_pid_var.set("")
        self.mpc_arrival_var.set(0.0)
        self.mpc_burst_var.set(10.0)
        self.mpc_io_var.set(0.0)
        self.mpc_priority_var.set(0)
    
    def _mpc_on_select(self, event):
        """Handle selection."""
        selection = self.mpc_tree.selection()
        if selection:
            vals = self.mpc_tree.item(selection[0])['values']
            self.mpc_pid_var.set(vals[0])
            self.mpc_arrival_var.set(vals[1])
            self.mpc_burst_var.set(vals[2])
            self.mpc_io_var.set(vals[3])
            self.mpc_priority_var.set(vals[4])
    
    def _get_mpc_processes(self) -> List[SimulatedProcess]:
        """Get processes from tree."""
        processes = []
        for item in self.mpc_tree.get_children():
            vals = self.mpc_tree.item(item)['values']
            processes.append(SimulatedProcess(
                pid=vals[0], arrival_time=vals[1], burst_time=vals[2],
                io_frequency=vals[3], priority=vals[4]
            ))
        return processes
    
    def _mpc_run(self):
        """Run multiprocessing simulation."""
        processes = self._get_mpc_processes()
        if not processes:
            messagebox.showerror("Error", "No processes defined")
            return
        
        num_cores = self.mpc_cores_var.get()
        time_slice = self.mpc_timeslice_var.get()
        
        try:
            self.mpc_result = ProcessManager.simulate_multiprocessing(processes, num_cores, time_slice)
            self._display_mpc_results()
            self._mpc_start_playback()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _display_mpc_results(self):
        """Display multiprocessing results."""
        if not self.mpc_result:
            return
        
        r = self.mpc_result
        self.mpc_metrics["overall_util"].config(text=f"{r.overall_cpu_utilization:.1f}%")
        self.mpc_metrics["throughput"].config(text=f"{r.throughput:.3f} proc/unit")
        self.mpc_metrics["avg_turnaround"].config(text=f"{r.avg_turnaround:.2f}")
        self.mpc_metrics["avg_waiting"].config(text=f"{r.avg_waiting:.2f}")
        self.mpc_metrics["avg_response"].config(text=f"{r.avg_response:.2f}")
        self.mpc_metrics["total_time"].config(text=f"{r.total_time:.2f}")
        
        # Per-core utilization
        for widget in self.mpc_core_frame.winfo_children():
            widget.destroy()
        
        for core_id, util in sorted(r.core_utilizations.items()):
            f = ttk.Frame(self.mpc_core_frame)
            f.pack(side=tk.LEFT, padx=20, pady=5)
            ttk.Label(f, text=f"Core {core_id}:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(f, text=f"{util:.1f}%", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        
        # Log
        self.mpc_log.delete(1.0, tk.END)
        for core_id in sorted(r.core_schedules.keys()):
            self.mpc_log.insert(tk.END, f"=== Core {core_id} ===\n")
            for event in r.core_schedules[core_id]:
                self.mpc_log.insert(tk.END, f"[{event.time:6.2f}] {event.process_id:>4} | {event.event_type:<10} | {event.details}\n")
            self.mpc_log.insert(tk.END, "\n")
        
        self._draw_mpc_gantt()
    
    def _draw_mpc_gantt(self):
        """Draw multiprocessing Gantt chart."""
        self.mpc_ax.clear()
        self.mpc_ax.set_facecolor('#1e1e1e')
        self.mpc_ax.tick_params(colors='white')
        for spine in self.mpc_ax.spines.values():
            spine.set_color('#555555')
        
        if not self.mpc_result:
            self.mpc_canvas.draw()
            return
        
        r = self.mpc_result
        num_cores = len(r.core_schedules)
        
        # Collect all processes
        all_procs = set()
        for core_sched in r.core_schedules.values():
            for event in core_sched:
                all_procs.add(event.process_id)
        
        procs = sorted(all_procs)
        colors = ['#0078d7', '#e81123', '#00b294', '#ff8c00', '#8764b8', '#e67e22']
        color_map = {p: colors[i % len(colors)] for i, p in enumerate(procs)}
        
        # Draw per-core timelines
        for core_id in sorted(r.core_schedules.keys()):
            y = core_id + 0.5
            events = r.core_schedules[core_id]
            
            current_proc = None
            start_time = 0
            
            for event in events:
                if event.event_type == "start":
                    if current_proc:
                        self.mpc_ax.barh(y, event.time - start_time, left=start_time, height=0.6,
                                        color=color_map[current_proc], edgecolor='white', linewidth=0.5)
                    current_proc = event.process_id
                    start_time = event.time
                elif event.event_type in ("preempt", "io", "complete"):
                    if current_proc:
                        self.mpc_ax.barh(y, event.time - start_time, left=start_time, height=0.6,
                                        color=color_map[current_proc], edgecolor='white', linewidth=0.5)
                    current_proc = None
        
        self.mpc_ax.set_ylim(0, num_cores)
        self.mpc_ax.set_xlim(0, r.total_time * 1.05)
        self.mpc_ax.set_yticks([i + 0.5 for i in range(num_cores)])
        self.mpc_ax.set_yticklabels([f"Core {i}" for i in range(num_cores)])
        self.mpc_ax.set_xlabel('Time', color='white')
        self.mpc_ax.set_title('Multiprocessing Core Timelines', color='white')
        
        self.mpc_fig.tight_layout()
        self.mpc_canvas.draw()
    
    def _mpc_start_playback(self):
        """Start playback."""
        self.playback_running = True
        self.playback_time = 0.0
        self._mpc_playback_step()
    
    def _mpc_playback_step(self):
        """Playback step."""
        if not self.playback_running or not self.mpc_result:
            return
        
        self.playback_time += 0.1 * self.playback_speed
        if self.playback_time > self.mpc_result.total_time:
            self.playback_time = self.mpc_result.total_time
            self.playback_running = False
        
        self.mpc_time_label.config(text=f"Time: {self.playback_time:.2f}")
        self._draw_mpc_playback()
        
        if self.playback_running:
            self.playback_after_id = self.parent.after(50, self._mpc_playback_step)
    
    def _draw_mpc_playback(self):
        """Draw playback state."""
        self._draw_mpc_gantt()
        self.mpc_ax.axvline(x=self.playback_time, color='yellow', linewidth=2, linestyle='--')
        self.mpc_canvas.draw()
    
    def _mpc_pause(self):
        """Pause."""
        self.playback_running = False
        if self.playback_after_id:
            self.parent.after_cancel(self.playback_after_id)
    
    def _mpc_stop(self):
        """Stop."""
        self._mpc_pause()
        self.playback_time = 0.0
        self.mpc_time_label.config(text="Time: 0.00")
        self._draw_mpc_gantt()
    
    def _mpc_reset(self):
        """Reset."""
        self._mpc_stop()
        self.mpc_result = None
        for key in self.mpc_metrics:
            self.mpc_metrics[key].config(text="--")
        for widget in self.mpc_core_frame.winfo_children():
            widget.destroy()
        self.mpc_log.delete(1.0, tk.END)
        self.mpc_ax.clear()
        self.mpc_canvas.draw()
    
    # ==================== COMMON ====================
    
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
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
    SchedulingAlgorithm, generate_sample_processes
)


class ProcessManagerWindow:
    """Process Manager simulation window."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        self.mp_result: Optional[MultiprogrammingResult] = None
        self.playback_time = 0.0
        self.playback_running = False
        self.playback_speed = 1.0
        self.playback_after_id = None
        
        self._setup_ui()
        self._load_sample_data()
    
    def _setup_ui(self):
        """Setup the UI components."""
        main_paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
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
    
    # ==================== MULTIPROGRAMMING CONFIG ====================
    
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
        
        # Algorithm selection
        algo_frame = ttk.Frame(param_frame)
        algo_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(algo_frame, text="Algorithm:").pack(side=tk.LEFT, padx=5)
        self.mp_algo_var = tk.StringVar(value=SchedulingAlgorithm.ROUND_ROBIN.value)
        algo_combo = ttk.Combobox(
            algo_frame,
            textvariable=self.mp_algo_var,
            values=[a.value for a in SchedulingAlgorithm],
            state="readonly",
            width=18
        )
        algo_combo.pack(side=tk.LEFT, padx=5)
        algo_combo.bind("<<ComboboxSelected>>", self._on_algo_change)
        
        # Time Slice (only relevant for Round Robin)
        ts_frame = ttk.Frame(param_frame)
        ts_frame.pack(fill=tk.X, pady=(0, 5))
        self.ts_frame = ts_frame
        ttk.Label(ts_frame, text="Time Slice:").pack(side=tk.LEFT, padx=5)
        self.mp_timeslice_var = tk.DoubleVar(value=2.0)
        self.mp_timeslice_spin = ttk.Spinbox(
            ts_frame, from_=0.1, to=10.0, increment=0.1,
            textvariable=self.mp_timeslice_var, width=8
        )
        self.mp_timeslice_spin.pack(side=tk.LEFT, padx=5)
        
        # Priority info label
        info_frame = ttk.Frame(param_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(
            info_frame,
            text="Priority: lower number = higher priority",
            font=("Segoe UI", 8),
            foreground=COLORS["text_secondary"]
        ).pack(side=tk.LEFT, padx=5)
    
    def _on_algo_change(self, event=None):
        """Handle algorithm selection change."""
        algo = SchedulingAlgorithm(self.mp_algo_var.get())
        if algo == SchedulingAlgorithm.ROUND_ROBIN:
            self.mp_timeslice_spin.configure(state="normal")
        else:
            self.mp_timeslice_spin.configure(state="disabled")
    
    # ==================== MULTIPROGRAMMING CONTROLS ====================
    
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
    
    # ==================== MULTIPROGRAMMING RESULTS ====================
    
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
    
    # ==================== MULTIPROGRAMMING VISUALIZATION ====================
    
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
    
    # ==================== MULTIPROGRAMMING HANDLERS ====================
    
    def _mp_add_process(self):
        """Add a process from form inputs."""
        try:
            pid = self.mp_pid_var.get().strip()
            arrival = self.mp_arrival_var.get()
            burst = self.mp_burst_var.get()
            io_freq = self.mp_io_var.get()
            priority = self.mp_priority_var.get()
            
            if not pid:
                messagebox.showerror("Error", "Process ID required")
                return
            if arrival < 0 or burst <= 0 or io_freq < 0:
                messagebox.showerror("Error", "Invalid values (arrival >= 0, burst > 0, io_freq >= 0)")
                return
            if any(self.mp_tree.item(item)['values'][0] == pid for item in self.mp_tree.get_children()):
                messagebox.showerror("Error", f"Process {pid} already exists")
                return
            
            self.mp_tree.insert("", tk.END, values=(pid, arrival, burst, io_freq, priority))
            self.mp_pid_var.set("")
            self.mp_arrival_var.set(0.0)
            self.mp_burst_var.set(10.0)
            self.mp_io_var.set(0.0)
            self.mp_priority_var.set(0)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _mp_remove_process(self):
        """Remove selected process."""
        selection = self.mp_tree.selection()
        if not selection:
            return
        self.mp_tree.delete(selection[0])
    
    def _mp_clear_processes(self):
        """Clear all processes."""
        for item in self.mp_tree.get_children():
            self.mp_tree.delete(item)
    
    def _mp_on_select(self, event):
        """Populate form from selected process."""
        selection = self.mp_tree.selection()
        if not selection:
            return
        values = self.mp_tree.item(selection[0])['values']
        self.mp_pid_var.set(str(values[0]))
        self.mp_arrival_var.set(float(values[1]))
        self.mp_burst_var.set(float(values[2]))
        self.mp_io_var.set(float(values[3]))
        self.mp_priority_var.set(int(values[4]))
    
    def _mp_run(self):
        """Run multiprogramming simulation."""
        processes = []
        for item in self.mp_tree.get_children():
            vals = self.mp_tree.item(item)['values']
            processes.append(SimulatedProcess(
                pid=str(vals[0]), arrival_time=float(vals[1]),
                burst_time=float(vals[2]), io_frequency=float(vals[3]),
                priority=int(vals[4])
            ))
        
        if not processes:
            messagebox.showerror("Error", "No processes defined")
            return
        
        algo = SchedulingAlgorithm(self.mp_algo_var.get())
        time_slice = self.mp_timeslice_var.get()
        self.mp_result = ProcessManager.simulate_multiprogramming(processes, algo, time_slice)
        self._display_mp_results()
    
    def _mp_pause(self):
        """Pause playback."""
        self.playback_running = False
        if self.playback_after_id:
            self.parent.after_cancel(self.playback_after_id)
    
    def _mp_stop(self):
        """Stop simulation."""
        self._mp_pause()
        self.playback_time = 0.0
        # Preserve the final simulation time in the readout;
        # only Reset clears it to 0.00.
        if self.mp_result:
            self.mp_time_label.config(text=f"Time: {self.mp_result.total_time:.2f}")
            self._display_mp_results()
    
    def _mp_reset(self):
        """Reset simulation."""
        self._mp_stop()
        self.mp_result = None
        for key in self.mp_metrics:
            self.mp_metrics[key].config(text="--")
        self.mp_log.delete(1.0, tk.END)
        self.mp_ax.clear()
        self.mp_canvas.draw()
    
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
        
        self.mp_log.delete(1.0, tk.END)
        for event in r.schedule:
            self.mp_log.insert(tk.END, f"[{event.time:6.2f}] {event.process_id:>4} | {event.event_type:<10} | {event.details}\n")
        
        self._draw_mp_gantt()
    
    def _draw_mp_gantt(self):
        """Draw multiprogramming Gantt chart."""
        self.mp_ax.clear()
        self.mp_ax.set_facecolor(COLORS['bg_panel'])
        self.mp_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.mp_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not self.mp_result:
            self.mp_canvas.draw()
            return
        
        r = self.mp_result
        events = r.schedule
        if not events:
            self.mp_canvas.draw()
            return
        
        # Build execution intervals from schedule events
        # Merge consecutive same-process intervals (e.g., preempt + immediate re-dispatch)
        intervals = []  # List of (pid, start, end)
        current_proc = None
        start_time = 0
        
        for event in events:
            if event.event_type == "start" or event.event_type.startswith("start"):
                if current_proc is not None:
                    intervals.append((current_proc, start_time, event.time))
                current_proc = event.process_id
                start_time = event.time
            elif event.event_type in ("preempt", "io", "complete"):
                if current_proc is not None:
                    intervals.append((current_proc, start_time, event.time))
                current_proc = None
        
        # Merge consecutive intervals of the same process
        merged = []
        for pid, start, end in intervals:
            if merged and merged[-1][0] == pid and merged[-1][2] == start:
                # Extend the previous interval
                merged[-1] = (pid, merged[-1][1], end)
            else:
                merged.append((pid, start, end))
        
        # Group intervals by process for color assignment
        procs = sorted(set(pid for pid, _, _ in merged))
        colors = ['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa']
        color_map = {p: colors[i % len(colors)] for i, p in enumerate(procs)}
        
        # Draw each interval as a bar, grouped by PID on Y-axis
        # Each process gets exactly one horizontal row
        y_positions = []
        y_labels = []
        y = 0.5
        for pid in procs:
            # Collect all intervals for this process
            proc_intervals = [(s, e) for p, s, e in merged if p == pid]
            for start, end in proc_intervals:
                self.mp_ax.barh(y, end - start, left=start, height=0.6,
                               color=color_map[pid], edgecolor='white', linewidth=0.5)
                if end - start > 0.5:
                    self.mp_ax.text(start + (end - start) / 2, y, pid, ha='center', va='center',
                                   color='white', fontsize=8, fontweight='bold')
            y_positions.append(y)
            y_labels.append(pid)
            y += 1
        
        self.mp_ax.set_ylim(0, len(merged) + 0.5)
        self.mp_ax.set_yticks(y_positions)
        self.mp_ax.set_yticklabels(y_labels, color='white')
        self.mp_ax.set_xlim(0, max(r.total_time, 1))
        self.mp_ax.set_xlabel('Time', color='white')
        self.mp_ax.set_title(f'CPU Timeline - {r.algorithm.replace("_", " ").title()}', color='white')
        
        self.mp_fig.tight_layout()
        self.mp_canvas.draw()
    
    def _load_sample_data(self):
        """Load sample processes."""
        sample = generate_sample_processes()
        
        # Multiprogramming view
        for p in sample:
            self.mp_tree.insert("", tk.END, values=(p.pid, p.arrival_time, p.burst_time, p.io_frequency, p.priority))


def create_process_manager_module(parent_window, content_frame):
    """Factory function to create process manager module."""
    return ProcessManagerWindow(parent_window, content_frame)

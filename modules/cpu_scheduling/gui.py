"""
CPU Scheduling GUI Module for Mini OS Simulator.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from gui.theme import COLORS, FONTS
from modules.cpu_scheduling.algorithms import (
    CPUScheduler, Process, AlgorithmType, SchedulingResult, GanttEntry
)
from simulation.engine import SimulationEngine, PlaybackControls, SimulationEvent, SimulationSnapshot


class CPUSchedulingWindow:
    """CPU Scheduling simulation window."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        self.processes: List[Process] = []
        self.current_result: Optional[SchedulingResult] = None
        self.simulation_engine = SimulationEngine()
        self.simulation_engine.set_tk_root(parent_window)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Input and controls
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        self._create_input_panel(left_frame)
        self._create_control_panel(left_frame)
        self._create_results_panel(left_frame)
        
        # Right panel - Visualization
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        self._create_visualization_panel(right_frame)
        
        # Initialize with sample data
        self._load_sample_data()
    
    def _create_input_panel(self, parent):
        """Create process input panel."""
        input_frame = ttk.LabelFrame(parent, text="Process Configuration", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Process list
        list_frame = ttk.Frame(input_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for processes
        columns = ("PID", "Arrival", "Burst", "Priority")
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=70, anchor=tk.CENTER)
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        # Add/Edit process form
        form_frame = ttk.Frame(input_frame)
        form_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(form_frame, text="PID:").grid(row=0, column=0, padx=2, pady=2)
        self.pid_entry = ttk.Entry(form_frame, width=10)
        self.pid_entry.grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Label(form_frame, text="Arrival:").grid(row=0, column=2, padx=2, pady=2)
        self.arrival_entry = ttk.Entry(form_frame, width=8)
        self.arrival_entry.grid(row=0, column=3, padx=2, pady=2)
        
        ttk.Label(form_frame, text="Burst:").grid(row=0, column=4, padx=2, pady=2)
        self.burst_entry = ttk.Entry(form_frame, width=8)
        self.burst_entry.grid(row=0, column=5, padx=2, pady=2)
        
        ttk.Label(form_frame, text="Priority:").grid(row=0, column=6, padx=2, pady=2)
        self.priority_entry = ttk.Entry(form_frame, width=8)
        self.priority_entry.grid(row=0, column=7, padx=2, pady=2)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=0, column=8, padx=5)
        
        ttk.Button(btn_frame, text="Add", command=self._add_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Update", command=self._update_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_process).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self._clear_processes).pack(side=tk.LEFT, padx=2)
        
        # Bind selection
        self.process_tree.bind("<<TreeviewSelect>>", self._on_process_select)
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(parent, text="Algorithm Selection", padding=10)
        algo_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.algorithm_var = tk.StringVar(value=AlgorithmType.FCFS.value)
        algorithms = [
            (AlgorithmType.FCFS, "FCFS (First Come First Serve)"),
            (AlgorithmType.SJF, "SJF (Shortest Job First)"),
            (AlgorithmType.SRTF, "SRTF (Shortest Remaining Time First)"),
            (AlgorithmType.PRIORITY_NONPREEMPTIVE, "Priority (Non-preemptive)"),
            (AlgorithmType.PRIORITY_PREEMPTIVE, "Priority (Preemptive)"),
            (AlgorithmType.ROUND_ROBIN, "Round Robin"),
        ]
        
        for i, (algo, desc) in enumerate(algorithms):
            rb = ttk.Radiobutton(
                algo_frame,
                text=desc,
                variable=self.algorithm_var,
                value=algo.value,
                command=self._on_algorithm_change
            )
            rb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=10, pady=2)
        
        # Time Quantum for Round Robin
        self.quantum_frame = ttk.Frame(algo_frame)
        self.quantum_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(self.quantum_frame, text="Time Quantum:").pack(side=tk.LEFT, padx=10)
        self.quantum_var = tk.DoubleVar(value=2.0)
        self.quantum_spin = ttk.Spinbox(
            self.quantum_frame, from_=0.1, to=10.0, increment=0.1,
            textvariable=self.quantum_var, width=8
        )
        self.quantum_spin.pack(side=tk.LEFT, padx=5)
        self.quantum_frame.pack_forget()  # Hide initially
        
        # Run button
        ttk.Button(parent, text="Run Simulation", command=self._run_simulation).pack(fill=tk.X, pady=5)
    
    def _create_control_panel(self, parent):
        """Create simulation playback controls."""
        self.control_frame = ttk.LabelFrame(parent, text="Simulation Controls", padding=10)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # The PlaybackControls will be added here after simulation runs
        self.playback_controls = None
    
    def _create_results_panel(self, parent):
        """Create results display panel."""
        results_frame = ttk.LabelFrame(parent, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary metrics
        self.metrics_frame = ttk.Frame(results_frame)
        self.metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.metric_labels = {}
        metrics = [
            ("Avg Turnaround", "avg_turnaround"),
            ("Avg Waiting", "avg_waiting"),
            ("Avg Response", "avg_response"),
            ("CPU Utilization", "cpu_util"),
            ("Throughput", "throughput"),
            ("Context Switches", "context_switches"),
        ]
        
        for i, (label, key) in enumerate(metrics):
            row, col = divmod(i, 3)
            frame = ttk.Frame(self.metrics_frame)
            frame.grid(row=row, column=col, padx=10, pady=5, sticky=tk.W)
            ttk.Label(frame, text=f"{label}:", font=FONTS["small"]).pack(side=tk.LEFT)
            self.metric_labels[key] = ttk.Label(frame, text="--", font=FONTS["small"])
            self.metric_labels[key].pack(side=tk.LEFT, padx=5)
        
        # Process results table
        table_frame = ttk.Frame(results_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        result_columns = ("PID", "Arrival", "Burst", "Completion", "Turnaround", "Waiting", "Response")
        self.result_tree = ttk.Treeview(table_frame, columns=result_columns, show="headings", height=6)
        for col in result_columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80, anchor=tk.CENTER)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        result_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=result_scroll.set)
    
    def _create_visualization_panel(self, parent):
        """Create Gantt chart visualization panel."""
        viz_frame = ttk.LabelFrame(parent, text="Gantt Chart", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        # Matplotlib figure
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor=COLORS['bg_panel'])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS['bg_panel'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Explanation panel
        self.explanation_frame = ttk.LabelFrame(parent, text="Step Explanation", padding=10)
        self.explanation_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.explanation_text = tk.Text(
            self.explanation_frame,
            height=6,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_primary"],
            font=FONTS["mono_small"],
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.explanation_text.pack(fill=tk.BOTH, expand=True)
    
    def _on_algorithm_change(self):
        """Handle algorithm selection change."""
        algo = AlgorithmType(self.algorithm_var.get())
        if algo == AlgorithmType.ROUND_ROBIN:
            self.quantum_frame.pack(fill=tk.X, pady=5)
        else:
            self.quantum_frame.pack_forget()
    
    def _add_process(self):
        """Add a new process."""
        try:
            pid = self.pid_entry.get().strip()
            arrival = float(self.arrival_entry.get())
            burst = float(self.burst_entry.get())
            priority = int(self.priority_entry.get())
            
            if not pid:
                messagebox.showerror("Error", "Process ID is required")
                return
            
            if any(p.pid == pid for p in self.processes):
                messagebox.showerror("Error", f"Process {pid} already exists")
                return
            
            if arrival < 0:
                messagebox.showerror("Error", "Arrival time cannot be negative")
                return
            if burst <= 0:
                messagebox.showerror("Error", "Burst time must be positive")
                return
            if priority < 0:
                messagebox.showerror("Error", "Priority cannot be negative")
                return
            
            process = Process(pid=pid, arrival_time=arrival, burst_time=burst, priority=priority)
            self.processes.append(process)
            self._refresh_process_list()
            self._clear_form()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input values")
    
    def _update_process(self):
        """Update selected process."""
        selection = self.process_tree.selection()
        if not selection:
            return
        
        try:
            pid = self.pid_entry.get().strip()
            arrival = float(self.arrival_entry.get())
            burst = float(self.burst_entry.get())
            priority = int(self.priority_entry.get())
            
            if not pid:
                messagebox.showerror("Error", "Process ID is required")
                return
            
            # Check for duplicate PID (excluding current)
            for p in self.processes:
                if p.pid == pid and p.pid != self.process_tree.item(selection[0])['values'][0]:
                    messagebox.showerror("Error", f"Process {pid} already exists")
                    return
            
            if arrival < 0 or burst <= 0 or priority < 0:
                messagebox.showerror("Error", "Invalid values")
                return
            
            # Update process
            old_pid = self.process_tree.item(selection[0])['values'][0]
            for p in self.processes:
                if p.pid == old_pid:
                    p.pid = pid
                    p.arrival_time = arrival
                    p.burst_time = burst
                    p.priority = priority
                    p.remaining_time = burst
                    break
            
            self._refresh_process_list()
            self._clear_form()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input values")
    
    def _remove_process(self):
        """Remove selected process."""
        selection = self.process_tree.selection()
        if not selection:
            return
        
        pid = self.process_tree.item(selection[0])['values'][0]
        self.processes = [p for p in self.processes if p.pid != pid]
        self._refresh_process_list()
        self._clear_form()
    
    def _clear_processes(self):
        """Clear all processes."""
        self.processes.clear()
        self._refresh_process_list()
        self._clear_form()
    
    def _clear_form(self):
        """Clear input form."""
        self.pid_entry.delete(0, tk.END)
        self.arrival_entry.delete(0, tk.END)
        self.burst_entry.delete(0, tk.END)
        self.priority_entry.delete(0, tk.END)
        self.process_tree.selection_remove(self.process_tree.selection())
    
    def _on_process_select(self, event):
        """Handle process selection."""
        selection = self.process_tree.selection()
        if not selection:
            return
        
        values = self.process_tree.item(selection[0])['values']
        self.pid_entry.delete(0, tk.END)
        self.pid_entry.insert(0, values[0])
        self.arrival_entry.delete(0, tk.END)
        self.arrival_entry.insert(0, values[1])
        self.burst_entry.delete(0, tk.END)
        self.burst_entry.insert(0, values[2])
        self.priority_entry.delete(0, tk.END)
        self.priority_entry.insert(0, values[3])
    
    def _refresh_process_list(self):
        """Refresh the process list display."""
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        for p in sorted(self.processes, key=lambda x: (x.arrival_time, x.pid)):
            self.process_tree.insert("", tk.END, values=(p.pid, p.arrival_time, p.burst_time, p.priority))
    
    def _load_sample_data(self):
        """Load sample process data."""
        sample = [
            Process("P1", 0, 8, 3),
            Process("P2", 1, 4, 1),
            Process("P3", 2, 9, 4),
            Process("P4", 3, 5, 2),
        ]
        self.processes = sample
        self._refresh_process_list()
    
    def _run_simulation(self):
        """Run the selected scheduling algorithm."""
        if not self.processes:
            messagebox.showerror("Error", "No processes defined")
            return
        
        algo = AlgorithmType(self.algorithm_var.get())
        quantum = self.quantum_var.get() if algo == AlgorithmType.ROUND_ROBIN else 2.0
        
        try:
            self.current_result = CPUScheduler.run_algorithm(algo, self.processes, quantum)
            self._display_results()
            self._setup_playback()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def _display_results(self):
        """Display simulation results."""
        if not self.current_result:
            return
        
        r = self.current_result
        
        # Update metrics
        self.metric_labels["avg_turnaround"].config(text=f"{r.avg_turnaround_time:.2f}")
        self.metric_labels["avg_waiting"].config(text=f"{r.avg_waiting_time:.2f}")
        self.metric_labels["avg_response"].config(text=f"{r.avg_response_time:.2f}")
        self.metric_labels["cpu_util"].config(text=f"{r.cpu_utilization:.1f}%")
        self.metric_labels["throughput"].config(text=f"{r.throughput:.2f} proc/unit")
        self.metric_labels["context_switches"].config(text=str(r.context_switches))
        
        # Update process results table
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        for p in r.processes:
            self.result_tree.insert("", tk.END, values=(
                p.pid, p.arrival_time, p.burst_time,
                f"{p.completion_time:.2f}", f"{p.turnaround_time:.2f}",
                f"{p.waiting_time:.2f}", f"{p.response_time:.2f}"
            ))
        
        # Draw Gantt chart
        self._draw_gantt_chart()
    
    def _draw_gantt_chart(self):
        """Draw the Gantt chart."""
        self.ax.clear()
        self.ax.set_facecolor(COLORS['bg_panel'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not self.current_result:
            self.canvas.draw()
            return
        
        gantt = self.current_result.gantt_chart
        if not gantt:
            self.canvas.draw()
            return
        
        # Color map for processes
        pids = list(set(g.pid for g in gantt if not g.is_idle))
        colors = {}
        color_palette = ['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa', '#34d399', '#fb923c']
        for i, pid in enumerate(pids):
            colors[pid] = color_palette[i % len(color_palette)]
        colors["IDLE"] = "#333333"
        
        y_pos = 0.5
        bar_height = 0.6
        
        for entry in gantt:
            color = colors.get(entry.pid, "#888888")
            alpha = 0.5 if entry.is_idle else 1.0
            pattern = '///' if entry.is_idle else None
            
            self.ax.barh(
                y_pos, entry.duration, left=entry.start_time, height=bar_height,
                color=color, alpha=alpha, edgecolor='white', linewidth=0.5,
                hatch=pattern
            )
            
            # Add label
            if entry.duration > 0.5:  # Only label if wide enough
                label = "IDLE" if entry.is_idle else entry.pid
                self.ax.text(
                    entry.start_time + entry.duration / 2, y_pos,
                    label, ha='center', va='center',
                    color='white', fontsize=9, fontweight='bold'
                )
        
        self.ax.set_ylim(0, 1)
        self.ax.set_xlim(0, max(g.end_time for g in gantt) * 1.05)
        self.ax.set_xlabel('Time', color='white')
        self.ax.set_yticks([])
        self.ax.set_title(f'Gantt Chart - {self.current_result.algorithm.value.upper()}', color='white', pad=10)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _setup_playback(self):
        """Setup simulation playback controls."""
        if self.playback_controls:
            self.playback_controls.frame.destroy()
        
        events, snapshots = CPUScheduler.generate_simulation_events(self.current_result)
        self.simulation_engine.load_events(events, snapshots)
        
        def on_event(event):
            self._on_simulation_event(event)
        
        def on_state_change(state):
            self._on_simulation_state_change(state)
        
        def on_complete():
            self._on_simulation_complete()
        
        self.simulation_engine.set_callbacks(on_event, on_state_change, on_complete)
        
        self.playback_controls = PlaybackControls(self.control_frame, self.simulation_engine)
        
        # Initial explanation
        self._set_explanation("Simulation ready. Click Play to start.")
    
    def _on_simulation_event(self, event: SimulationEvent):
        """Handle simulation event during playback."""
        self._set_explanation(event.description)
        
        # Highlight current Gantt entry
        self._highlight_gantt_entry(event.data.get("pid"), event.data.get("start"), event.data.get("end"))
    
    def _on_simulation_state_change(self, state):
        """Handle simulation state change."""
        pass
    
    def _on_simulation_complete(self):
        """Handle simulation completion."""
        self._set_explanation("Simulation complete. All processes finished execution.")
    
    def _highlight_gantt_entry(self, pid: str, start: float, end: float):
        """Highlight a Gantt chart entry during playback."""
        # Redraw with highlight
        self._draw_gantt_chart()
        
        # Add highlight rectangle
        if pid and pid != "IDLE":
            for entry in self.current_result.gantt_chart:
                if entry.pid == pid and abs(entry.start_time - start) < 0.01:
                    self.ax.axvspan(entry.start_time, entry.end_time, alpha=0.3, color='yellow')
                    self.canvas.draw()
                    break
    
    def _set_explanation(self, text: str):
        """Set explanation text."""
        self.explanation_text.config(state=tk.NORMAL)
        self.explanation_text.delete(1.0, tk.END)
        self.explanation_text.insert(tk.END, text)
        self.explanation_text.config(state=tk.DISABLED)


def create_cpu_scheduling_module(parent_window, content_frame):
    """Factory function to create CPU scheduling module."""
    return CPUSchedulingWindow(parent_window, content_frame)
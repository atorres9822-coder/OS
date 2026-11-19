"""
Disk Scheduling GUI Module for Mini OS Simulator.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import COLORS, FONTS
from modules.disk_scheduling.algorithms import (
    DiskScheduler, DiskConfig, DiskAlgorithm, DiskResult,
    generate_sample_disk_config
)


class DiskSchedulingWindow:
    """Disk Scheduling simulation window."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        self.current_result: Optional[DiskResult] = None
        
        self._setup_ui()
        self._load_sample_data()
    
    def _setup_ui(self):
        """Setup the UI components."""
        main_paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Configuration
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_config_panel(left)
        self._create_algorithm_panel(left)
        self._create_results_panel(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_visualization_panel(right)
    
    def _create_config_panel(self, parent):
        """Create disk configuration panel."""
        frame = ttk.LabelFrame(parent, text="Disk Configuration", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Initial head
        ttk.Label(frame, text="Initial Head Position:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.head_var = tk.IntVar(value=50)
        ttk.Spinbox(frame, from_=0, to=1000, textvariable=self.head_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # Cylinder range
        ttk.Label(frame, text="Min Cylinder:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.min_cyl_var = tk.IntVar(value=0)
        ttk.Spinbox(frame, from_=0, to=1000, textvariable=self.min_cyl_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Max Cylinder:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_cyl_var = tk.IntVar(value=199)
        ttk.Spinbox(frame, from_=0, to=10000, textvariable=self.max_cyl_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        # Initial direction
        ttk.Label(frame, text="Initial Direction:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.direction_var = tk.StringVar(value="up")
        ttk.Combobox(frame, textvariable=self.direction_var, values=["up", "down"], width=8, state="readonly").grid(row=3, column=1, padx=5, pady=5)
        
        # Requests
        ttk.Label(frame, text="Request Queue (comma-separated):").grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.requests_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.requests_var, width=40).grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Button(frame, text="Apply Configuration", command=self._apply_config).grid(row=6, column=0, columnspan=2, pady=10)
    
    def _create_algorithm_panel(self, parent):
        """Create algorithm selection panel."""
        frame = ttk.LabelFrame(parent, text="Algorithm Selection", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.algo_var = tk.StringVar(value=DiskAlgorithm.FCFS.value)
        
        for algo in DiskAlgorithm:
            ttk.Radiobutton(frame, text=algo.value.upper(), variable=self.algo_var, 
                           value=algo.value).pack(anchor=tk.W, pady=2)
        
        ttk.Button(frame, text="Run Simulation", command=self._run_simulation).pack(fill=tk.X, pady=10)
        ttk.Button(frame, text="Compare All", command=self._compare_all).pack(fill=tk.X)
    
    def _create_results_panel(self, parent):
        """Create results panel."""
        frame = ttk.LabelFrame(parent, text="Results", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Metrics
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.metrics = {}
        for i, (label, key) in enumerate([
            ("Total Head Movement", "total"), ("Avg Seek Distance", "avg")
        ]):
            row, col = divmod(i, 2)
            f = ttk.Frame(metrics_frame)
            f.grid(row=row, column=col, padx=10, pady=5, sticky=tk.W)
            ttk.Label(f, text=f"{label}:", font=FONTS["small"]).pack(side=tk.LEFT)
            self.metrics[key] = ttk.Label(f, text="--", font=FONTS["small"])
            self.metrics[key].pack(side=tk.LEFT, padx=5)
        
        # Service order table
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Step", "From", "To", "Distance", "Request Served")
        self.result_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80, anchor=tk.CENTER)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=scroll.set)
    
    def _create_visualization_panel(self, parent):
        """Create visualization panel."""
        frame = ttk.LabelFrame(parent, text="Disk Head Movement", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS['bg_panel'])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS['bg_panel'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _apply_config(self):
        """Apply disk configuration."""
        try:
            head = self.head_var.get()
            min_cyl = self.min_cyl_var.get()
            max_cyl = self.max_cyl_var.get()
            direction = self.direction_var.get()
            
            if min_cyl >= max_cyl:
                messagebox.showerror("Error", "Min cylinder must be less than max cylinder")
                return
            
            if not (min_cyl <= head <= max_cyl):
                messagebox.showerror("Error", f"Head position must be between {min_cyl} and {max_cyl}")
                return
            
            req_str = self.requests_var.get().strip()
            if req_str:
                requests = [int(x.strip()) for x in req_str.split(",") if x.strip()]
            else:
                requests = []
            
            for req in requests:
                if not (min_cyl <= req <= max_cyl):
                    messagebox.showerror("Error", f"Request {req} out of range [{min_cyl}, {max_cyl}]")
                    return
            
            self.config = DiskConfig(
                initial_head=head,
                cylinder_range=(min_cyl, max_cyl),
                requests=requests,
                initial_direction=direction
            )
            
            pass  # Configuration applied silently
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def _run_simulation(self):
        """Run the selected algorithm."""
        if not hasattr(self, 'config'):
            messagebox.showerror("Error", "Apply configuration first")
            return
        
        if not self.config.requests:
            messagebox.showerror("Error", "No requests in queue")
            return
        
        algo = DiskAlgorithm(self.algo_var.get())
        
        try:
            self.current_result = DiskScheduler.run_algorithm(algo, self.config)
            self._display_results()
            self._draw_visualization()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _compare_all(self):
        """Compare all algorithms."""
        if not hasattr(self, 'config'):
            messagebox.showerror("Error", "Apply configuration first")
            return
        
        if not self.config.requests:
            messagebox.showerror("Error", "No requests in queue")
            return
        
        results = DiskScheduler.compare_all(self.config)
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Algorithm Comparison")
        dialog.geometry("600x350")
        dialog.configure(bg=COLORS["bg_panel"])
        
        # Table
        columns = ("Algorithm", "Total Movement", "Avg Seek")
        tree = ttk.Treeview(dialog, columns=columns, show="headings", height=8)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for algo, result in results.items():
            tree.insert("", tk.END, values=(
                algo.value.upper(), result.total_head_movement, f"{result.avg_seek_distance:.2f}"
            ))
        
        # Bar chart
        chart_frame = ttk.Frame(dialog)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        fig = Figure(figsize=(6, 3), dpi=100, facecolor=COLORS['bg_panel'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS['bg_panel'])
        ax.tick_params(colors=COLORS['text_secondary'])
        
        algos = [r.algorithm.value.upper() for r in results.values()]
        totals = [r.total_head_movement for r in results.values()]
        
        bars = ax.bar(algos, totals, color=['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa', '#34d399', '#fb923c'])
        ax.set_ylabel('Total Head Movement', color='white')
        ax.set_title('Algorithm Comparison', color='white')
        
        for bar, val in zip(bars, totals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, str(val),
                   ha='center', va='bottom', color='white', fontsize=9)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()
    
    def _display_results(self):
        """Display simulation results."""
        if not self.current_result:
            return
        
        r = self.current_result
        self.metrics["total"].config(text=str(r.total_head_movement))
        self.metrics["avg"].config(text=f"{r.avg_seek_distance:.2f}")
        
        # Update table
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        for i, (from_cyl, to_cyl, dist) in enumerate(r.execution_path):
            request_served = ""
            if i < len(r.service_order):
                request_served = str(r.service_order[i])
            self.result_tree.insert("", tk.END, values=(i+1, from_cyl, to_cyl, dist, request_served))
    
    def _draw_visualization(self):
        """Draw disk head movement visualization."""
        self.ax.clear()
        self.ax.set_facecolor(COLORS['bg_panel'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not self.current_result or not self.config:
            self.canvas.draw()
            return
        
        r = self.current_result
        config = self.config
        
        # Build sequence of (sequence_index, cylinder) points
        # X-axis = movement sequence, Y-axis = cylinder number
        sequence_points = [(0, config.initial_head)]  # Start with initial head
        for i, (from_cyl, to_cyl, dist) in enumerate(r.execution_path):
            sequence_points.append((i + 1, to_cyl))
        
        seq_indices = [p[0] for p in sequence_points]
        cylinders = [p[1] for p in sequence_points]
        
        min_cyl, max_cyl = config.cylinder_range
        
        # Plot the movement path as a line (shows zigzag for direction changes)
        self.ax.plot(seq_indices, cylinders, color=COLORS['accent'], linewidth=2.5,
                     marker='o', markersize=8, markerfacecolor=COLORS['success'],
                     markeredgecolor='white', markeredgewidth=1.5, label='Head Movement Path')
        
        # Mark initial head position
        self.ax.plot(0, config.initial_head, 's', markersize=14,
                     markerfacecolor=COLORS['success'], markeredgecolor='white',
                     markeredgewidth=2, label='Initial Head')
        self.ax.annotate(f'START\n{config.initial_head}', (0, config.initial_head),
                        xytext=(-0.4, config.initial_head + (max_cyl - min_cyl) * 0.08),
                        fontsize=9, fontweight='bold', color=COLORS['success'],
                        ha='right', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS['bg_card'],
                                 edgecolor=COLORS['success'], alpha=0.9))
        
        # Mark each service point with cylinder label
        for i, (seq, cyl) in enumerate(sequence_points[1:], start=1):
            self.ax.plot(seq, cyl, 'o', markersize=10,
                         markerfacecolor=COLORS['danger'], markeredgecolor='white',
                         markeredgewidth=1.5)
            # Label with cylinder number
            self.ax.annotate(str(cyl), (seq, cyl),
                            xytext=(0, 12), textcoords='offset points',
                            fontsize=9, fontweight='bold', color='white',
                            ha='center', va='bottom',
                            bbox=dict(boxstyle='round,pad=0.25', facecolor=COLORS['danger'],
                                     alpha=0.8))
        
        # Mark all request positions as reference on Y-axis
        for req in sorted(set(config.requests)):
            self.ax.axhline(y=req, color=COLORS['border'], linewidth=0.5, alpha=0.3, zorder=0)
        
        # Configure axes
        self.ax.set_xlim(-0.5, len(sequence_points) - 0.5)
        y_margin = (max_cyl - min_cyl) * 0.1
        self.ax.set_ylim(min_cyl - y_margin, max_cyl + y_margin)
        
        # X-axis: sequence steps
        x_labels = ['Start'] + [f'S{i}' for i in range(1, len(sequence_points))]
        self.ax.set_xticks(seq_indices)
        self.ax.set_xticklabels(x_labels, rotation=45, ha='right')
        
        self.ax.set_xlabel('Service Sequence', color='white', fontsize=11)
        self.ax.set_ylabel('Cylinder Number', color='white', fontsize=11)
        self.ax.set_title(f'Disk Head Movement - {r.algorithm.value.upper()}',
                         color='white', fontsize=12, fontweight='bold', pad=15)
        
        # Grid for readability
        self.ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Legend
        self.ax.legend(loc='upper left', facecolor=COLORS['bg_card'],
                      edgecolor=COLORS['border'], labelcolor=COLORS['text_primary'],
                      fontsize=9)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _load_sample_data(self):
        """Load sample data."""
        config = generate_sample_disk_config()
        
        self.head_var.set(config.initial_head)
        self.min_cyl_var.set(config.cylinder_range[0])
        self.max_cyl_var.set(config.cylinder_range[1])
        self.direction_var.set(config.initial_direction)
        self.requests_var.set(",".join(map(str, config.requests)))
        
        self._apply_config()


def create_disk_scheduling_module(parent_window, content_frame):
    """Factory function to create disk scheduling module."""
    return DiskSchedulingWindow(parent_window, content_frame)
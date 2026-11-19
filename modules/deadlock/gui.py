"""
Deadlock Manager GUI Module for Mini OS Simulator.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import COLORS, FONTS
from modules.deadlock.algorithms import (
    BankersAlgorithm, BankerState, SafetyResult, RequestResult, generate_sample_state
)


class DeadlockWindow:
    """Deadlock Manager simulation window."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        self.state: Optional[BankerState] = None
        self.last_safety_result: Optional[SafetyResult] = None
        
        self._setup_ui()
        self._load_sample_state()
    
    def _setup_ui(self):
        """Setup the UI components."""
        main_paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Configuration
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        self._create_config_panel(left_frame)
        self._create_matrices_panel(left_frame)
        self._create_request_panel(left_frame)
        
        # Right panel - Results and explanation
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        self._create_results_panel(right_frame)
    
    def _create_config_panel(self, parent):
        """Create configuration panel."""
        config_frame = ttk.LabelFrame(parent, text="System Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Number of processes and resources
        ttk.Label(config_frame, text="Processes:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.num_processes_var = tk.IntVar(value=5)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_processes_var, width=5,
                    command=self._on_dimension_change).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Resources:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.num_resources_var = tk.IntVar(value=3)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.num_resources_var, width=5,
                    command=self._on_dimension_change).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Apply Dimensions", command=self._apply_dimensions).grid(
            row=0, column=4, padx=10, pady=5)
        
        ttk.Button(config_frame, text="Load Sample", command=self._load_sample_state).grid(
            row=0, column=5, padx=5, pady=5)
        
        # Available resources
        avail_frame = ttk.LabelFrame(config_frame, text="Available Resources", padding=5)
        avail_frame.grid(row=1, column=0, columnspan=6, sticky=tk.EW, pady=10)
        
        self.available_entries = []
        self.available_labels = []

    def _create_matrices_panel(self, parent):
        """Create matrices display/edit panel."""
        self.matrices_frame = ttk.LabelFrame(parent, text="Resource Matrices", padding=8)
        self.matrices_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.alloc_entries = []
        self.max_entries = []
        self.need_labels = []
        
        self._create_matrix_grids()
    
    def _create_matrix_grids(self):
        """Create matrix input grids - process-oriented compact layout."""
        # Clear existing matrices_frame and rebuild
        for widget in self.matrices_frame.winfo_children():
            widget.destroy()
        
        self.matrix_container = ttk.Frame(self.matrices_frame)
        self.matrix_container.pack(fill=tk.BOTH, expand=True)
        
        self.alloc_entries = []
        self.max_entries = []
        self.need_labels = []
        
        n_proc = self.num_processes_var.get()
        n_res = self.num_resources_var.get()
        
        if not self.state:
            return
        
        # Compact process-oriented layout: each process gets a row group
        # with Allocation, Maximum, Need shown side by side
        header_frame = ttk.Frame(self.matrix_container)
        header_frame.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(header_frame, text="Process", font=FONTS["heading"], width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Allocation", font=FONTS["heading"]).pack(side=tk.LEFT, padx=10)
        ttk.Label(header_frame, text="Maximum", font=FONTS["heading"]).pack(side=tk.LEFT, padx=10)
        ttk.Label(header_frame, text="Need (auto)", font=FONTS["heading"]).pack(side=tk.LEFT, padx=10)
        
        # Resource column headers (small, above each matrix block)
        res_header_frame = ttk.Frame(self.matrix_container)
        res_header_frame.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(res_header_frame, text="", width=10).pack(side=tk.LEFT)
        for j in range(n_res):
            ttk.Label(res_header_frame, text=f"R{j}", font=FONTS["small"], width=6).pack(side=tk.LEFT, padx=1)
        ttk.Label(res_header_frame, text="", width=6).pack(side=tk.LEFT, padx=1)
        for j in range(n_res):
            ttk.Label(res_header_frame, text=f"R{j}", font=FONTS["small"], width=6).pack(side=tk.LEFT, padx=1)
        ttk.Label(res_header_frame, text="", width=6).pack(side=tk.LEFT, padx=1)
        for j in range(n_res):
            ttk.Label(res_header_frame, text=f"R{j}", font=FONTS["small"], width=6).pack(side=tk.LEFT, padx=1)
        
        # Process rows
        for i in range(n_proc):
            proc_frame = ttk.Frame(self.matrix_container)
            proc_frame.pack(fill=tk.X, pady=1)
            
            # Process label
            ttk.Label(proc_frame, text=f"P{i}", font=FONTS["body"], width=10).pack(side=tk.LEFT, padx=2)
            
            # Allocation row (editable)
            alloc_row = ttk.Frame(proc_frame)
            alloc_row.pack(side=tk.LEFT, padx=4)
            row_alloc = []
            for j in range(n_res):
                entry = ttk.Entry(alloc_row, width=5, justify=tk.CENTER)
                entry.pack(side=tk.LEFT, padx=1)
                entry.insert(0, str(self.state.allocation[i][j]))
                entry.bind("<FocusOut>", lambda e, pi=i, pj=j: self._on_matrix_change(pi, pj, "alloc"))
                row_alloc.append(entry)
            self.alloc_entries.append(row_alloc)
            
            # Maximum row (editable)
            max_row = ttk.Frame(proc_frame)
            max_row.pack(side=tk.LEFT, padx=4)
            row_max = []
            for j in range(n_res):
                entry = ttk.Entry(max_row, width=5, justify=tk.CENTER)
                entry.pack(side=tk.LEFT, padx=1)
                entry.insert(0, str(self.state.maximum[i][j]))
                entry.bind("<FocusOut>", lambda e, pi=i, pj=j: self._on_matrix_change(pi, pj, "max"))
                row_max.append(entry)
            self.max_entries.append(row_max)
            
            # Need row (read-only, auto-calculated)
            need_row = ttk.Frame(proc_frame)
            need_row.pack(side=tk.LEFT, padx=4)
            row_need = []
            for j in range(n_res):
                need_val = self.state.maximum[i][j] - self.state.allocation[i][j]
                lbl = ttk.Label(need_row, text=str(need_val), width=6, anchor=tk.CENTER,
                               background=COLORS["bg_card"], foreground=COLORS["text_secondary"],
                               relief="solid", borderwidth=1)
                lbl.pack(side=tk.LEFT, padx=1)
                self.state.need[i][j] = need_val
                row_need.append(lbl)
            self.need_labels.append(row_need)
    
    def _on_matrix_change(self, process_idx: int, resource_idx: int, field: str):
        """Handle matrix value change."""
        try:
            if field == "alloc":
                val = int(self.alloc_entries[process_idx][resource_idx].get())
                if val < 0:
                    raise ValueError
                self.state.allocation[process_idx][resource_idx] = val
            elif field == "max":
                val = int(self.max_entries[process_idx][resource_idx].get())
                if val < 0:
                    raise ValueError
                self.state.maximum[process_idx][resource_idx] = val
            
            # Validate allocation <= maximum
            if self.state.allocation[process_idx][resource_idx] > self.state.maximum[process_idx][resource_idx]:
                messagebox.showerror("Error", f"Allocation cannot exceed Maximum for P{process_idx} R{resource_idx}")
                # Revert
                if field == "alloc":
                    self.state.allocation[process_idx][resource_idx] = self.state.maximum[process_idx][resource_idx]
                    self.alloc_entries[process_idx][resource_idx].delete(0, tk.END)
                    self.alloc_entries[process_idx][resource_idx].insert(0, str(self.state.allocation[process_idx][resource_idx]))
                else:
                    self.state.maximum[process_idx][resource_idx] = self.state.allocation[process_idx][resource_idx]
                    self.max_entries[process_idx][resource_idx].delete(0, tk.END)
                    self.max_entries[process_idx][resource_idx].insert(0, str(self.state.maximum[process_idx][resource_idx]))
            
            self._update_need_matrix()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid non-negative integers")
            self._refresh_matrix_values()
    
    def _update_need_matrix(self):
        """Update the need matrix display."""
        if not self.state:
            return
        
        for i in range(self.state.num_processes):
            for j in range(self.state.num_resources):
                need_val = self.state.maximum[i][j] - self.state.allocation[i][j]
                self.state.need[i][j] = need_val
                self.need_labels[i][j].config(text=str(need_val))
    
    def _refresh_matrix_values(self):
        """Refresh matrix entry values from state."""
        if not self.state:
            return
        
        for i in range(self.state.num_processes):
            for j in range(self.state.num_resources):
                self.alloc_entries[i][j].delete(0, tk.END)
                self.alloc_entries[i][j].insert(0, str(self.state.allocation[i][j]))
                self.max_entries[i][j].delete(0, tk.END)
                self.max_entries[i][j].insert(0, str(self.state.maximum[i][j]))
    
    def _on_matrix_change(self, process_idx: int, resource_idx: int, frame):
        """Handle matrix value change."""
        try:
            if frame == self.alloc_frame:
                val = int(self.alloc_entries[process_idx][resource_idx].get())
                if val < 0:
                    raise ValueError
                self.state.allocation[process_idx][resource_idx] = val
            else:
                val = int(self.max_entries[process_idx][resource_idx].get())
                if val < 0:
                    raise ValueError
                self.state.maximum[process_idx][resource_idx] = val
            
            # Validate allocation <= maximum
            if self.state.allocation[process_idx][resource_idx] > self.state.maximum[process_idx][resource_idx]:
                messagebox.showerror("Error", "Allocation cannot exceed Maximum")
                # Revert
                if frame == self.alloc_frame:
                    self.state.allocation[process_idx][resource_idx] = self.state.maximum[process_idx][resource_idx]
                else:
                    self.state.maximum[process_idx][resource_idx] = self.state.allocation[process_idx][resource_idx]
                self._refresh_matrix_values()
            
            self._update_need_matrix()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid non-negative integers")
            self._refresh_matrix_values()
    
    def _update_need_matrix(self):
        """Update the need matrix display."""
        if not self.state:
            return
        
        for i in range(self.state.num_processes):
            for j in range(self.state.num_resources):
                need_val = self.state.maximum[i][j] - self.state.allocation[i][j]
                self.state.need[i][j] = need_val
                self.need_labels[i][j].config(text=str(need_val))
    
    def _refresh_matrix_values(self):
        """Refresh matrix entry values from state."""
        if not self.state:
            return
        
        for i in range(self.state.num_processes):
            for j in range(self.state.num_resources):
                self.alloc_entries[i][j].delete(0, tk.END)
                self.alloc_entries[i][j].insert(0, str(self.state.allocation[i][j]))
                self.max_entries[i][j].delete(0, tk.END)
                self.max_entries[i][j].insert(0, str(self.state.maximum[i][j]))
    
    def _create_request_panel(self, parent):
        """Create resource request panel."""
        req_frame = ttk.LabelFrame(parent, text="Resource Request", padding=10)
        req_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(req_frame, text="Process:").grid(row=0, column=0, padx=5, pady=5)
        self.request_process_var = tk.IntVar(value=0)
        self.request_process_spin = ttk.Spinbox(req_frame, from_=0, to=9, textvariable=self.request_process_var, width=5)
        self.request_process_spin.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(req_frame, text="Request:").grid(row=0, column=2, padx=5, pady=5)
        self.request_entries = []
        
        self.request_frame = ttk.Frame(req_frame)
        self.request_frame.grid(row=0, column=3, columnspan=5, padx=5, pady=5)
        
        ttk.Button(req_frame, text="Submit Request", command=self._submit_request).grid(
            row=0, column=8, padx=10, pady=5)
        
        self._update_request_entries()
    
    def _update_request_entries(self):
        """Update request entry fields based on resource count."""
        for widget in self.request_frame.winfo_children():
            widget.destroy()
        
        self.request_entries = []
        n_res = self.num_resources_var.get()
        
        for j in range(n_res):
            ttk.Label(self.request_frame, text=f"R{j}:").pack(side=tk.LEFT, padx=2)
            entry = ttk.Entry(self.request_frame, width=5, justify=tk.CENTER)
            entry.pack(side=tk.LEFT, padx=2)
            entry.insert(0, "0")
            self.request_entries.append(entry)
    
    def _create_results_panel(self, parent):
        """Create results and explanation panel."""
        # Safety check button
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Check Safety", command=self._check_safety).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        
        # Results display
        result_frame = ttk.LabelFrame(parent, text="Safety Analysis", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(
            result_frame,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_primary"],
            font=FONTS["mono_small"],
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # Visualization
        viz_frame = ttk.LabelFrame(parent, text="Resource Allocation Visualization", padding=10)
        viz_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.fig = Figure(figsize=(6, 3), dpi=100, facecolor=COLORS['bg_panel'])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS['bg_panel'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self._draw_visualization()
    
    def _on_dimension_change(self):
        """Handle dimension spinbox change."""
        # Just update the request entries
        self._update_request_entries()
    
    def _apply_dimensions(self):
        """Apply new dimensions and create empty state."""
        n_proc = self.num_processes_var.get()
        n_res = self.num_resources_var.get()
        
        # Create empty state
        available = [0] * n_res
        maximum = [[0] * n_res for _ in range(n_proc)]
        allocation = [[0] * n_res for _ in range(n_proc)]
        
        self.state = BankersAlgorithm.create_state(n_proc, n_res, available, maximum, allocation)
        
        # Update available entries
        self._update_available_entries()
        self._create_matrix_grids()
        self._update_request_entries()
        self._draw_visualization()
    
    def _update_available_entries(self):
        """Update available resource entry fields."""
        # Clear existing
        for widget in self.content_frame.winfo_children():
            pass  # We'll recreate in config panel
        
        # Find the available frame
        for child in self.content_frame.winfo_children():
            if isinstance(child, ttk.PanedWindow):
                for pane in child.winfo_children():
                    for widget in pane.winfo_children():
                        if isinstance(widget, ttk.LabelFrame) and "Configuration" in str(widget.cget("text")):
                            for c in widget.winfo_children():
                                if isinstance(c, ttk.LabelFrame) and "Available" in str(c.cget("text")):
                                    for w in c.winfo_children():
                                        w.destroy()
                                    
                                    n_res = self.num_resources_var.get()
                                    self.available_entries = []
                                    self.available_labels = []
                                    
                                    for j in range(n_res):
                                        ttk.Label(c, text=f"R{j}:").grid(row=0, column=j*2, padx=2, pady=5)
                                        entry = ttk.Entry(c, width=6, justify=tk.CENTER)
                                        entry.grid(row=0, column=j*2+1, padx=2, pady=5)
                                        entry.insert(0, "0")
                                        entry.bind("<FocusOut>", lambda e, idx=j: self._on_available_change(idx))
                                        self.available_entries.append(entry)
    
    def _on_available_change(self, resource_idx: int):
        """Handle available resource change."""
        try:
            val = int(self.available_entries[resource_idx].get())
            if val < 0:
                raise ValueError
            self.state.available[resource_idx] = val
            self._draw_visualization()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid non-negative integers")
            self.available_entries[resource_idx].delete(0, tk.END)
            self.available_entries[resource_idx].insert(0, str(self.state.available[resource_idx]))
    
    def _load_sample_state(self):
        """Load the classic textbook sample state."""
        self.state = generate_sample_state()
        self.num_processes_var.set(self.state.num_processes)
        self.num_resources_var.set(self.state.num_resources)
        
        self._update_available_entries()
        self._create_matrix_grids()
        self._update_request_entries()
        
        # Fill available entries
        for j, val in enumerate(self.state.available):
            if j < len(self.available_entries):
                self.available_entries[j].delete(0, tk.END)
                self.available_entries[j].insert(0, str(val))
        
        self._draw_visualization()
    
    def _check_safety(self):
        """Run the safety algorithm."""
        if not self.state:
            messagebox.showerror("Error", "No state configured")
            return
        
        # Validate
        errors = BankersAlgorithm.validate_state(self.state)
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        result = BankersAlgorithm.safety_algorithm(self.state)
        self.last_safety_result = result
        
        self._display_result(result)
        self._draw_visualization(result)
    
    def _submit_request(self):
        """Submit a resource request."""
        if not self.state:
            messagebox.showerror("Error", "No state configured")
            return
        
        # Validate current state first
        errors = BankersAlgorithm.validate_state(self.state)
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        process_id = self.request_process_var.get()
        if process_id >= self.state.num_processes:
            messagebox.showerror("Error", f"Invalid process ID. Must be 0-{self.state.num_processes-1}")
            return
        
        request = []
        for entry in self.request_entries:
            try:
                val = int(entry.get())
                if val < 0:
                    raise ValueError
                request.append(val)
            except ValueError:
                messagebox.showerror("Error", "Please enter valid non-negative integers for request")
                return
        
        result = BankersAlgorithm.request_algorithm(self.state, process_id, request)
        self._display_result(result)
        
        if result.granted and result.new_state:
            # Apply the new state
            self.state = result.new_state
            self._refresh_matrix_values()
            self._update_need_matrix()
            self._update_available_entries()
            for j, val in enumerate(self.state.available):
                if j < len(self.available_entries):
                    self.available_entries[j].delete(0, tk.END)
                    self.available_entries[j].insert(0, str(val))
            self._draw_visualization()
    
    def _display_result(self, result):
        """Display result in text area."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        if isinstance(result, SafetyResult):
            for line in result.explanation:
                if "SAFE" in line and "UNSAFE" not in line:
                    self.result_text.insert(tk.END, line + "\n", "safe")
                elif "UNSAFE" in line:
                    self.result_text.insert(tk.END, line + "\n", "unsafe")
                elif "GRANTED" in line:
                    self.result_text.insert(tk.END, line + "\n", "granted")
                elif "DENIED" in line:
                    self.result_text.insert(tk.END, line + "\n", "denied")
                else:
                    self.result_text.insert(tk.END, line + "\n")
        elif isinstance(result, RequestResult):
            for line in result.explanation:
                if "GRANTED" in line:
                    self.result_text.insert(tk.END, line + "\n", "granted")
                elif "DENIED" in line:
                    self.result_text.insert(tk.END, line + "\n", "denied")
                elif "ERROR" in line or "Error" in line:
                    self.result_text.insert(tk.END, line + "\n", "error")
                else:
                    self.result_text.insert(tk.END, line + "\n")
        
        # Configure tags
        self.result_text.tag_config("safe", foreground="#00ff00")
        self.result_text.tag_config("unsafe", foreground="#ff4444")
        self.result_text.tag_config("granted", foreground="#00ff00", font=("Consolas", 9, "bold"))
        self.result_text.tag_config("denied", foreground="#ff4444", font=("Consolas", 9, "bold"))
        self.result_text.tag_config("error", foreground="#ffaa00")
        
        self.result_text.config(state=tk.DISABLED)
        self.result_text.see(tk.END)
    
    def _clear_log(self):
        """Clear the result log."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
    
    def _draw_visualization(self, safety_result: SafetyResult = None):
        """Draw resource allocation visualization."""
        self.ax.clear()
        self.ax.set_facecolor(COLORS['bg_panel'])
        self.ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not self.state:
            self.canvas.draw()
            return
        
        n_proc = self.state.num_processes
        n_res = self.state.num_resources
        
        # Create stacked bar chart showing allocation per process
        processes = [f"P{i}" for i in range(n_proc)]
        bottom = [0] * n_proc
        colors = ['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa', '#34d399', '#fb923c']
        
        for j in range(n_res):
            allocations = [self.state.allocation[i][j] for i in range(n_proc)]
            self.ax.bar(processes, allocations, bottom=bottom, label=f'R{j}', 
                       color=colors[j % len(colors)], edgecolor='white', linewidth=0.5)
            bottom = [bottom[i] + allocations[i] for i in range(n_proc)]
        
        # Add maximum as outline
        for i in range(n_proc):
            total_max = sum(self.state.maximum[i])
            if total_max > 0:
                self.ax.bar(i, total_max, bottom=0, fill=False, edgecolor='yellow', 
                           linewidth=2, linestyle='--', hatch='//', alpha=0)
        
        self.ax.set_ylabel('Resource Instances', color='white')
        self.ax.set_title('Resource Allocation per Process\n(Dashed outline = Maximum claim)', color='white')
        self.ax.legend(loc='upper right', facecolor=COLORS['bg_card'], edgecolor=COLORS['border'], labelcolor=COLORS['text_primary'])
        
        # Add available as text
        avail_text = "Available: " + ", ".join(f"R{j}={self.state.available[j]}" for j in range(n_res))
        self.ax.text(0.02, 0.98, avail_text, transform=self.ax.transAxes, 
                    color='white', fontsize=9, va='top', ha='left',
                    bbox=dict(boxstyle='round', facecolor=COLORS['bg_card'], edgecolor=COLORS['border']))
        
        # If safety result, highlight safe sequence
        if safety_result and safety_result.is_safe:
            seq_text = "Safe Sequence: " + " -> ".join(f"P{i}" for i in safety_result.safe_sequence)
            self.ax.text(0.98, 0.02, seq_text, transform=self.ax.transAxes,
                        color='#00ff00', fontsize=9, va='bottom', ha='right',
                        bbox=dict(boxstyle='round', facecolor=COLORS['bg_card'], edgecolor='#00ff00'))
        elif safety_result and not safety_result.is_safe:
            self.ax.text(0.98, 0.02, "UNSAFE STATE", transform=self.ax.transAxes,
                        color='#ff4444', fontsize=12, fontweight='bold', va='bottom', ha='right',
                        bbox=dict(boxstyle='round', facecolor=COLORS['bg_card'], edgecolor=COLORS['danger']))
        
        self.fig.tight_layout()
        self.canvas.draw()


def create_deadlock_module(parent_window, content_frame):
    """Factory function to create deadlock manager module."""
    return DeadlockWindow(parent_window, content_frame)
"""
Memory Manager GUI Module for Mini OS Simulator.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import COLORS, FONTS
from modules.memory.algorithms import (
    PagingConfig, PageTableEntry, PagingSimulator,
    PageReplacementAlgorithm, PageReplacementSimulator, ReplacementResult,
    Segment, SegmentationSimulator,
    AllocationAlgorithm, MemoryBlock, FragmentationSimulator, FragmentationResult,
    generate_sample_paging_config, generate_sample_page_references,
    generate_sample_segments, generate_sample_memory_blocks, generate_sample_process_requests
)


class MemoryWindow:
    """Memory Manager simulation window with tabs for different modules."""
    
    def __init__(self, parent_window, content_frame):
        self.parent = parent_window
        self.content_frame = content_frame
        
        self._setup_ui()
        self._load_sample_data()
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Notebook for different memory modules
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Paging
        self.paging_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.paging_frame, text="Paging")
        self._create_paging_tab()
        
        # Tab 2: Page Replacement
        self.replacement_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.replacement_frame, text="Page Replacement")
        self._create_replacement_tab()
        
        # Tab 3: Segmentation
        self.segmentation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.segmentation_frame, text="Segmentation")
        self._create_segmentation_tab()
        
        # Tab 4: Fragmentation
        self.fragmentation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fragmentation_frame, text="Fragmentation")
        self._create_fragmentation_tab()
    
    # ==================== PAGING TAB ====================
    
    def _create_paging_tab(self):
        """Create paging simulation tab."""
        main_paned = ttk.PanedWindow(self.paging_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Configuration
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_paging_config(left)
        self._create_paging_page_table(left)
        self._create_paging_translation(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_paging_visualization(right)
    
    def _create_paging_config(self, parent):
        """Create paging configuration panel."""
        frame = ttk.LabelFrame(parent, text="Memory Configuration", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Logical Memory (KB):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.logical_mem_var = tk.IntVar(value=64)
        ttk.Spinbox(frame, from_=4, to=1024, textvariable=self.logical_mem_var, width=8).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Physical Memory (KB):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.physical_mem_var = tk.IntVar(value=32)
        ttk.Spinbox(frame, from_=4, to=1024, textvariable=self.physical_mem_var, width=8).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Page Size (KB):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.page_size_var = tk.IntVar(value=4)
        ttk.Spinbox(frame, from_=1, to=64, textvariable=self.page_size_var, width=8).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Button(frame, text="Apply", command=self._apply_paging_config).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Derived values
        self.derived_frame = ttk.LabelFrame(frame, text="Derived Values", padding=5)
        self.derived_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.pages_label = ttk.Label(self.derived_frame, text="Pages: --")
        self.pages_label.pack(anchor=tk.W)
        self.frames_label = ttk.Label(self.derived_frame, text="Frames: --")
        self.frames_label.pack(anchor=tk.W)
    
    def _create_paging_page_table(self, parent):
        """Create page table editor."""
        frame = ttk.LabelFrame(parent, text="Page Table", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Page table as treeview
        columns = ("Page", "Frame", "Valid")
        self.page_table_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.page_table_tree.heading(col, text=col)
            self.page_table_tree.column(col, width=80, anchor=tk.CENTER)
        self.page_table_tree.pack(fill=tk.BOTH, expand=True)
        
        # Edit controls
        edit_frame = ttk.Frame(frame)
        edit_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(edit_frame, text="Page:").pack(side=tk.LEFT, padx=2)
        self.pt_page_var = tk.IntVar()
        ttk.Spinbox(edit_frame, from_=0, to=15, textvariable=self.pt_page_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(edit_frame, text="Frame:").pack(side=tk.LEFT, padx=2)
        self.pt_frame_var = tk.IntVar()
        ttk.Spinbox(edit_frame, from_=-1, to=15, textvariable=self.pt_frame_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(edit_frame, text="Valid:").pack(side=tk.LEFT, padx=2)
        self.pt_valid_var = tk.BooleanVar()
        ttk.Checkbutton(edit_frame, variable=self.pt_valid_var).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(edit_frame, text="Update", command=self._update_page_table_entry).pack(side=tk.LEFT, padx=10)
        ttk.Button(edit_frame, text="Auto-Assign", command=self._auto_assign_frames).pack(side=tk.LEFT, padx=5)
    
    def _create_paging_translation(self, parent):
        """Create address translation panel."""
        frame = ttk.LabelFrame(parent, text="Address Translation", padding=10)
        frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(frame, text="Logical Address:").pack(anchor=tk.W)
        addr_frame = ttk.Frame(frame)
        addr_frame.pack(fill=tk.X, pady=5)
        
        self.logical_addr_var = tk.IntVar(value=0)
        ttk.Entry(addr_frame, textvariable=self.logical_addr_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(addr_frame, text="Translate", command=self._translate_address).pack(side=tk.LEFT, padx=5)
        
        self.translation_result = tk.Text(frame, height=6, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono_small"])
        self.translation_result.pack(fill=tk.BOTH, expand=True)
    
    def _create_paging_visualization(self, parent):
        """Create paging visualization."""
        frame = ttk.LabelFrame(parent, text="Memory Map", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.paging_fig = Figure(figsize=(6, 5), dpi=100, facecolor=COLORS['bg_panel'])
        self.paging_ax = self.paging_fig.add_subplot(111)
        self.paging_ax.set_facecolor(COLORS['bg_panel'])
        self.paging_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.paging_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.paging_canvas = FigureCanvasTkAgg(self.paging_fig, master=frame)
        self.paging_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _apply_paging_config(self):
        """Apply paging configuration."""
        try:
            logical = self.logical_mem_var.get() * 1024
            physical = self.physical_mem_var.get() * 1024
            page = self.page_size_var.get() * 1024
            
            if logical % page != 0 or physical % page != 0:
                messagebox.showerror("Error", "Memory sizes must be multiples of page size")
                return
            
            self.paging_config = PagingConfig(logical, physical, page)
            self.page_table = [PageTableEntry() for _ in range(self.paging_config.num_pages)]
            
            self.pages_label.config(text=f"Pages: {self.paging_config.num_pages}")
            self.frames_label.config(text=f"Frames: {self.paging_config.num_frames}")
            
            self._refresh_page_table()
            self._draw_paging_visualization()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _refresh_page_table(self):
        """Refresh page table display."""
        for item in self.page_table_tree.get_children():
            self.page_table_tree.delete(item)
        
        for i, entry in enumerate(self.page_table):
            self.page_table_tree.insert("", tk.END, values=(
                i, entry.frame_number if entry.valid else "-", "✓" if entry.valid else "✗"
            ))
        
        # Update spinbox ranges
        self.pt_page_var.set(0)
        self.pt_frame_var.set(-1)
        self.pt_valid_var.set(False)
    
    def _update_page_table_entry(self):
        """Update a page table entry."""
        if not hasattr(self, 'paging_config'):
            return
        
        page = self.pt_page_var.get()
        frame = self.pt_frame_var.get()
        valid = self.pt_valid_var.get()
        
        if page >= self.paging_config.num_pages:
            messagebox.showerror("Error", f"Page number must be < {self.paging_config.num_pages}")
            return
        
        if valid and (frame < 0 or frame >= self.paging_config.num_frames):
            messagebox.showerror("Error", f"Frame number must be 0-{self.paging_config.num_frames-1}")
            return
        
        # Check for duplicate frame assignment
        if valid:
            for i, entry in enumerate(self.page_table):
                if i != page and entry.valid and entry.frame_number == frame:
                    messagebox.showerror("Error", f"Frame {frame} already assigned to page {i}")
                    return
        
        self.page_table[page] = PageTableEntry(frame_number=frame if valid else -1, valid=valid)
        self._refresh_page_table()
        self._draw_paging_visualization()
    
    def _auto_assign_frames(self):
        """Auto-assign frames to pages."""
        if not hasattr(self, 'paging_config'):
            return
        
        available_frames = list(range(self.paging_config.num_frames))
        num_to_assign = min(len(available_frames), self.paging_config.num_pages)
        
        for i in range(num_to_assign):
            if available_frames:
                frame = available_frames.pop(0)
                self.page_table[i] = PageTableEntry(frame_number=frame, valid=True)
            else:
                self.page_table[i] = PageTableEntry()
        
        self._refresh_page_table()
        self._draw_paging_visualization()
    
    def _translate_address(self):
        """Translate logical address."""
        if not hasattr(self, 'paging_config'):
            messagebox.showerror("Error", "Apply configuration first")
            return
        
        addr = self.logical_addr_var.get()
        phys, valid, explanation = PagingSimulator.translate_address(
            self.paging_config, addr, self.page_table
        )
        
        self.translation_result.delete(1.0, tk.END)
        self.translation_result.insert(tk.END, explanation)
        if not valid:
            self.translation_result.tag_add("error", "1.0", "end")
            self.translation_result.tag_config("error", foreground="#ff4444")
    
    def _draw_paging_visualization(self):
        """Draw paging memory map."""
        self.paging_ax.clear()
        self.paging_ax.set_facecolor(COLORS['bg_panel'])
        self.paging_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.paging_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not hasattr(self, 'paging_config'):
            self.paging_canvas.draw()
            return
        
        config = self.paging_config
        
        # Draw logical pages
        page_height = 0.8
        for i in range(config.num_pages):
            y = i * 1.0
            color = COLORS['accent'] if (i < len(self.page_table) and self.page_table[i].valid) else COLORS['bg_input']
            self.paging_ax.barh(y, 1, height=page_height, left=0, color=color, edgecolor='white', linewidth=0.5)
            label = f"P{i}"
            if i < len(self.page_table) and self.page_table[i].valid:
                label += f" → F{self.page_table[i].frame_number}"
            self.paging_ax.text(0.5, y + 0.05, label, ha='center', va='center', color='white', fontsize=8)
        
        self.paging_ax.set_xlim(0, 1.2)
        self.paging_ax.set_ylim(-0.5, config.num_pages * 1.0 - 0.5)
        self.paging_ax.set_title('Logical Pages → Physical Frames', color='white')
        self.paging_ax.set_yticks([])
        self.paging_ax.set_xticks([])
        
        # Draw physical frames on right
        frame_x = 1.2
        for i in range(config.num_frames):
            y = i * 1.0
            # Check if frame is used
            used_by = -1
            for p, entry in enumerate(self.page_table):
                if entry.valid and entry.frame_number == i:
                    used_by = p
                    break
            
            color = COLORS['success'] if used_by >= 0 else COLORS['bg_input']
            self.paging_ax.barh(y, 1, height=page_height, left=frame_x, color=color, edgecolor='white', linewidth=0.5)
            label = f"F{i}"
            if used_by >= 0:
                label += f" ← P{used_by}"
            self.paging_ax.text(frame_x + 0.5, y + 0.05, label, ha='center', va='center', color='white', fontsize=8)
        
        self.paging_ax.set_xlim(0, 2.5)
        self.paging_fig.tight_layout()
        self.paging_canvas.draw()
    
    # ==================== PAGE REPLACEMENT TAB ====================
    
    def _create_replacement_tab(self):
        """Create page replacement tab."""
        main_paned = ttk.PanedWindow(self.replacement_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Configuration
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_replacement_config(left)
        self._create_replacement_results(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_replacement_visualization(right)
    
    def _create_replacement_config(self, parent):
        """Create replacement configuration."""
        frame = ttk.LabelFrame(parent, text="Configuration", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Reference String:").pack(anchor=tk.W)
        self.ref_string_var = tk.StringVar(value="7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1")
        ttk.Entry(frame, textvariable=self.ref_string_var, width=40).pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Number of Frames:").pack(anchor=tk.W)
        self.num_frames_var = tk.IntVar(value=3)
        ttk.Spinbox(frame, from_=1, to=10, textvariable=self.num_frames_var, width=8).pack(anchor=tk.W, pady=5)
        
        ttk.Label(frame, text="Algorithm:").pack(anchor=tk.W)
        self.replace_algo_var = tk.StringVar(value=PageReplacementAlgorithm.FIFO.value)
        for algo in PageReplacementAlgorithm:
            ttk.Radiobutton(frame, text=algo.value.upper(), variable=self.replace_algo_var, 
                           value=algo.value).pack(anchor=tk.W)
        
        ttk.Button(frame, text="Run Simulation", command=self._run_replacement).pack(fill=tk.X, pady=10)
        ttk.Button(frame, text="Compare All", command=self._compare_all_replacement).pack(fill=tk.X)
    
    def _create_replacement_results(self, parent):
        """Create replacement results panel."""
        frame = ttk.LabelFrame(parent, text="Results", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Metrics
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.replace_metrics = {}
        for i, (label, key) in enumerate([
            ("Page Faults", "faults"), ("Page Hits", "hits"),
            ("Fault Rate", "fault_rate"), ("Hit Rate", "hit_rate")
        ]):
            row, col = divmod(i, 2)
            f = ttk.Frame(metrics_frame)
            f.grid(row=row, column=col, padx=10, pady=5, sticky=tk.W)
            ttk.Label(f, text=f"{label}:", font=FONTS["small"]).pack(side=tk.LEFT)
            self.replace_metrics[key] = ttk.Label(f, text="--", font=FONTS["small"])
            self.replace_metrics[key].pack(side=tk.LEFT, padx=5)
        
        # Step-by-step table
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Step", "Reference", "Frames", "Fault/Hit", "Replaced")
        self.replace_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.replace_tree.heading(col, text=col)
            self.replace_tree.column(col, width=100, anchor=tk.CENTER)
        self.replace_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.replace_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.replace_tree.configure(yscrollcommand=scroll.set)
    
    def _create_replacement_visualization(self, parent):
        """Create replacement visualization."""
        frame = ttk.LabelFrame(parent, text="Frame State Timeline", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.replace_fig = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS['bg_panel'])
        self.replace_ax = self.replace_fig.add_subplot(111)
        self.replace_ax.set_facecolor(COLORS['bg_panel'])
        self.replace_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.replace_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.replace_canvas = FigureCanvasTkAgg(self.replace_fig, master=frame)
        self.replace_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _run_replacement(self):
        """Run page replacement simulation."""
        try:
            ref_str = [int(x.strip()) for x in self.ref_string_var.get().split(",") if x.strip()]
            num_frames = self.num_frames_var.get()
            algo = PageReplacementAlgorithm(self.replace_algo_var.get())
            
            result = PageReplacementSimulator.run_algorithm(algo, ref_str, num_frames)
            self._display_replacement_result(result)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _compare_all_replacement(self):
        """Compare all algorithms."""
        try:
            ref_str = [int(x.strip()) for x in self.ref_string_var.get().split(",") if x.strip()]
            num_frames = self.num_frames_var.get()
            
            results = PageReplacementSimulator.compare_all(ref_str, num_frames)
            
            # Show comparison dialog
            self._show_comparison_dialog(results)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _show_comparison_dialog(self, results: dict):
        """Show algorithm comparison dialog."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Algorithm Comparison")
        dialog.geometry("500x300")
        dialog.configure(bg=COLORS["bg_panel"])
        
        text = tk.Text(dialog, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono"])
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text.insert(tk.END, f"{'Algorithm':<12} {'Faults':>8} {'Hits':>8} {'Fault Rate':>12} {'Hit Rate':>10}\n")
        text.insert(tk.END, "-" * 55 + "\n")
        
        for algo, result in results.items():
            text.insert(tk.END, 
                f"{algo.value.upper():<12} {result.total_faults:>8} {result.total_hits:>8} "
                f"{result.fault_rate:>11.2%} {result.hit_rate:>9.2%}\n"
            )
        
        text.config(state=tk.DISABLED)
    
    def _display_replacement_result(self, result: ReplacementResult):
        """Display replacement result."""
        self.replace_metrics["faults"].config(text=str(result.total_faults))
        self.replace_metrics["hits"].config(text=str(result.total_hits))
        self.replace_metrics["fault_rate"].config(text=f"{result.fault_rate:.2%}")
        self.replace_metrics["hit_rate"].config(text=f"{result.hit_rate:.2%}")
        
        # Update table
        for item in self.replace_tree.get_children():
            self.replace_tree.delete(item)
        
        for step, (ref, frames, fault, replaced) in enumerate(zip(
            result.reference_string, result.frame_states, result.page_faults, result.replaced_pages
        )):
            frame_str = " | ".join(str(f) if f is not None else "-" for f in frames)
            self.replace_tree.insert("", tk.END, values=(
                step, ref, frame_str, "Fault" if fault else "Hit",
                str(replaced) if replaced is not None else "-"
            ))
        
        # Draw visualization
        self._draw_replacement_visualization(result)
    
    def _draw_replacement_visualization(self, result: ReplacementResult):
        """Draw replacement timeline."""
        self.replace_ax.clear()
        self.replace_ax.set_facecolor(COLORS['bg_panel'])
        self.replace_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.replace_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not result.frame_states:
            self.replace_canvas.draw()
            return
        
        num_steps = len(result.frame_states)
        num_frames = result.num_frames
        
        # Color map for pages
        all_pages = set(result.reference_string)
        colors = {}
        palette = ['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa', '#34d399', '#fb923c']
        for i, page in enumerate(sorted(all_pages)):
            colors[page] = palette[i % len(palette)]
        colors[None] = COLORS['bg_input']
        
        for frame_idx in range(num_frames):
            for step in range(num_steps):
                page = result.frame_states[step][frame_idx]
                color = colors.get(page, '#888888')
                alpha = 1.0 if page is not None else 0.3
                
                rect = self.replace_ax.barh(
                    frame_idx, 1, left=step, height=0.8,
                    color=color, alpha=alpha, edgecolor='white', linewidth=0.3
                )
                
                # Mark faults
                if result.page_faults[step] and page is not None:
                    # Check if this frame got the new page
                    if step == 0 or result.frame_states[step-1][frame_idx] != page:
                        self.replace_ax.plot(step + 0.5, frame_idx, 'r*', markersize=8)
        
        self.replace_ax.set_xlim(-0.5, num_steps - 0.5)
        self.replace_ax.set_ylim(-0.5, num_frames - 0.5)
        self.replace_ax.set_xlabel('Reference Step', color='white')
        self.replace_ax.set_ylabel('Frame', color='white')
        self.replace_ax.set_title(f'Page Replacement - {result.algorithm.value.upper()}', color='white')
        self.replace_ax.set_yticks(range(num_frames))
        self.replace_ax.set_yticklabels([f'F{i}' for i in range(num_frames)])
        
        self.replace_fig.tight_layout()
        self.replace_canvas.draw()
    
    # ==================== SEGMENTATION TAB ====================
    
    def _create_segmentation_tab(self):
        """Create segmentation tab."""
        main_paned = ttk.PanedWindow(self.segmentation_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Segments
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_segmentation_segments(left)
        self._create_segmentation_translation(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_segmentation_visualization(right)
    
    def _create_segmentation_segments(self, parent):
        """Create segment editor."""
        frame = ttk.LabelFrame(parent, text="Segments", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Name", "Base", "Limit")
        self.segment_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.segment_tree.heading(col, text=col)
            self.segment_tree.column(col, width=80, anchor=tk.CENTER)
        self.segment_tree.pack(fill=tk.BOTH, expand=True)
        
        # Edit form
        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(form, text="ID:").grid(row=0, column=0, padx=2)
        self.seg_id_var = tk.IntVar()
        ttk.Spinbox(form, from_=0, to=15, textvariable=self.seg_id_var, width=5).grid(row=0, column=1, padx=2)
        
        ttk.Label(form, text="Name:").grid(row=0, column=2, padx=2)
        self.seg_name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.seg_name_var, width=10).grid(row=0, column=3, padx=2)
        
        ttk.Label(form, text="Base:").grid(row=0, column=4, padx=2)
        self.seg_base_var = tk.IntVar()
        ttk.Entry(form, textvariable=self.seg_base_var, width=10).grid(row=0, column=5, padx=2)
        
        ttk.Label(form, text="Limit:").grid(row=0, column=6, padx=2)
        self.seg_limit_var = tk.IntVar()
        ttk.Entry(form, textvariable=self.seg_limit_var, width=10).grid(row=0, column=7, padx=2)
        
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=0, column=8, padx=10)
        ttk.Button(btn_frame, text="Add", command=self._add_segment).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Update", command=self._update_segment).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_segment).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Load Sample", command=self._load_sample_segments).pack(side=tk.LEFT, padx=2)
        
        self.segment_tree.bind("<<TreeviewSelect>>", self._on_segment_select)
    
    def _create_segmentation_translation(self, parent):
        """Create address translation panel."""
        frame = ttk.LabelFrame(parent, text="Address Translation", padding=10)
        frame.pack(fill=tk.X, pady=(10, 0))
        
        addr_frame = ttk.Frame(frame)
        addr_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(addr_frame, text="Segment:").pack(side=tk.LEFT, padx=2)
        self.seg_trans_seg_var = tk.IntVar(value=0)
        ttk.Spinbox(addr_frame, from_=0, to=15, textvariable=self.seg_trans_seg_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(addr_frame, text="Offset:").pack(side=tk.LEFT, padx=2)
        self.seg_trans_off_var = tk.IntVar(value=0)
        ttk.Entry(addr_frame, textvariable=self.seg_trans_off_var, width=10).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(addr_frame, text="Translate", command=self._translate_segmented).pack(side=tk.LEFT, padx=10)
        
        self.seg_translation_result = tk.Text(frame, height=6, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono_small"])
        self.seg_translation_result.pack(fill=tk.BOTH, expand=True)
    
    def _create_segmentation_visualization(self, parent):
        """Create segmentation visualization."""
        frame = ttk.LabelFrame(parent, text="Memory Map", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.seg_fig = Figure(figsize=(6, 5), dpi=100, facecolor=COLORS['bg_panel'])
        self.seg_ax = self.seg_fig.add_subplot(111)
        self.seg_ax.set_facecolor(COLORS['bg_panel'])
        self.seg_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.seg_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.seg_canvas = FigureCanvasTkAgg(self.seg_fig, master=frame)
        self.seg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _add_segment(self):
        """Add a segment."""
        try:
            sid = self.seg_id_var.get()
            name = self.seg_name_var.get().strip()
            base = self.seg_base_var.get()
            limit = self.seg_limit_var.get()
            
            if not name:
                messagebox.showerror("Error", "Segment name required")
                return
            if limit <= 0:
                messagebox.showerror("Error", "Limit must be positive")
                return
            if any(s.segment_id == sid for s in self.segments):
                messagebox.showerror("Error", f"Segment ID {sid} already exists")
                return
            
            # Check overlap
            new_start = base
            new_end = base + limit - 1
            for s in self.segments:
                if not (new_end < s.base or new_start > s.end):
                    messagebox.showerror("Error", f"Overlaps with segment {s.segment_id} ({s.name})")
                    return
            
            self.segments.append(Segment(sid, name, base, limit))
            self.segments.sort(key=lambda s: s.base)
            self._refresh_segments()
            self._draw_segmentation_visualization()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def _update_segment(self):
        """Update selected segment."""
        selection = self.segment_tree.selection()
        if not selection:
            return
        
        try:
            old_id = self.segment_tree.item(selection[0])['values'][0]
            sid = self.seg_id_var.get()
            name = self.seg_name_var.get().strip()
            base = self.seg_base_var.get()
            limit = self.seg_limit_var.get()
            
            if not name or limit <= 0:
                messagebox.showerror("Error", "Invalid values")
                return
            
            # Find and update
            for i, s in enumerate(self.segments):
                if s.segment_id == old_id:
                    # Check overlap with others
                    new_start = base
                    new_end = base + limit - 1
                    for j, other in enumerate(self.segments):
                        if j != i and not (new_end < other.base or new_start > other.end):
                            messagebox.showerror("Error", f"Overlaps with segment {other.segment_id}")
                            return
                    
                    self.segments[i] = Segment(sid, name, base, limit)
                    break
            
            self.segments.sort(key=lambda s: s.base)
            self._refresh_segments()
            self._draw_segmentation_visualization()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def _remove_segment(self):
        """Remove selected segment."""
        selection = self.segment_tree.selection()
        if not selection:
            return
        
        sid = self.segment_tree.item(selection[0])['values'][0]
        self.segments = [s for s in self.segments if s.segment_id != sid]
        self._refresh_segments()
        self._draw_segmentation_visualization()
    
    def _load_sample_segments(self):
        """Load sample segments."""
        self.segments = generate_sample_segments()
        self._refresh_segments()
        self._draw_segmentation_visualization()
    
    def _on_segment_select(self, event):
        """Handle segment selection."""
        selection = self.segment_tree.selection()
        if not selection:
            return
        
        values = self.segment_tree.item(selection[0])['values']
        self.seg_id_var.set(values[0])
        self.seg_name_var.set(values[1])
        self.seg_base_var.set(values[2])
        self.seg_limit_var.set(values[3])
    
    def _refresh_segments(self):
        """Refresh segment display."""
        for item in self.segment_tree.get_children():
            self.segment_tree.delete(item)
        
        for s in self.segments:
            self.segment_tree.insert("", tk.END, values=(s.segment_id, s.name, s.base, s.limit))
    
    def _translate_segmented(self):
        """Translate segmented address."""
        seg_id = self.seg_trans_seg_var.get()
        offset = self.seg_trans_off_var.get()
        
        result = SegmentationSimulator.translate_address(self.segments, (seg_id, offset))
        explanation = SegmentationSimulator.explain_translation(self.segments, (seg_id, offset))
        
        self.seg_translation_result.delete(1.0, tk.END)
        self.seg_translation_result.insert(tk.END, explanation)
        
        if not result.valid:
            self.seg_translation_result.tag_add("error", "1.0", "end")
            self.seg_translation_result.tag_config("error", foreground="#ff4444")
    
    def _draw_segmentation_visualization(self):
        """Draw segmentation memory map."""
        self.seg_ax.clear()
        self.seg_ax.set_facecolor(COLORS['bg_panel'])
        self.seg_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.seg_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        if not self.segments:
            self.seg_canvas.draw()
            return
        
        colors = ['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa', '#34d399', '#fb923c']
        
        max_addr = max(s.end for s in self.segments) if self.segments else 1000
        
        for i, seg in enumerate(self.segments):
            color = colors[i % len(colors)]
            self.seg_ax.barh(0, seg.limit, left=seg.base, height=0.6, 
                           color=color, edgecolor='white', linewidth=1)
            self.seg_ax.text(seg.base + seg.limit/2, 0, f"{seg.name} [{seg.base}-{seg.end}]",
                           ha='center', va='center', color='white', fontsize=9, fontweight='bold')
        
        # Show holes
        self.segments.sort(key=lambda s: s.base)
        for i in range(len(self.segments) - 1):
            hole_start = self.segments[i].end + 1
            hole_end = self.segments[i+1].base - 1
            if hole_end >= hole_start:
                self.seg_ax.barh(0, hole_end - hole_start + 1, left=hole_start, height=0.6,
                               color=COLORS['bg_input'], edgecolor=COLORS['text_secondary'], linewidth=0.5, hatch='///')
                self.seg_ax.text(hole_start + (hole_end - hole_start + 1)/2, 0, "FREE",
                               ha='center', va='center', color='#888888', fontsize=8)
        
        self.seg_ax.set_xlim(0, max_addr * 1.1)
        self.seg_ax.set_ylim(-0.5, 0.5)
        self.seg_ax.set_xlabel('Memory Address', color='white')
        self.seg_ax.set_title('Segmentation Memory Layout', color='white')
        self.seg_ax.set_yticks([])
        
        self.seg_fig.tight_layout()
        self.seg_canvas.draw()
    
    # ==================== FRAGMENTATION TAB ====================
    
    def _create_fragmentation_tab(self):
        """Create fragmentation tab."""
        main_paned = ttk.PanedWindow(self.fragmentation_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Configuration
        left = ttk.Frame(main_paned)
        main_paned.add(left, weight=1)
        
        self._create_fragmentation_config(left)
        self._create_fragmentation_results(left)
        
        # Right - Visualization
        right = ttk.Frame(main_paned)
        main_paned.add(right, weight=1)
        
        self._create_fragmentation_visualization(right)
    
    def _create_fragmentation_config(self, parent):
        """Create fragmentation configuration."""
        # Memory blocks
        blocks_frame = ttk.LabelFrame(parent, text="Memory Blocks", padding=10)
        blocks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("Start", "Size", "Status")
        self.block_tree = ttk.Treeview(blocks_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.block_tree.heading(col, text=col)
            self.block_tree.column(col, width=80, anchor=tk.CENTER)
        self.block_tree.pack(fill=tk.BOTH, expand=True)
        
        block_form = ttk.Frame(blocks_frame)
        block_form.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(block_form, text="Start:").pack(side=tk.LEFT, padx=2)
        self.block_start_var = tk.IntVar()
        ttk.Entry(block_form, textvariable=self.block_start_var, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(block_form, text="Size:").pack(side=tk.LEFT, padx=2)
        self.block_size_var = tk.IntVar()
        ttk.Entry(block_form, textvariable=self.block_size_var, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(block_form, text="Add Block", command=self._add_block).pack(side=tk.LEFT, padx=5)
        ttk.Button(block_form, text="Load Sample", command=self._load_sample_fragmentation).pack(side=tk.LEFT, padx=5)
        
        # Process requests
        req_frame = ttk.LabelFrame(parent, text="Process Requests", padding=10)
        req_frame.pack(fill=tk.X, pady=(0, 10))
        
        req_form = ttk.Frame(req_frame)
        req_form.pack(fill=tk.X)
        
        ttk.Label(req_form, text="PID:").pack(side=tk.LEFT, padx=2)
        self.req_pid_var = tk.StringVar()
        ttk.Entry(req_form, textvariable=self.req_pid_var, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(req_form, text="Size:").pack(side=tk.LEFT, padx=2)
        self.req_size_var = tk.IntVar()
        ttk.Entry(req_form, textvariable=self.req_size_var, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(req_form, text="Add Request", command=self._add_request).pack(side=tk.LEFT, padx=5)
        ttk.Button(req_form, text="Update", command=self._update_request).pack(side=tk.LEFT, padx=5)
        ttk.Button(req_form, text="Clear", command=self._clear_request_form).pack(side=tk.LEFT, padx=5)
        
        # Request list
        req_columns = ("PID", "Size")
        self.req_tree = ttk.Treeview(req_frame, columns=req_columns, show="headings", height=4)
        for col in req_columns:
            self.req_tree.heading(col, text=col)
            self.req_tree.column(col, width=80, anchor=tk.CENTER)
        self.req_tree.pack(fill=tk.X, pady=5)
        
        # Bind selection to populate form
        self.req_tree.bind("<<TreeviewSelect>>", self._on_request_select)
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(parent, text="Algorithm", padding=10)
        algo_frame.pack(fill=tk.X)
        
        self.frag_algo_var = tk.StringVar(value=AllocationAlgorithm.FIRST_FIT.value)
        for algo in AllocationAlgorithm:
            ttk.Radiobutton(algo_frame, text=algo.value.replace('_', ' ').title(),
                           variable=self.frag_algo_var, value=algo.value).pack(anchor=tk.W)
        
        ttk.Button(algo_frame, text="Run Allocation", command=self._run_fragmentation).pack(fill=tk.X, pady=5)
        ttk.Button(algo_frame, text="Compare All", command=self._compare_all_fragmentation).pack(fill=tk.X)
    
    def _create_fragmentation_results(self, parent):
        """Create fragmentation results."""
        frame = ttk.LabelFrame(parent, text="Results", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.frag_metrics = {}
        for i, (label, key) in enumerate([
            ("Allocated", "allocated"), ("Free", "free"),
            ("Internal Frag", "internal"), ("External Frag", "external")
        ]):
            row, col = divmod(i, 2)
            f = ttk.Frame(frame)
            f.grid(row=row, column=col, padx=10, pady=5, sticky=tk.W)
            ttk.Label(f, text=f"{label}:", font=FONTS["small"]).pack(side=tk.LEFT)
            self.frag_metrics[key] = ttk.Label(f, text="--", font=FONTS["small"])
            self.frag_metrics[key].pack(side=tk.LEFT, padx=5)
        
        # Allocation log
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=(10, 0))
        frame.rowconfigure(2, weight=1)
        self.frag_log = tk.Text(log_frame, height=8, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono_small"])
        self.frag_log.pack(fill=tk.BOTH, expand=True)
    
    def _create_fragmentation_visualization(self, parent):
        """Create fragmentation visualization."""
        frame = ttk.LabelFrame(parent, text="Memory Layout", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.frag_fig = Figure(figsize=(8, 4), dpi=100, facecolor=COLORS['bg_panel'])
        self.frag_ax = self.frag_fig.add_subplot(111)
        self.frag_ax.set_facecolor(COLORS['bg_panel'])
        self.frag_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.frag_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        self.frag_canvas = FigureCanvasTkAgg(self.frag_fig, master=frame)
        self.frag_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _add_block(self):
        """Add memory block."""
        try:
            start = self.block_start_var.get()
            size = self.block_size_var.get()
            
            if size <= 0:
                messagebox.showerror("Error", "Size must be positive")
                return
            
            # Check overlap
            new_end = start + size - 1
            for b in self.memory_blocks:
                if not (new_end < b.start or start > b.end):
                    messagebox.showerror("Error", f"Overlaps with existing block at {b.start}")
                    return
            
            self.memory_blocks.append(MemoryBlock(start, size))
            self.memory_blocks.sort(key=lambda b: b.start)
            self._refresh_blocks()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def _add_request(self):
        """Add process request."""
        pid = self.req_pid_var.get().strip()
        try:
            size = self.req_size_var.get()
            
            if not pid:
                messagebox.showerror("Error", "Process ID required")
                return
            if size <= 0:
                messagebox.showerror("Error", "Size must be positive")
                return
            
            self.process_requests.append((pid, size))
            self.req_tree.insert("", tk.END, values=(pid, size))
            self.req_pid_var.set("")
            self.req_size_var.set(0)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def _on_request_select(self, event):
        """Populate form from selected request."""
        selection = self.req_tree.selection()
        if not selection:
            return
        values = self.req_tree.item(selection[0])['values']
        self.req_pid_var.set(str(values[0]))
        self.req_size_var.set(int(values[1]))
    
    def _clear_request_form(self):
        """Clear request input fields and selection."""
        self.req_pid_var.set("")
        self.req_size_var.set(0)
        self.req_tree.selection_remove(self.req_tree.selection())
    
    def _update_request(self):
        """Update selected request or add new one with validation."""
        pid = self.req_pid_var.get().strip()
        try:
            size = self.req_size_var.get()
            
            if not pid:
                messagebox.showerror("Error", "Process ID required")
                return
            if size <= 0:
                messagebox.showerror("Error", "Size must be positive")
                return
            
            selection = self.req_tree.selection()
            if selection:
                # Update existing request
                idx = self.req_tree.index(selection[0])
                self.process_requests[idx] = (pid, size)
                self.req_tree.item(selection[0], values=(pid, size))
                self.req_tree.selection_remove(selection)
            else:
                # Add new request (same as Add Request)
                self.process_requests.append((pid, size))
                self.req_tree.insert("", tk.END, values=(pid, size))
            
            self.req_pid_var.set("")
            self.req_size_var.set(0)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def _load_sample_fragmentation(self):
        """Load sample fragmentation data."""
        self.memory_blocks = generate_sample_memory_blocks()
        self.process_requests = generate_sample_process_requests()
        self._refresh_blocks()
        self._refresh_requests()
    
    def _refresh_blocks(self):
        """Refresh block display."""
        for item in self.block_tree.get_children():
            self.block_tree.delete(item)
        
        for b in self.memory_blocks:
            self.block_tree.insert("", tk.END, values=(b.start, b.size, "Free" if not b.allocated else f"P{b.process_id}"))
    
    def _refresh_requests(self):
        """Refresh request display."""
        for item in self.req_tree.get_children():
            self.req_tree.delete(item)
        
        for pid, size in self.process_requests:
            self.req_tree.insert("", tk.END, values=(pid, size))
    
    def _run_fragmentation(self):
        """Run fragmentation simulation."""
        if not self.memory_blocks or not self.process_requests:
            messagebox.showerror("Error", "Define memory blocks and process requests first")
            return
        
        algo = AllocationAlgorithm(self.frag_algo_var.get())
        result = FragmentationSimulator.allocate(algo, self.memory_blocks, self.process_requests)
        self._display_fragmentation_result(result)
    
    def _compare_all_fragmentation(self):
        """Compare all fragmentation algorithms."""
        if not self.memory_blocks or not self.process_requests:
            messagebox.showerror("Error", "Define memory blocks and process requests first")
            return
        
        results = FragmentationSimulator.compare_all(self.memory_blocks, self.process_requests)
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Algorithm Comparison")
        dialog.geometry("600x300")
        dialog.configure(bg=COLORS["bg_panel"])
        
        text = tk.Text(dialog, bg=COLORS["bg_panel"], fg=COLORS["text_primary"], font=FONTS["mono"])
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text.insert(tk.END, f"{'Algorithm':<15} {'Allocated':>10} {'Free':>10} {'Internal':>10} {'External':>10}\n")
        text.insert(tk.END, "-" * 60 + "\n")
        
        for algo, result in results.items():
            text.insert(tk.END,
                f"{algo.value.replace('_', ' ').title():<15} "
                f"{result.allocated_memory:>10} {result.free_memory:>10} "
                f"{result.internal_fragmentation:>10} {result.external_fragmentation:>10}\n"
            )
        
        text.config(state=tk.DISABLED)
    
    def _display_fragmentation_result(self, result: FragmentationResult):
        """Display fragmentation result."""
        self.frag_metrics["allocated"].config(text=str(result.allocated_memory))
        self.frag_metrics["free"].config(text=str(result.free_memory))
        self.frag_metrics["internal"].config(text=str(result.internal_fragmentation))
        self.frag_metrics["external"].config(text=str(result.external_fragmentation))
        
        self.frag_log.delete(1.0, tk.END)
        self.frag_log.insert(tk.END, f"Algorithm: {result.algorithm.value.replace('_', ' ').title()}\n\n")
        
        for pid, size, start, success in result.allocations:
            if success:
                self.frag_log.insert(tk.END, f"✓ {pid}: {size} units → address {start}\n", "success")
            else:
                self.frag_log.insert(tk.END, f"✗ {pid}: {size} units → ALLOCATION FAILED\n", "fail")
        
        self.frag_log.tag_config("success", foreground="#00ff00")
        self.frag_log.tag_config("fail", foreground="#ff4444")
        
        self._draw_fragmentation_visualization(result)
    
    def _draw_fragmentation_visualization(self, result: FragmentationResult = None):
        """Draw fragmentation memory layout."""
        self.frag_ax.clear()
        self.frag_ax.set_facecolor(COLORS['bg_panel'])
        self.frag_ax.tick_params(colors=COLORS['text_secondary'])
        for spine in self.frag_ax.spines.values():
            spine.set_color(COLORS['border'])
        
        blocks = result.final_blocks if result else self.memory_blocks
        if not blocks:
            self.frag_canvas.draw()
            return
        
        colors = ['#6c8cff', '#f87171', '#4ade80', '#fbbf24', '#a78bfa', '#60a5fa', '#34d399', '#fb923c']
        color_idx = 0
        
        max_addr = max(b.end for b in blocks)
        
        for block in blocks:
            if block.allocated:
                color = colors[color_idx % len(colors)]
                color_idx += 1
                label = f"{block.process_id} ({block.size})"
            else:
                color = COLORS['bg_input']
                label = f"FREE ({block.size})"
            
            self.frag_ax.barh(0, block.size, left=block.start, height=0.6,
                            color=color, edgecolor='white', linewidth=1)
            self.frag_ax.text(block.start + block.size/2, 0, label,
                            ha='center', va='center', color='white', fontsize=9, fontweight='bold')
        
        self.frag_ax.set_xlim(0, max_addr * 1.05)
        self.frag_ax.set_ylim(-0.5, 0.5)
        self.frag_ax.set_xlabel('Memory Address', color='white')
        title = f'Memory Layout - {result.algorithm.value.replace("_", " ").title()}' if result else 'Initial Memory Layout'
        self.frag_ax.set_title(title, color='white')
        self.frag_ax.set_yticks([])
        
        self.frag_fig.tight_layout()
        self.frag_canvas.draw()
    
    # ==================== COMMON ====================
    
    def _load_sample_data(self):
        """Load all sample data."""
        # Paging
        self.paging_config = generate_sample_paging_config()
        self.logical_mem_var.set(self.paging_config.logical_memory_size // 1024)
        self.physical_mem_var.set(self.paging_config.physical_memory_size // 1024)
        self.page_size_var.set(self.paging_config.page_size // 1024)
        self._apply_paging_config()
        
        # Page Replacement
        self.ref_string_var.set(",".join(map(str, generate_sample_page_references())))
        self.num_frames_var.set(3)
        
        # Segmentation
        self.segments = generate_sample_segments()
        self._refresh_segments()
        self._draw_segmentation_visualization()
        
        # Fragmentation
        self.memory_blocks = generate_sample_memory_blocks()
        self.process_requests = generate_sample_process_requests()
        self._refresh_blocks()
        self._refresh_requests()


def create_memory_module(parent_window, content_frame):
    """Factory function to create memory manager module."""
    return MemoryWindow(parent_window, content_frame)
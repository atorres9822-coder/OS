"""
Simulation engine for Mini OS Simulator.
Provides a reusable simulation playback system with step-by-step execution control.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import copy


class SimulationState(Enum):
    """State of the simulation playback."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STEP = "step"


@dataclass
class SimulationEvent:
    """Represents a single event in the simulation timeline."""
    time: float
    event_type: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    snapshot: Optional[Dict[str, Any]] = None
    
    def __lt__(self, other):
        return self.time < other.time


@dataclass
class SimulationSnapshot:
    """Complete state snapshot at a point in time."""
    time: float
    state: Dict[str, Any]
    description: str = ""


class SimulationEngine:
    """
    Core simulation engine that manages event timelines and playback.
    
    Algorithms precompute their events and snapshots, then the engine
    handles playback, stepping, and state management.
    """
    
    def __init__(self):
        self.events: List[SimulationEvent] = []
        self.snapshots: List[SimulationSnapshot] = []
        self.current_time: float = 0.0
        self.current_event_index: int = 0
        self.state: SimulationState = SimulationState.STOPPED
        self.playback_speed: float = 1.0
        self.on_event_callback: Optional[Callable[[SimulationEvent], None]] = None
        self.on_state_change_callback: Optional[Callable[[SimulationState], None]] = None
        self.on_complete_callback: Optional[Callable[[], None]] = None
        self._after_id: Optional[str] = None
        self._tk_root = None
    
    def set_tk_root(self, root):
        """Set the Tkinter root for after() scheduling."""
        self._tk_root = root
    
    def load_events(self, events: List[SimulationEvent], snapshots: List[SimulationSnapshot] = None):
        """Load precomputed events and snapshots."""
        self.events = sorted(events, key=lambda e: e.time)
        self.snapshots = snapshots or []
        self.current_time = 0.0
        self.current_event_index = 0
        self.state = SimulationState.STOPPED
    
    def set_callbacks(
        self,
        on_event: Optional[Callable[[SimulationEvent], None]] = None,
        on_state_change: Optional[Callable[[SimulationState], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """Set callback functions for simulation events."""
        self.on_event_callback = on_event
        self.on_state_change_callback = on_state_change
        self.on_complete_callback = on_complete
    
    def set_playback_speed(self, speed: float):
        """Set playback speed multiplier."""
        self.playback_speed = max(0.1, min(10.0, speed))
    
    def start(self):
        """Start or resume simulation."""
        if self.state == SimulationState.RUNNING:
            return
        
        if self.state == SimulationState.STOPPED:
            self.current_time = 0.0
            self.current_event_index = 0
        
        self.state = SimulationState.RUNNING
        if self.on_state_change_callback:
            self.on_state_change_callback(self.state)
        self._run_next_event()
    
    def pause(self):
        """Pause simulation."""
        if self.state != SimulationState.RUNNING:
            return
        
        self.state = SimulationState.PAUSED
        if self._after_id and self._tk_root:
            self._tk_root.after_cancel(self._after_id)
            self._after_id = None
        if self.on_state_change_callback:
            self.on_state_change_callback(self.state)
    
    def stop(self):
        """Stop simulation and reset."""
        if self._after_id and self._tk_root:
            self._tk_root.after_cancel(self._after_id)
            self._after_id = None
        
        self.state = SimulationState.STOPPED
        self.current_time = 0.0
        self.current_event_index = 0
        if self.on_state_change_callback:
            self.on_state_change_callback(self.state)
    
    def step_forward(self):
        """Execute single step forward."""
        if self.current_event_index >= len(self.events):
            return
        
        self.state = SimulationState.STEP
        if self.on_state_change_callback:
            self.on_state_change_callback(self.state)
        
        event = self.events[self.current_event_index]
        self.current_time = event.time
        self.current_event_index += 1
        
        if self.on_event_callback:
            self.on_event_callback(event)
        
        # Check if complete
        if self.current_event_index >= len(self.events):
            self.state = SimulationState.STOPPED
            if self.on_state_change_callback:
                self.on_state_change_callback(self.state)
            if self.on_complete_callback:
                self.on_complete_callback()
        else:
            self.state = SimulationState.PAUSED
            if self.on_state_change_callback:
                self.on_state_change_callback(self.state)
    
    def step_backward(self):
        """Step backward to previous event."""
        if self.current_event_index <= 0:
            return
        
        self.current_event_index -= 1
        event = self.events[self.current_event_index]
        self.current_time = event.time
        
        if self.on_event_callback:
            self.on_event_callback(event)
    
    def jump_to_time(self, time: float):
        """Jump to a specific simulation time."""
        # Find the event at or before this time
        new_index = 0
        for i, event in enumerate(self.events):
            if event.time <= time:
                new_index = i + 1
            else:
                break
        
        self.current_event_index = new_index
        if new_index > 0:
            self.current_time = self.events[new_index - 1].time
        else:
            self.current_time = 0.0
        
        if self.on_event_callback and new_index > 0:
            self.on_event_callback(self.events[new_index - 1])
    
    def get_progress(self) -> float:
        """Get simulation progress as 0.0 to 1.0."""
        if not self.events:
            return 1.0
        return self.current_event_index / len(self.events)
    
    def get_current_snapshot(self) -> Optional[SimulationSnapshot]:
        """Get the snapshot for current time."""
        for snapshot in reversed(self.snapshots):
            if snapshot.time <= self.current_time:
                return snapshot
        return None
    
    def _run_next_event(self):
        """Internal method to run the next event."""
        if self.state != SimulationState.RUNNING:
            return
        
        if self.current_event_index >= len(self.events):
            self.state = SimulationState.STOPPED
            if self.on_state_change_callback:
                self.on_state_change_callback(self.state)
            if self.on_complete_callback:
                self.on_complete_callback()
            return
        
        event = self.events[self.current_event_index]
        self.current_time = event.time
        self.current_event_index += 1
        
        if self.on_event_callback:
            self.on_event_callback(event)
        
        # Schedule next event
        if self.current_event_index < len(self.events):
            next_event = self.events[self.current_event_index]
            delay = (next_event.time - event.time) * 1000 / self.playback_speed
            delay = max(10, int(delay))  # Minimum 10ms
            
            if self._tk_root:
                self._after_id = self._tk_root.after(delay, self._run_next_event)
        else:
            # Last event completed
            self.state = SimulationState.STOPPED
            if self.on_state_change_callback:
                self.on_state_change_callback(self.state)
            if self.on_complete_callback:
                self.on_complete_callback()


class PlaybackControls:
    """UI component for simulation playback controls."""
    
    def __init__(self, parent: 'tk.Frame', engine: SimulationEngine):
        self.parent = parent
        self.engine = engine
        self.frame = tk.Frame(parent, bg="#1e1e1e", height=50)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        self.frame.pack_propagate(False)
        self._create_controls()
    
    def _create_controls(self):
        import tkinter as tk
        
        # Control buttons
        btn_frame = tk.Frame(self.frame, bg="#1e1e1e")
        btn_frame.pack(side=tk.LEFT, padx=10)
        
        self.btn_restart = tk.Button(
            btn_frame, text="⏮", width=3,
            bg="#333333", fg="#ffffff", bd=0,
            activebackground="#444444",
            command=self.engine.stop
        )
        self.btn_restart.pack(side=tk.LEFT, padx=2)
        
        self.btn_step_back = tk.Button(
            btn_frame, text="⏪", width=3,
            bg="#333333", fg="#ffffff", bd=0,
            activebackground="#444444",
            command=self.engine.step_backward
        )
        self.btn_step_back.pack(side=tk.LEFT, padx=2)
        
        self.btn_play = tk.Button(
            btn_frame, text="▶", width=3,
            bg="#0078d7", fg="#ffffff", bd=0,
            activebackground="#1084d8",
            command=self.engine.start
        )
        self.btn_play.pack(side=tk.LEFT, padx=2)
        
        self.btn_pause = tk.Button(
            btn_frame, text="⏸", width=3,
            bg="#333333", fg="#ffffff", bd=0,
            activebackground="#444444",
            command=self.engine.pause
        )
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        
        self.btn_step_forward = tk.Button(
            btn_frame, text="⏩", width=3,
            bg="#333333", fg="#ffffff", bd=0,
            activebackground="#444444",
            command=self.engine.step_forward
        )
        self.btn_step_forward.pack(side=tk.LEFT, padx=2)
        
        # Speed control
        speed_frame = tk.Frame(self.frame, bg="#1e1e1e")
        speed_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(speed_frame, text="Speed:", bg="#1e1e1e", fg="#ffffff").pack(side=tk.LEFT)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = tk.Scale(
            speed_frame,
            from_=0.1,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            bg="#1e1e1e",
            fg="#ffffff",
            highlightthickness=0,
            troughcolor="#333333",
            length=150,
            command=self._on_speed_change
        )
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = tk.Frame(self.frame, bg="#1e1e1e")
        progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = tk.Scale(
            progress_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            bg="#1e1e1e",
            fg="#ffffff",
            highlightthickness=0,
            troughcolor="#333333",
            showvalue=False,
            command=self._on_progress_change
        )
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        # Time display
        self.time_label = tk.Label(
            self.frame,
            text="Time: 0.00",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 9)
        )
        self.time_label.pack(side=tk.RIGHT, padx=10)
        
        # Update loop
        self._update_ui()
    
    def _on_speed_change(self, value):
        self.engine.set_playback_speed(float(value))
    
    def _on_progress_change(self, value):
        progress = float(value) / 100.0
        if self.engine.events:
            target_time = self.engine.events[-1].time * progress
            self.engine.jump_to_time(target_time)
    
    def _update_ui(self):
        """Update UI elements based on engine state."""
        progress = self.engine.get_progress() * 100
        self.progress_var.set(progress)
        self.time_label.config(text=f"Time: {self.engine.current_time:.2f}")
        
        # Update button states
        if self.engine.state == SimulationState.RUNNING:
            self.btn_play.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
        else:
            self.btn_play.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
        
        self.parent.after(100, self._update_ui)


# Import tkinter at module level for PlaybackControls
import tkinter as tk
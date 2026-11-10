# Architecture Documentation

## Overview

Mini OS Simulator follows a modular architecture separating concerns between:
- **GUI Layer**: Desktop environment, windows, and module interfaces
- **Simulation Layer**: Playback engine and event management
- **Algorithm Layer**: Core OS algorithm implementations
- **Data Layer**: Data structures and models

## Directory Structure

```
mini-os/
├── main.py                 # Application entry point
├── gui/
│   └── desktop.py         # Desktop environment with window management
├── modules/
│   ├── cpu_scheduling/
│   │   ├── algorithms.py  # Scheduling algorithm implementations
│   │   └── gui.py         # Module GUI
│   ├── deadlock/
│   │   ├── algorithms.py  # Banker's algorithm
│   │   └── gui.py         # Module GUI
│   ├── memory/
│   │   ├── algorithms.py  # Paging, replacement, segmentation, fragmentation
│   │   └── gui.py         # Module GUI
│   ├── disk_scheduling/
│   │   ├── algorithms.py  # Disk scheduling algorithms
│   │   └── gui.py         # Module GUI
│   ├── process_manager/
│   │   ├── algorithms.py  # Process simulation
│   │   └── gui.py         # Module GUI
│   └── system_monitor/
│       └── gui.py         # System monitor GUI
├── simulation/
│   └── engine.py          # Playback engine & controls
└── tests/                 # Unit tests
```

## Core Components

### Desktop Environment (`gui/desktop.py`)

The `DesktopApp` class manages:
- **Window Management**: `Window` class for draggable, minimizable, maximizable windows
- **Desktop Icons**: `DesktopIcon` for module launchers
- **Taskbar**: `TaskbarButton` for window management
- **Start Menu**: Application launcher

Each module window is a `tk.Toplevel` with custom title bar and controls.

### Module Factory Pattern

Each module exposes a factory function:
```python
def create_cpu_scheduling_module(parent_window, content_frame) -> ModuleInstance
```

This allows the desktop to instantiate modules without knowing their internal structure.

### Simulation Engine (`simulation/engine.py`)

The `SimulationEngine` class provides:
- **Event-driven playback**: Precomputed events with timestamps
- **State management**: STOPPED, RUNNING, PAUSED, STEP states
- **Callbacks**: `on_event`, `on_state_change`, `on_complete`
- **Tkinter integration**: Uses `after()` for non-blocking animation
- **Variable speed**: Configurable playback speed multiplier

The `PlaybackControls` class provides a reusable UI component with:
- Play/Pause/Stop/Step buttons
- Speed slider
- Progress bar with time jumping
- Current time display

### Algorithm Modules

Each algorithm module follows a consistent pattern:

1. **Data Classes**: `@dataclass` for inputs, configurations, results
2. **Algorithm Class**: Static methods for each algorithm
3. **Validation**: Input validation with descriptive errors
4. **Factory Function**: `run_algorithm(algorithm_type, inputs, params)`
5. **Comparison**: `compare_all(inputs, params)` for side-by-side analysis
6. **Event Generation**: `generate_simulation_events(result)` for playback

#### Example: CPU Scheduling

```python
# Input
processes = [Process(pid, arrival, burst, priority)]

# Run
result = CPUScheduler.run_algorithm(AlgorithmType.FCFS, processes)

# Result contains:
# - processes with computed metrics
# - gantt_chart: List[GanttEntry]
# - avg_turnaround_time, avg_waiting_time, etc.
# - cpu_utilization, throughput, context_switches

# Playback
events, snapshots = CPUScheduler.generate_simulation_events(result)
engine.load_events(events, snapshots)
```

### GUI Modules

Each GUI module:
- Creates its own UI within a provided `content_frame`
- Uses the simulation engine for playback
- Displays results in tables and charts (matplotlib)
- Provides explanations for algorithm decisions
- Handles input validation with user feedback

### Visualization Strategy

**Matplotlib with TkAgg backend** embedded in Tkinter:
- Dark theme (`#1e1e1e` background) matching app theme
- Gantt charts for scheduling
- Memory maps for paging/segmentation
- Timeline charts for disk head movement
- Bar charts for comparisons

Charts are redrawn on simulation events for playback highlighting.

## Data Flow

```
User Input
    ↓
Module GUI (validation)
    ↓
Algorithm Module (computation)
    ↓
Result Object (metrics, gantt chart, etc.)
    ↓
Event Generation (for playback)
    ↓
Simulation Engine (timeline management)
    ↓
Playback Controls + Visualization Updates
    ↓
User sees animated results
```

## Key Design Decisions

### Precomputation over Real-time Simulation

Algorithms compute complete results first, then events are generated for playback. This ensures:
- Deterministic results
- Accurate visualizations
- Step-backward capability
- No race conditions

### Separation of Algorithm and GUI

- Algorithms are pure functions/classes with no GUI dependencies
- GUI modules import algorithms, not vice versa
- Enables unit testing without GUI
- Allows algorithm reuse

### Event-based Playback

- `SimulationEvent`: Discrete event with timestamp, type, data
- `SimulationSnapshot`: Full state at a point in time
- Engine manages timeline, UI subscribes to events

### Theme Consistency

Dark theme colors defined as constants:
- Background: `#1e1e1e`
- Panels: `#2d2d2d`
- Accent: `#0078d7`
- Success: `#00b294`
- Warning: `#ff8c00`
- Error: `#e81123`

### Extensibility

Adding a new module:
1. Create algorithm module with standard interface
2. Create GUI module with factory function
3. Register in `desktop.py` module_factories dict
4. Add desktop icon and start menu entry

## Threading Model

**Single-threaded** using Tkinter's event loop:
- All computation runs in main thread
- Long computations should be avoided or chunked
- `after()` used for animation timing
- No `time.sleep()` in GUI thread

## Error Handling

- Input validation at GUI and algorithm level
- User-friendly error dialogs
- Graceful degradation (placeholder UI on module load failure)
- Logging via explanation panels

## Performance Considerations

- Matplotlib figures reused, not recreated
- Canvas redraw only on state changes
- Event lists pre-allocated
- Treeview virtual scrolling for large datasets
- History limited to 60 seconds in System Monitor

## Testing Strategy

- Unit tests for all algorithms (`tests/`)
- Edge cases: empty inputs, single items, boundaries
- Property-based: optimal ≤ FIFO faults, conservation laws
- Mock GUI testing not implemented (manual verification)
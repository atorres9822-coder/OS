# Mini OS Simulator

An interactive educational operating system simulator for academic final projects.

## Overview

Mini OS Simulator is a desktop application that simulates core operating system concepts including:
- CPU Scheduling
- Deadlock Management (Banker's Algorithm)
- Memory Management (Paging, Page Replacement, Segmentation, Fragmentation)
- Disk Scheduling
- Process Management (Multiprogramming & Multiprocessing)
- System Monitoring

## Features

- **OS-Inspired Desktop Interface**: Desktop icons, taskbar, start menu, and window management
- **Interactive Simulations**: Configure inputs, select algorithms, run step-by-step simulations
- **Visualizations**: Gantt charts, memory maps, disk head movement animations
- **Playback Controls**: Start, pause, step forward/backward, adjustable speed
- **Educational Explanations**: Step-by-step reasoning for algorithm decisions

## Supported Algorithms

### CPU Scheduling
- First Come First Serve (FCFS)
- Shortest Job First (SJF) - Non-preemptive
- Shortest Remaining Time First (SRTF) - Preemptive
- Priority Scheduling - Non-preemptive
- Priority Scheduling - Preemptive
- Round Robin

### Deadlock Management
- Banker's Algorithm (Safety Algorithm & Resource Request Algorithm)

### Memory Management
- Paging with address translation
- Page Replacement: FIFO, LRU, Optimal
- Segmentation with address translation
- Memory Fragmentation: First Fit, Best Fit, Worst Fit

### Disk Scheduling
- FCFS
- SSTF (Shortest Seek Time First)
- SCAN (Elevator)
- C-SCAN (Circular SCAN)
- LOOK
- C-LOOK

### Process Management
- Multiprogramming simulation (single CPU with Round Robin)
- Multiprocessing simulation (multi-core with shared ready queue)
- Process state transitions (NEW, READY, RUNNING, WAITING, TERMINATED)

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- matplotlib

Install dependencies:
```bash
pip install matplotlib Pillow
```

On Linux, you may need to install tkinter separately:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## Running the Application

### Quick Start (Recommended)

Use the launcher script for your platform:

**Linux/macOS:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

The launcher script automatically:
1. Sets the working directory to the project root
2. Activates a virtual environment if one is present (`.venv`, `venv`, `env`, `.env`)
3. Runs `main.py` using Python 3.14 (or falls back to `python3` / `python`)

### Manual Execution

Alternatively, run directly with Python:

```bash
python3.14 main.py
```

Or with conda Python (includes all dependencies):

```bash
/home/saint/miniconda3/bin/python main.py
```

**Note:** The system `python3` may not have tkinter. Use `python3.14` or conda Python.

### Installing Dependencies

If you encounter missing dependency errors, install the required packages:

```bash
pip install -r requirements.txt
```

On Linux, you may need to install tkinter separately:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## Project Structure

```
mini-os/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md              # This file
├── CHANGELOG.md           # Version history
├── gui/
│   └── desktop.py         # Desktop environment
├── modules/
│   ├── cpu_scheduling/    # CPU scheduling algorithms & GUI
│   ├── deadlock/          # Banker's algorithm & GUI
│   ├── memory/            # Memory management & GUI
│   ├── disk_scheduling/   # Disk scheduling & GUI
│   ├── process_manager/   # Process management & GUI
│   └── system_monitor/    # System monitor & GUI
├── simulation/
│   └── engine.py          # Simulation playback engine
├── tests/                 # Unit tests
└── docs/
    ├── ARCHITECTURE.md    # Architecture documentation
    └── ALGORITHMS.md      # Algorithm explanations
```

## Usage

1. Launch the application - you'll see the Mini OS desktop
2. Double-click any module icon or use the Start menu to open a simulation
3. Configure your inputs (processes, resources, memory, etc.)
4. Select an algorithm
5. Click "Run Simulation" or use playback controls
6. Observe the visualization and results
7. Use step controls to inspect each decision

## Keyboard Shortcuts

- `Space`: Play/Pause simulation
- `←/→`: Step backward/forward
- `R`: Reset simulation
- `+/-`: Adjust playback speed

## Testing

Run unit tests:
```bash
python run_tests.py
```

Or run specific test module:
```bash
python -m tests.test_cpu_scheduling
python -m tests.test_deadlock
python -m tests.test_memory
python -m tests.test_disk_scheduling
python -m tests.test_process_manager
```

## Educational Value

This simulator helps Computer Science students understand:
- How scheduling algorithms make decisions
- Why certain algorithms perform better in specific scenarios
- The mechanics of deadlock avoidance
- Memory address translation
- Page replacement trade-offs
- Disk head movement optimization
- Process state machines
- Concurrency vs parallelism

## License

Educational project for academic purposes.

## Contributing

This is a student project. For improvements, please refer to the course instructor.
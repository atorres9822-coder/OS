# Mini OS Simulator — Algorithm Guide

This document explains every algorithm you can run in the Mini OS Simulator, in plain language.
No prior OS knowledge needed. Each section tells you:

- What the algorithm does
- When to use it
- A simple example
- The steps the simulator takes
- What the results mean

---

## Table of Contents

1. [CPU Scheduling](#cpu-scheduling)
   - FCFS
   - SJF (Non-preemptive)
   - SRTF (Preemptive)
   - Priority (Non-preemptive)
   - Priority (Preemptive)
   - Round Robin
2. [Deadlock Management — Banker's Algorithm](#deadlock-management--bankers-algorithm)
   - Safety Algorithm
   - Resource Request Algorithm
3. [Memory Management](#memory-management)
   - Paging & Address Translation
   - Page Replacement (FIFO, LRU, Optimal)
   - Segmentation & Address Translation
   - Memory Fragmentation (First Fit, Best Fit, Worst Fit)
4. [Disk Scheduling](#disk-scheduling)
   - FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
5. [Process Management](#process-management)
   - Multiprogramming
   - Multiprocessing
   - Process State Transitions
6. [System Monitor](#system-monitor)

---

## 1. CPU Scheduling

### The Problem

You have several processes (programs) that need the CPU. The CPU can only run one at a time. The scheduler decides **which process runs next** and for **how long**.

### Key Terms

| Term | Meaning |
|------|---------|
| Arrival Time | When a process first arrives in the system |
| Burst Time | How long the process needs the CPU |
| Priority | Importance level (lower number = higher priority) |
| Time Quantum | Max time a process can run before being preempted (Round Robin) |
| Completion Time | When a process finishes |
| Turnaround Time | Completion − Arrival (total time in system) |
| Waiting Time | Turnaround − Burst (time spent waiting, not running) |
| Response Time | First run start − Arrival (how fast it gets the CPU) |

### FCFS — First Come First Serve

**What it does:** Processes run in the order they arrive. Like a queue at a store.

**When to use:** Simple systems where fairness by arrival order matters.

**Example:**
```
P1 arrives at 0, needs 8 units
P2 arrives at 1, needs 4 units
P3 arrives at 2, needs 9 units

Timeline:  [P1: 0-8] [P2: 8-12] [P3: 12-21]
```

**Results:**
- P1: Turnaround=8, Waiting=0, Response=0
- P2: Turnaround=11, Waiting=7, Response=7
- P3: Turnaround=19, Waiting=10, Response=10

**Pros:** Simple, fair by arrival
**Cons:** Convoy effect — a long process blocks short ones behind it

---

### SJF — Shortest Job First (Non-preemptive)

**What it does:** Among arrived processes, pick the one with the **shortest burst time**. Once started, it runs to completion.

**When to use:** When you know burst times in advance and want minimum average waiting time.

**Example:**
```
P1: arrival 0, burst 8
P2: arrival 1, burst 4
P3: arrival 2, burst 9

t=0: Only P1 → runs (8)
t=8: P2(4), P3(9) → P2 shortest → runs (4)
t=12: P3 → runs (9)

Timeline: [P1: 0-8] [P2: 8-12] [P3: 12-21]
```

**Pros:** Optimal average waiting time (non-preemptive)
**Cons:** Requires knowing burst times; long jobs can starve

---

### SRTF — Shortest Remaining Time First (Preemptive)

**What it does:** Like SJF, but **preemptive**. If a new process arrives with a shorter remaining time, the current process is paused.

**When to use:** When you want the absolute minimum average waiting time.

**Example:**
```
P1: arrival 0, burst 8
P2: arrival 1, burst 4
P3: arrival 2, burst 9

t=0: P1 starts (remaining=8)
t=1: P2 arrives, remaining=4 < 8 → preempt P1, run P2
t=2: P3 arrives, remaining=9 > P2(3) → P2 continues
t=5: P2 completes → P1(remaining=7) vs P3(9) → P1 runs
t=12: P1 completes → P3 runs
t=21: P3 completes

Timeline: [P1: 0-1] [P2: 1-5] [P1: 5-12] [P3: 12-21]
```

**Pros:** Optimal average waiting time
**Cons:** More context switches, requires remaining time estimation

---

### Priority Scheduling (Non-preemptive)

**What it does:** Higher priority (lower number) runs first. Once started, runs to completion.

**When to use:** When some processes are more important than others.

**Example:**
```
P1: priority 3
P2: priority 1
P3: priority 4
P4: priority 2

Order: P2(1) → P4(2) → P1(3) → P3(4)
```

**Pros:** Importance-based, simple
**Cons:** Low-priority processes may starve indefinitely

---

### Priority Scheduling (Preemptive)

**What it does:** Like priority, but **preemptive**. If a higher-priority process arrives, the current process is paused.

**When to use:** Real-time systems where urgent tasks must run immediately.

**Pros:** Responsive to high-priority tasks
**Cons:** Even more context switches

---

### Round Robin (RR)

**What it does:** Each process gets a fixed time slice (quantum). After the quantum, it goes to the back of the queue. New arrivals join the queue.

**When to use:** Time-sharing systems (like modern OS schedulers).

**Example (quantum=2):**
```
Ready queue: P1(8), P2(4), P3(9), P4(5)

Cycle 1: P1 runs 2 (rem=6) → queue: P2,P3,P4,P1
         P2 runs 2 (rem=2) → queue: P3,P4,P1,P2
         P3 runs 2 (rem=7) → queue: P4,P1,P2,P3
         P4 runs 2 (rem=3) → queue: P1,P2,P3,P4
Cycle 2: P1 runs 2 (rem=4) → ...
```

**Pros:** Fair, good response time, prevents starvation
**Cons:** Performance depends on quantum size
- Small quantum → high overhead from context switches
- Large quantum → approaches FCFS

**Tip:** Typical quantum is 10-100ms in real systems.

---

### How to Use in the App

1. Open **CPU Scheduler**
2. Add processes: PID, Arrival Time, Burst Time, Priority
3. Select algorithm from the list
4. If Round Robin, set Time Quantum
5. Click **Run Simulation**
6. Watch the Gantt chart animate
7. Read results in the table below

---

## 2. Deadlock Management — Banker's Algorithm

### The Problem

Multiple processes share resources. A deadlock occurs when processes wait for resources held by others, forming a cycle. Banker's Algorithm **prevents** deadlocks by only granting requests that keep the system in a **safe state**.

### Key Terms

| Term | Meaning |
|------|---------|
| Available | Free resource instances right now |
| Maximum | Max resources a process might ever need |
| Allocation | Resources currently held by a process |
| Need | Maximum − Allocation (what it still needs) |
| Safe State | There exists an order (safe sequence) where all processes can finish |
| Unsafe State | Might deadlock — not guaranteed to finish |

### Safety Algorithm

**What it does:** Determines if the system is in a safe state by finding a safe sequence.

**Steps:**
1. Start with Work = Available (free resources)
2. Find a process whose Need ≤ Work
3. Pretend it finishes: Work = Work + its Allocation
4. Mark it as finished, add to safe sequence
5. Repeat until no process can finish
6. If all finished → SAFE (with sequence). Otherwise → UNSAFE.

**Example:**
```
Available: [3, 3, 2]  (3 resource types)
P0: Need=[7,4,3], Alloc=[0,1,0]
P1: Need=[1,2,2], Alloc=[2,0,0]
P2: Need=[6,0,0], Alloc=[3,0,2]
P3: Need=[0,1,1], Alloc=[2,1,1]
P4: Need=[4,3,1], Alloc=[0,0,2]

Step 1: Work=[3,3,2]. P1 Need=[1,2,2] ≤ Work ✓ → Work=[5,3,2], seq=[P1]
Step 2: Work=[5,3,2]. P3 Need=[0,1,1] ≤ Work ✓ → Work=[7,4,3], seq=[P1,P3]
Step 3: Work=[7,4,3]. P4 Need=[4,3,1] ≤ Work ✓ → Work=[7,4,5], seq=[P1,P3,P4]
Step 4: Work=[7,4,5]. P0 Need=[7,4,3] ≤ Work ✓ → Work=[7,5,5], seq=[P1,P3,P4,P0]
Step 5: Work=[7,5,5]. P2 Need=[6,0,0] ≤ Work ✓ → Work=[10,5,7], seq=[P1,P3,P4,P0,P2]

SAFE! Sequence: P1 → P3 → P4 → P0 → P2
```

### Resource Request Algorithm

**What it does:** When a process requests resources, decide whether to grant.

**Steps:**
1. Check: Request ≤ Need (process can't request more than it declared)
2. Check: Request ≤ Available (enough free resources)
3. Pretend to grant: update Available, Allocation, Need
4. Run Safety Algorithm on new state
5. If SAFE → Grant (keep changes). If UNSAFE → Deny (revert).

**Important:** Unsafe ≠ Deadlock. Unsafe means "might deadlock depending on future requests." Deadlock is a confirmed cycle.

### How to Use in the App

1. Open **Deadlock Manager**
2. Set number of processes and resource types
3. Fill in Available, Maximum, and Allocation matrices
4. Need is calculated automatically
5. Click **Check Safety** to see if safe
6. Use the Request panel to test resource requests
7. Watch the visualization show allocation per process

---

## 3. Memory Management

### Paging & Address Translation

**What it does:** Splits logical (virtual) memory into fixed-size pages and physical memory into frames. A page table maps each page to a frame.

**Address Translation:**
```
Logical Address = Page Number × Page Size + Offset
Page Number = Logical Address / Page Size
Offset = Logical Address % Page Size
Physical Address = Frame Number × Page Size + Offset
```

**Example:**
- Logical memory: 64 KB, Physical: 32 KB, Page size: 4 KB
- Pages = 16, Frames = 8
- Address 100 → Page 0, Offset 100
- If Page 0 maps to Frame 2 → Physical = 2×4096 + 100 = 8292

### Page Replacement Algorithms

When a page is needed but not in memory (page fault), and no free frames exist, one page must be replaced.

#### FIFO — First In First Out
- Replace the page that has been in memory the longest
- Uses a queue to track order
- Simple but may replace frequently used pages

#### LRU — Least Recently Used
- Replace the page not accessed for the longest time
- Tracks last access time per page
- Better than FIFO, approximates optimal

#### Optimal (MIN)
- Replace the page used farthest in the future (or never used again)
- Requires knowing future references (theoretical)
- Provides the minimum possible page faults

**Metrics:** Page Faults, Page Hits, Fault Rate, Hit Rate

**Tip:** Optimal ≤ FIFO in faults. LRU is between them.

### Segmentation & Address Translation

**What it does:** Divides memory into variable-sized segments (code, data, stack, heap). Each segment has a base (start address) and limit (size).

**Address Translation:**
```
Logical Address = (Segment Number, Offset)
If Offset < Segment.Limit:
    Physical Address = Segment.Base + Offset
Else:
    Segmentation Fault (error)
```

**Example:**
```
Segment 0 (Code): Base=0, Limit=1024
Segment 1 (Data): Base=1024, Limit=2048
Address (1, 500) → 1024 + 500 = 1524 ✓
Address (0, 1500) → 1500 > 1024 → Segmentation Fault!
```

### Memory Fragmentation

#### Internal Fragmentation
- Wasted space **inside** an allocated block
- Example: 100-unit block allocated for 80-unit process → 20 wasted
- Common with fixed-size allocation (pages)

#### External Fragmentation
- Free memory scattered in small pieces
- Total free may be enough, but not contiguous
- Common with variable-size allocation (segments)

#### Allocation Algorithms

**First Fit:** Allocate the first free block that fits.
- Fast (stops at first fit)
- May create many small fragments at the start

**Best Fit:** Allocate the smallest free block that fits.
- Minimizes leftover fragment
- Searches all blocks, may leave tiny unusable pieces

**Worst Fit:** Allocate the largest free block.
- Leaves large remnants
- Counterintuitively sometimes better for future large requests

**Example:**
```
Free blocks: [100, 500, 200, 300, 400]
Request P1=212:
  First Fit: 500 block (first that fits)
  Best Fit: 300 block (smallest that fits)
  Worst Fit: 500 block (largest)
```

### How to Use in the App

1. Open **Memory Manager**
2. **Paging tab:** Set memory sizes, page size, edit page table, translate addresses
3. **Page Replacement tab:** Enter reference string, frames, select algorithm, run
4. **Segmentation tab:** Add segments, translate addresses, see memory map
5. **Fragmentation tab:** Add memory blocks and process requests, compare algorithms

---

## 4. Disk Scheduling

### The Problem

The disk head must move to different cylinders to service read/write requests. The order of servicing affects total head movement (seek time). Goal: minimize total movement.

### Key Terms

| Term | Meaning |
|------|---------|
| Initial Head | Starting position of disk head |
| Cylinder Range | Min and max cylinder numbers |
| Request Queue | List of cylinders to service |
| Seek Distance | |next cylinder − current| |
| Total Head Movement | Sum of all seek distances |

### FCFS — First Come First Serve
- Service requests in arrival order
- No optimization, baseline for comparison

### SSTF — Shortest Seek Time First
- Service the closest request to current head position
- Greedy: always pick nearest
- **Pros:** Low total movement
- **Cons:** Starvation for far requests

### SCAN — Elevator Algorithm
- Move in one direction, service all requests along the way
- At disk end, reverse direction
- **Pros:** Fair, no starvation
- **Cons:** Requests just behind the head wait longer

### C-SCAN — Circular SCAN
- Like SCAN but jump from end to start (circular)
- Only services in one direction
- **Pros:** More uniform wait times
- **Cons:** Jump distance counted as seek

### LOOK
- Like SCAN but reverse at last request, not disk end
- Slightly less movement than SCAN
- **Pros:** More efficient than SCAN

### C-LOOK
- Like C-SCAN but jump to first request
- Most practical for real systems
- **Pros:** Best balance of efficiency and fairness

### Example

```
Initial head: 50
Requests: [98, 183, 37, 122, 14, 124, 65, 67]
Range: 0-199

FCFS: 50→98→183→37→122→14→124→65→67 = 643
SSTF: 50→37→14→65→67→98→122→124→183 = 236
SCAN: 50→65→67→98→122→124→183→199→37→14 = 376
```

### How to Use in the App

1. Open **Disk Scheduler**
2. Set initial head, cylinder range, direction
3. Enter request queue (comma-separated)
4. Select algorithm
5. Click **Run Simulation**
6. Watch animated disk head movement
7. See total movement and per-step distances

---

## 5. Process Management

### Process States

```
        ┌──────────┐
        │   NEW    │  (being created)
        └────┬─────┘
             │ admitted
             ▼
        ┌──────────┐
   ┌───│  READY   │◄──┐
   │   └────┬─────┘   │
   │        │ dispatch │
   │        ▼          │
   │   ┌──────────┐   │
   │   │ RUNNING  │───┤ I/O request
   │   └────┬─────┘   │
   │        │          │
   │        │ exit     │ I/O complete
   │        ▼          │
   │   ┌──────────┐   │
   │   │TERMINATED│   │
   │   └──────────┘   │
   │                  │
   │   ┌──────────┐   │
   └──►│ WAITING  │───┘
       └──────────┘
```

| State | Meaning |
|-------|---------|
| NEW | Process being created, PCB allocated |
| READY | In memory, waiting for CPU |
| RUNNING | Currently executing on CPU |
| WAITING | Blocked for I/O or event |
| TERMINATED | Finished, resources released |

### Multiprogramming (Single CPU)

**What it does:** Multiple processes coexist in memory. One CPU switches between them (Round Robin with I/O). While one process waits for I/O, another uses the CPU.

**Key insight:** I/O and CPU work overlap → better CPU utilization.

**Degree of Multiprogramming:** Max processes in memory simultaneously.

### Multiprocessing (Multi-Core)

**What it does:** Multiple CPUs (cores) execute processes simultaneously. Shared ready queue, each core has its own scheduler.

**Concurrency vs Parallelism:**
- **Concurrency:** Interleaved execution on single CPU (one at a time, switching fast)
- **Parallelism:** True simultaneous execution on multiple cores

### How to Use in the App

1. Open **Process Manager**
2. **Multiprogramming tab:** Add processes (PID, arrival, burst, I/O freq, priority), set time slice, run
3. **Multiprocessing tab:** Same but also set number of cores
4. **State Transitions tab:** See the process state diagram
5. Watch per-core timelines and metrics

---

## 6. System Monitor

### What it Shows

- **Process counts:** Total, Running, Ready, Waiting, Terminated
- **CPU utilization:** Percentage of time CPU is busy
- **Memory usage:** Used vs total (MB)
- **Available resources:** Free instances per resource type
- **Live charts:** CPU and memory over last 60 seconds

### Important

All data in System Monitor comes from **actual simulation state**, not fabricated statistics. When you run simulations in other modules, their results feed into the monitor.

---

## Quick Reference: How to Run Each Simulation

| Module | Steps |
|--------|-------|
| **CPU Scheduler** | Add processes → Select algorithm → Run → Watch Gantt chart |
| **Deadlock Manager** | Set dimensions → Fill matrices → Check Safety → Test requests |
| **Memory Manager** | Paging: configure → translate addresses. Replacement: string + frames → run. Segmentation: add segments → translate. Fragmentation: blocks + requests → run |
| **Disk Scheduler** | Set head, range, requests → Select algorithm → Run → Watch animation |
| **Process Manager** | Add processes → Set params → Run → Watch timelines |
| **System Monitor** | Auto-updates with simulated system activity |

---

## Tips for Understanding Results

1. **Lower waiting time is better** for scheduling
2. **Fewer page faults is better** for replacement
3. **Less head movement is better** for disk scheduling
4. **Higher CPU utilization is better** for process management
5. **Safe state is better** for deadlock (but unsafe ≠ deadlock)
6. **Compare algorithms** using the "Compare All" buttons to see trade-offs

---

## Common Mistakes to Avoid

1. **Round Robin with quantum too small** → excessive context switches
2. **SJF requires knowing burst times** → not always possible in real life
3. **Banker's unsafe ≠ deadlock** → it's a warning, not a confirmation
4. **Optimal page replacement is theoretical** → can't be implemented in real systems
5. **First Fit vs Best Fit** → no single winner, depends on workload
6. **More cores ≠ always faster** → depends on process count and I/O

# Algorithm Documentation

## CPU Scheduling Algorithms

### First Come First Serve (FCFS)

**Description**: Processes are executed in order of arrival. Non-preemptive.

**Algorithm**:
1. Sort processes by arrival time (then PID for ties)
2. For each process:
   - If CPU idle before arrival, advance time
   - Execute process to completion
   - Record completion time

**Complexity**: O(n log n) for sorting, O(n) for execution

**Example**:
```
Processes: P1(0,8), P2(1,4), P3(2,9), P4(3,5)
Gantt: | P1(0-8) | P2(8-12) | P3(12-21) | P4(21-26) |
```

**Metrics**:
- Simple but can cause convoy effect
- High average waiting time for short processes behind long ones

---

### Shortest Job First (SJF) - Non-preemptive

**Description**: Shortest burst time process runs next. Non-preemptive.

**Algorithm**:
1. At each scheduling point, select arrived process with shortest burst
2. Execute to completion
3. If no process arrived, jump to next arrival

**Complexity**: O(n²) worst case (repeated sorting)

**Example**:
```
At t=0: Only P1 → runs
At t=8: P2(4), P3(9), P4(5) → P2 shortest → runs
At t=12: P4(5), P3(9) → P4 → runs
```

**Metrics**:
- Optimal for minimum average waiting time (non-preemptive)
- Requires burst time prediction
- Can cause starvation for long processes

---

### Shortest Remaining Time First (SRTF) - Preemptive

**Description**: Preemptive version of SJF. Process with shortest remaining time runs.

**Algorithm**:
1. At each time unit/event:
   - Check for new arrivals
   - If new process has shorter remaining time, preempt current
   - Execute current process until next event (arrival or completion)

**Complexity**: O(n × t) where t is time units, or O(n² log n) with priority queue

**Example**:
```
t=0: P1(8) starts
t=1: P2(4) arrives, 4<7 → preempt, P2 runs
t=5: P2 completes, P4(5) < P1(7) < P3(9) → P4 runs
```

**Metrics**:
- Optimal for minimum average waiting time
- More context switches than SJF
- Requires remaining time estimation

---

### Priority Scheduling (Non-preemptive)

**Description**: Higher priority (lower number) runs first. Non-preemptive.

**Algorithm**:
1. At each scheduling point, select highest priority arrived process
2. Tie-break: arrival time, then PID
3. Execute to completion

**Complexity**: O(n²) worst case

**Note**: Lower priority number = higher priority (e.g., 1 > 2 > 3)

**Example**:
```
P1(pri=3), P2(pri=1), P3(pri=4), P4(pri=2)
Order: P1 → P2 → P4 → P3
```

**Metrics**:
- Good for importance-based scheduling
- Starvation risk for low priority
- Aging can prevent starvation

---

### Priority Scheduling (Preemptive)

**Description**: Preemptive priority. Running process preempted if higher priority arrives.

**Algorithm**:
1. Similar to SRTF but compares priority instead of remaining time
2. Preempt when new process has higher priority (lower number)

**Complexity**: O(n × t) or O(n² log n)

---

### Round Robin (RR)

**Description**: Each process gets fixed time quantum. Preemptive.

**Algorithm**:
1. Maintain ready queue (FIFO)
2. Dispatch front process for time quantum
3. If completes, remove; else add to back of queue
4. New arrivals added to back of queue

**Complexity**: O(total_time / quantum)

**Example** (quantum=2):
```
Ready: P1(8), P2(4), P3(9), P4(5)
P1: 2 → rem=6 → queue: P2,P3,P4,P1
P2: 2 → rem=2 → queue: P3,P4,P1,P2
P3: 2 → rem=7 → queue: P4,P1,P2,P3
...
```

**Metrics**:
- Fair, good response time
- Performance depends on quantum size
- Small quantum → high overhead, large → approaches FCFS
- Typical quantum: 10-100ms

---

### Metrics Calculations

For all algorithms:
- **Completion Time (CT)**: When process finishes
- **Turnaround Time (TAT)**: CT - Arrival Time
- **Waiting Time (WT)**: TAT - Burst Time
- **Response Time (RT)**: First Run Start - Arrival Time
- **CPU Utilization**: (Total Busy Time / Total Time) × 100%
- **Throughput**: Processes Completed / Total Time
- **Context Switches**: Number of process switches

---

## Deadlock Management: Banker's Algorithm

### Data Structures

- **Available[m]**: Available instances of each resource type
- **Max[n][m]**: Maximum demand of each process
- **Allocation[n][m]**: Currently allocated to each process
- **Need[n][m]**: Max - Allocation (remaining need)

Where n = processes, m = resource types

### Safety Algorithm

Determines if system is in a safe state.

```
Work = Available
Finish[i] = false for all i

Repeat:
    Find i where Finish[i] = false and Need[i] ≤ Work
    If found:
        Work = Work + Allocation[i]
        Finish[i] = true
    Else:
        break

If all Finish[i] = true → SAFE
Safe sequence = order of Finish becoming true
```

**Example** (Classic):
```
Available: [3,3,2]
Processes: P0[7,5,3], P1[3,2,2], P2[9,0,2], P3[2,2,2], P4[4,3,3]
Alloc:     P0[0,1,0], P1[2,0,0], P2[3,0,2], P3[2,1,1], P4[0,0,2]
Need:      P0[7,4,3], P1[1,2,2], P2[6,0,0], P3[0,1,1], P4[4,3,1]

Safe sequence: P1, P3, P4, P0, P2
```

**Key Point**: Safe state ≠ no deadlock. Safe = ∃ sequence where all complete.
Unsafe = may deadlock depending on future requests.

### Resource Request Algorithm

When process requests resources:

```
Request[i] = requested resources

1. If Request[i] > Need[i] → ERROR (exceeds maximum)
2. If Request[i] > Available → WAIT (not enough resources)
3. Pretend allocation:
   Available = Available - Request[i]
   Allocation[i] = Allocation[i] + Request[i]
   Need[i] = Need[i] - Request[i]
4. Run Safety Algorithm on new state
5. If SAFE → GRANT, keep changes
6. If UNSAFE → DENY, revert changes, process waits
```

---

## Memory Management

### Paging

**Concept**: Logical memory divided into fixed-size pages, physical into frames.

**Address Translation**:
```
Logical Address = (Page Number, Offset)
Page Number = Address / Page Size
Offset = Address % Page Size
Physical Address = Frame Number × Page Size + Offset
```

**Page Table**: Maps page → frame with valid bit.

**Example**:
- Logical: 64KB, Physical: 32KB, Page: 4KB
- Pages: 16, Frames: 8
- Address 100 → Page 0, Offset 100 → Frame 2 → Physical 8292

---

### Page Replacement Algorithms

When page fault occurs and no free frames:

#### FIFO (First In First Out)
- Replace oldest page in memory
- Queue tracks page order
- **Belady's Anomaly**: More frames can increase faults

#### LRU (Least Recently Used)
- Replace page not used for longest time
- Track last access time per page
- Approximates optimal but implementable

#### Optimal (MIN)
- Replace page used farthest in future (or never)
- Requires future knowledge (theoretical)
- Lower bound on page faults

**Metrics**:
- Page Fault Rate = Faults / Total References
- Hit Rate = 1 - Fault Rate

---

### Segmentation

**Concept**: Memory divided into variable-sized segments (code, data, stack, heap).

**Address**: (Segment Number, Offset)

**Translation**:
```
Segment Table: Base + Limit per segment
If Offset < Limit:
    Physical = Base + Offset
Else:
    Segmentation Fault
```

**Advantages**:
- Matches program structure
- Sharing by segment
- Protection per segment

**Disadvantages**:
- External fragmentation
- Variable allocation complexity

---

### Memory Fragmentation

#### Internal Fragmentation
- Wasted space within allocated blocks
- Fixed-size allocation (pages) → last page partially used
- Segmentation: minimal if exact fit

#### External Fragmentation
- Free memory scattered in small blocks
- Total free sufficient but not contiguous
- Compaction needed (requires relocation)

#### Allocation Algorithms

**First Fit**: First block that fits
- Fast, leaves large blocks at end
- May create many small fragments at start

**Best Fit**: Smallest block that fits
- Minimizes leftover fragment
- Searches all blocks, leaves tiny unusable fragments

**Worst Fit**: Largest block
- Leaves large remnants
- Intuitively bad, sometimes better for future large requests

---

## Disk Scheduling

**Goal**: Minimize total head movement (seek time)

### FCFS
- Service in arrival order
- No optimization, baseline

### SSTF (Shortest Seek Time First)
- Service closest request
- Greedy, may cause starvation for far requests

### SCAN (Elevator)
- Move in one direction, serve requests
- At end, reverse direction
- Serves all requests in path

### C-SCAN (Circular SCAN)
- Like SCAN but jump from end to start
- More uniform wait times
- Only serves in one direction

### LOOK
- Like SCAN but reverse at last request, not disk end
- Slightly less movement than SCAN

### C-LOOK
- Like C-SCAN but jump to first request
- Most practical for real systems

**Metrics**:
- Total Head Movement = Σ |next - current|
- Average Seek = Total / Requests

---

## Process Management

### Process States

```
NEW → READY → RUNNING → TERMINATED
            ↑    ↓
            └ WAITING (I/O)
```

**Transitions**:
- **NEW → READY**: Process admitted, loaded to memory
- **READY → RUNNING**: Scheduler dispatches
- **RUNNING → READY**: Time slice expired / Preempted
- **RUNNING → WAITING**: I/O request / Event wait
- **WAITING → READY**: I/O complete / Event signaled
- **RUNNING → TERMINATED**: Process exits

### Multiprogramming (Single CPU)

- Multiple processes in memory
- CPU switches between them (Round Robin)
- I/O overlaps with CPU execution
- **Degree of Multiprogramming**: Max processes in memory simultaneously

### Multiprocessing (Multi-Core)

- Multiple CPUs execute simultaneously
- Shared ready queue
- Each core runs independent scheduler
- **Parallelism**: True simultaneous execution
- **Concurrency**: Interleaved execution (single CPU)

**Metrics per Core**:
- Utilization, Throughput, Turnaround, Waiting, Response

---

## Complexity Summary

| Algorithm | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| FCFS | O(n log n) | O(n) |
| SJF | O(n²) | O(n) |
| SRTF | O(n × t) or O(n² log n) | O(n) |
| Priority NP | O(n²) | O(n) |
| Priority P | O(n × t) or O(n² log n) | O(n) |
| Round Robin | O(t/q) | O(n) |
| Banker's Safety | O(n²m) | O(nm) |
| Banker's Request | O(n²m) | O(nm) |
| FIFO Replacement | O(r) | O(f) |
| LRU Replacement | O(r) | O(f) |
| Optimal Replacement | O(r × f) | O(f) |
| Fragmentation | O(p × b) | O(b) |
| Disk Scheduling | O(r²) or O(r log r) | O(r) |
| Multiprogramming | O(t/q × n) | O(n) |
| Multiprocessing | O(t/q × n) | O(n + c) |

Where:
- n = processes, m = resource types, f = frames, r = requests
- t = total time, q = quantum, p = process requests, b = blocks
- c = cores

---

## References

1. Silberschatz, Galvin, Gagne - "Operating System Concepts"
2. Tanenbaum, Bos - "Modern Operating Systems"
3. Stallings - "Operating Systems: Internals and Design Principles"
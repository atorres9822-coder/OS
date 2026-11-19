"""
Process Manager - Multiprogramming and Multiprocessing Simulation.

Simulates process state transitions, multiprogramming, and multiprocessing.
Supports multiple CPU scheduling algorithms: FCFS, SJF, SRTF, Priority (NP/P), Round Robin.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from copy import deepcopy
import random


class ProcessState(Enum):
    NEW = "new"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"  # Blocked for I/O
    TERMINATED = "terminated"


class TransitionReason(Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    IO_REQUEST = "io_request"
    IO_COMPLETE = "io_complete"
    TIMEOUT = "timeout"
    TERMINATED = "terminated"
    PREEMPTED = "preempted"


class SchedulingAlgorithm(Enum):
    FCFS = "fcfs"
    SJF = "sjf"
    SRTF = "srtf"
    PRIORITY_NP = "priority_np"   # Non-preemptive priority
    PRIORITY_P = "priority_p"     # Preemptive priority
    ROUND_ROBIN = "round_robin"


@dataclass
class SimulatedProcess:
    """Process in the simulation."""
    pid: str
    arrival_time: float
    burst_time: float
    io_frequency: float = 0.0  # Cumulative CPU burst between I/O requests (0 = never)
    priority: int = 0           # Lower number = higher priority

    # Dynamic state
    state: ProcessState = ProcessState.NEW
    remaining_time: float = 0.0
    cpu_time_used: float = 0.0      # Total CPU time consumed
    cpu_since_io: float = 0.0       # CPU time since last I/O (for I/O frequency)
    io_time_remaining: float = 0.0
    start_time: float = -1.0
    completion_time: float = 0.0
    turnaround_time: float = 0.0
    waiting_time: float = 0.0       # Turnaround - Total Burst (includes I/O wait per classic definition)
    response_time: float = 0.0      # First CPU start - Arrival
    core_id: int = -1               # Which core it's running on (-1 = none)

    # For visualization
    state_history: List[Tuple[float, ProcessState, str]] = field(default_factory=list)

    def __post_init__(self):
        self.remaining_time = self.burst_time
        # Record initial state
        self.state_history.append((self.arrival_time, ProcessState.NEW, "initialized"))

    def record_state_change(self, time: float, new_state: ProcessState, reason: str):
        self.state_history.append((time, new_state, reason))
        self.state = new_state


@dataclass
class CPUScheduleEvent:
    """Event in CPU schedule."""
    time: float
    event_type: str  # "start", "preempt", "io", "io_complete", "complete"
    process_id: str
    core_id: int
    details: str


@dataclass
class MultiprogrammingResult:
    """Result of multiprogramming simulation."""
    processes: List[SimulatedProcess]
    schedule: List[CPUScheduleEvent]
    cpu_utilization: float
    throughput: float
    avg_turnaround: float
    avg_waiting: float
    avg_response: float
    context_switches: int
    total_time: float
    degree_of_multiprogramming: int  # Max processes in memory at once
    algorithm: str


@dataclass
class MultiprocessingResult:
    """Result of multiprocessing simulation."""
    processes: List[SimulatedProcess]
    core_schedules: Dict[int, List[CPUScheduleEvent]]  # Per-core schedule
    core_utilizations: Dict[int, float]
    total_time: float
    overall_cpu_utilization: float
    throughput: float
    avg_turnaround: float
    avg_waiting: float
    avg_response: float


class ProcessManager:
    """Process management simulation."""

    @staticmethod
    def simulate_multiprogramming(
        processes: List[SimulatedProcess],
        algorithm: SchedulingAlgorithm = SchedulingAlgorithm.ROUND_ROBIN,
        time_slice: float = 2.0,
        max_time: float = 1000.0
    ) -> MultiprogrammingResult:
        """
        Simulate multiprogramming on a single CPU with configurable scheduling algorithm.

        Context switch convention:
        A context switch is counted only when the CPU switches from one distinct PID
        to a different PID (or from idle to a process). If the same process continues
        running (e.g., same process re-dispatched after time slice with no other
        ready process), no context switch is counted.

        I/O frequency:
        I/O is triggered after cumulative CPU burst time since last I/O reaches
        io_frequency. A value of 0 disables I/O completely.

        Waiting time:
        Turnaround Time - Total Burst Time (classic OS definition).
        """
        # Copy processes
        procs = [deepcopy(p) for p in processes]
        procs.sort(key=lambda p: (p.arrival_time, p.pid))

        schedule = []
        current_time = 0.0
        ready_queue = []
        running_proc = None
        completed = []
        context_switches = 0
        last_pid = None  # Track last PID that ran for context switch counting
        max_in_memory = 0

        # Track I/O completions
        io_events = []  # (completion_time, process)

        process_idx = 0
        n_procs = len(procs)

        def select_from_ready(queue: List[SimulatedProcess]) -> Optional[SimulatedProcess]:
            """Select the next process from the ready queue based on algorithm."""
            if not queue:
                return None
            if algorithm == SchedulingAlgorithm.FCFS:
                # Already in arrival order
                return queue[0]
            elif algorithm == SchedulingAlgorithm.SJF:
                # Shortest burst time first
                return min(queue, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
            elif algorithm == SchedulingAlgorithm.PRIORITY_NP:
                # Highest priority first (lower number = higher priority)
                return min(queue, key=lambda p: (p.priority, p.arrival_time, p.pid))
            elif algorithm == SchedulingAlgorithm.SRTF:
                # Shortest remaining time first
                return min(queue, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
            elif algorithm == SchedulingAlgorithm.PRIORITY_P:
                # Highest priority first (preemptive)
                return min(queue, key=lambda p: (p.priority, p.arrival_time, p.pid))
            elif algorithm == SchedulingAlgorithm.ROUND_ROBIN:
                # FIFO order
                return queue[0]
            return queue[0]

        def remove_from_ready(queue: List[SimulatedProcess], proc: SimulatedProcess):
            """Remove a specific process from the ready queue."""
            for i, p in enumerate(queue):
                if p.pid == proc.pid:
                    queue.pop(i)
                    return

        def should_preempt(running: SimulatedProcess, candidate: SimulatedProcess) -> bool:
            """Check if a candidate process should preempt the running process."""
            if algorithm == SchedulingAlgorithm.SRTF:
                return candidate.remaining_time < running.remaining_time
            elif algorithm == SchedulingAlgorithm.PRIORITY_P:
                return candidate.priority < running.priority
            return False

        while len(completed) < n_procs and current_time < max_time:
            # 1. Process arrivals at current_time
            while process_idx < n_procs and procs[process_idx].arrival_time <= current_time:
                proc = procs[process_idx]
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.CREATED.value)
                ready_queue.append(proc)
                process_idx += 1

            # 2. Process I/O completions at current_time
            io_events.sort(key=lambda x: x[0])
            while io_events and io_events[0][0] <= current_time:
                _, proc = io_events.pop(0)
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.IO_COMPLETE.value)
                ready_queue.append(proc)

            # 3. Update max multiprogramming degree
            in_memory = len([p for p in procs if p.state != ProcessState.NEW and p.state != ProcessState.TERMINATED])
            max_in_memory = max(max_in_memory, in_memory)

            # 4. Check for preemption (preemptive algorithms only)
            if running_proc is not None and algorithm in (SchedulingAlgorithm.SRTF, SchedulingAlgorithm.PRIORITY_P):
                candidate = select_from_ready(ready_queue)
                if candidate is not None and should_preempt(running_proc, candidate):
                    # Preempt running process
                    running_proc.record_state_change(current_time, ProcessState.READY, TransitionReason.PREEMPTED.value)
                    remove_from_ready(ready_queue, candidate)
                    ready_queue.append(running_proc)
                    # Re-sort ready queue for preemptive algorithms
                    if algorithm == SchedulingAlgorithm.SRTF:
                        ready_queue.sort(key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
                    elif algorithm == SchedulingAlgorithm.PRIORITY_P:
                        ready_queue.sort(key=lambda p: (p.priority, p.arrival_time, p.pid))

                    # Context switch: different PID
                    if last_pid is not None and last_pid != candidate.pid:
                        context_switches += 1
                    last_pid = candidate.pid

                    running_proc = candidate
                    if running_proc.start_time < 0:
                        running_proc.start_time = current_time
                        running_proc.response_time = current_time - running_proc.arrival_time

                    running_proc.record_state_change(current_time, ProcessState.RUNNING, TransitionReason.SCHEDULED.value)
                    running_proc.core_id = 0

                    schedule.append(CPUScheduleEvent(
                        time=current_time,
                        event_type="preempt",
                        process_id=running_proc.pid,
                        core_id=0,
                        details=f"Preempted by {candidate.pid}"
                    ))

            # 5. If CPU free, schedule next process
            if running_proc is None and ready_queue:
                selected = select_from_ready(ready_queue)
                remove_from_ready(ready_queue, selected)
                running_proc = selected

                # Context switch: from idle or different PID
                if last_pid is None or last_pid != running_proc.pid:
                    context_switches += 1
                last_pid = running_proc.pid

                if running_proc.start_time < 0:
                    running_proc.start_time = current_time
                    running_proc.response_time = current_time - running_proc.arrival_time

                running_proc.record_state_change(current_time, ProcessState.RUNNING, TransitionReason.SCHEDULED.value)
                running_proc.core_id = 0

                schedule.append(CPUScheduleEvent(
                    time=current_time,
                    event_type="start",
                    process_id=running_proc.pid,
                    core_id=0,
                    details=f"Started on CPU"
                ))

            # 6. If still CPU idle, advance to next event
            if running_proc is None:
                next_event_time = max_time
                if process_idx < n_procs:
                    next_event_time = min(next_event_time, procs[process_idx].arrival_time)
                if io_events:
                    next_event_time = min(next_event_time, io_events[0][0])

                if next_event_time == current_time:
                    break  # Avoid infinite loop

                if next_event_time >= max_time:
                    break

                current_time = next_event_time
                continue

            # 7. Determine run duration
            if algorithm == SchedulingAlgorithm.ROUND_ROBIN:
                run_time = min(time_slice, running_proc.remaining_time)
            else:
                # Non-RR algorithms: run until completion, preemption, or I/O
                run_time = running_proc.remaining_time

            # Cap run_time at next arrival (if an arrival happens before time slice ends)
            if process_idx < n_procs:
                time_to_next_arrival = procs[process_idx].arrival_time - current_time
                if time_to_next_arrival > 0:
                    run_time = min(run_time, time_to_next_arrival)

            # Cap run_time at next I/O completion
            if io_events:
                time_to_next_io = io_events[0][0] - current_time
                if time_to_next_io > 0:
                    run_time = min(run_time, time_to_next_io)

            # 8. Check if I/O should occur during this run
            if running_proc.io_frequency > 0:
                if running_proc.cpu_since_io + run_time >= running_proc.io_frequency:
                    # I/O will trigger during this run
                    cpu_before_io = running_proc.io_frequency - running_proc.cpu_since_io
                    if cpu_before_io > 0:
                        run_time = cpu_before_io
                    else:
                        # I/O triggers immediately (edge case)
                        run_time = 0.001

            # 9. Execute the run
            if run_time <= 0:
                # Safety: advance minimally
                current_time += 0.001
                continue

            current_time += run_time
            running_proc.remaining_time -= run_time
            running_proc.cpu_time_used += run_time
            running_proc.cpu_since_io += run_time

            # 10. Check process completion
            if running_proc.remaining_time <= 0.001:
                running_proc.completion_time = current_time
                running_proc.turnaround_time = current_time - running_proc.arrival_time
                running_proc.waiting_time = running_proc.turnaround_time - running_proc.burst_time

                running_proc.record_state_change(current_time, ProcessState.TERMINATED, TransitionReason.TERMINATED.value)

                schedule.append(CPUScheduleEvent(
                    time=current_time,
                    event_type="complete",
                    process_id=running_proc.pid,
                    core_id=0,
                    details="Process terminated"
                ))

                completed.append(running_proc)
                # Context switch: process ends (different PID or idle next)
                if last_pid is not None and last_pid != running_proc.pid:
                    context_switches += 1
                last_pid = None
                running_proc = None
                continue

            # 11. Check I/O trigger
            if running_proc.io_frequency > 0 and running_proc.cpu_since_io >= running_proc.io_frequency:
                running_proc.cpu_since_io = 0.0
                io_time = random.uniform(0.5, 3.0)
                io_completion = current_time + io_time

                running_proc.record_state_change(
                    current_time, ProcessState.WAITING, TransitionReason.IO_REQUEST.value
                )

                schedule.append(CPUScheduleEvent(
                    time=current_time,
                    event_type="io",
                    process_id=running_proc.pid,
                    core_id=0,
                    details=f"I/O request (duration: {io_time:.1f})"
                ))

                io_events.append((io_completion, running_proc))
                # Context switch: process goes to I/O
                if last_pid is not None and last_pid != running_proc.pid:
                    context_switches += 1
                last_pid = None
                running_proc = None
                continue

            # 12. Check time slice expiration (RR only)
            if algorithm == SchedulingAlgorithm.ROUND_ROBIN and run_time >= time_slice - 0.001:
                # If no other processes are waiting, same process continues
                # without any context switch or redundant preempt/start events
                if len(ready_queue) == 0:
                    running_proc.record_state_change(current_time, ProcessState.RUNNING, TransitionReason.SCHEDULED.value)
                    schedule.append(CPUScheduleEvent(
                        time=current_time,
                        event_type="start",
                        process_id=running_proc.pid,
                        core_id=0,
                        details=f"Continued after time slice ({time_slice})"
                    ))
                    # running_proc continues, no context switch, no last_pid change
                else:
                    # Other processes waiting - preempt current process
                    running_proc.record_state_change(current_time, ProcessState.READY, TransitionReason.TIMEOUT.value)
                    ready_queue.append(running_proc)

                    if last_pid is not None and last_pid != running_proc.pid:
                        context_switches += 1

                    schedule.append(CPUScheduleEvent(
                        time=current_time,
                        event_type="preempt",
                        process_id=running_proc.pid,
                        core_id=0,
                        details=f"Time slice expired ({time_slice})"
                    ))

                    running_proc = None

        # Calculate metrics
        total_time = current_time
        execution_time = sum(p.cpu_time_used for p in procs)
        cpu_util = (execution_time / total_time * 100) if total_time > 0 else 0
        throughput = len(completed) / total_time if total_time > 0 else 0

        avg_turnaround = sum(p.turnaround_time for p in completed) / len(completed) if completed else 0
        avg_waiting = sum(p.waiting_time for p in completed) / len(completed) if completed else 0
        avg_response = sum(p.response_time for p in completed) / len(completed) if completed else 0

        return MultiprogrammingResult(
            processes=procs,
            schedule=schedule,
            cpu_utilization=cpu_util,
            throughput=throughput,
            avg_turnaround=avg_turnaround,
            avg_waiting=avg_waiting,
            avg_response=avg_response,
            context_switches=context_switches,
            total_time=total_time,
            degree_of_multiprogramming=max_in_memory,
            algorithm=algorithm.value
        )

    @staticmethod
    def simulate_multiprocessing(
        processes: List[SimulatedProcess],
        num_cores: int = 2,
        time_slice: float = 2.0,
        max_time: float = 1000.0
    ) -> MultiprocessingResult:
        """
        Simulate multiprocessing on multiple CPUs.

        Each core runs independently with shared ready queue.
        Uses Round Robin scheduling per core.
        """
        procs = [deepcopy(p) for p in processes]
        procs.sort(key=lambda p: (p.arrival_time, p.pid))

        # Per-core state
        core_running = [None] * num_cores
        core_schedules = {i: [] for i in range(num_cores)}
        core_busy_time = [0.0] * num_cores

        ready_queue = []
        io_events = []  # (completion_time, process)
        completed = []
        process_idx = 0
        n_procs = len(procs)
        current_time = 0.0
        context_switches = 0
        last_pid_per_core = {i: None for i in range(num_cores)}

        # Waiting time tracking
        waiting_accum = {p.pid: 0.0 for p in procs}
        last_ready_time = {}

        def add_waiting(pid: str, up_to_time: float):
            if pid in last_ready_time:
                waiting_accum[pid] += up_to_time - last_ready_time[pid]
                del last_ready_time[pid]

        def set_ready(pid: str, at_time: float):
            last_ready_time[pid] = at_time

        while len(completed) < n_procs and current_time < max_time:
            # Process arrivals
            while process_idx < n_procs and procs[process_idx].arrival_time <= current_time:
                proc = procs[process_idx]
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.CREATED.value)
                ready_queue.append(proc)
                set_ready(proc.pid, current_time)
                process_idx += 1

            # I/O completions
            io_events.sort(key=lambda x: x[0])
            while io_events and io_events[0][0] <= current_time:
                _, proc = io_events.pop(0)
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.IO_COMPLETE.value)
                ready_queue.append(proc)
                set_ready(proc.pid, current_time)

            # Schedule on free cores (Round Robin/FIFO)
            for core_id in range(num_cores):
                if core_running[core_id] is None and ready_queue:
                    proc = ready_queue.pop(0)
                    if proc.start_time < 0:
                        proc.start_time = current_time
                        proc.response_time = current_time - proc.arrival_time

                    proc.record_state_change(current_time, ProcessState.RUNNING, TransitionReason.SCHEDULED.value)
                    proc.core_id = core_id
                    core_running[core_id] = proc

                    # Context switch
                    if last_pid_per_core[core_id] is None or last_pid_per_core[core_id] != proc.pid:
                        context_switches += 1
                    last_pid_per_core[core_id] = proc.pid

                    add_waiting(proc.pid, current_time)

                    core_schedules[core_id].append(CPUScheduleEvent(
                        time=current_time,
                        event_type="start",
                        process_id=proc.pid,
                        core_id=core_id,
                        details=f"Started on Core {core_id}"
                    ))

            # Check if all cores idle and no pending events
            if all(c is None for c in core_running) and not ready_queue:
                next_event = max_time
                if process_idx < n_procs:
                    next_event = min(next_event, procs[process_idx].arrival_time)
                if io_events:
                    next_event = min(next_event, io_events[0][0])

                if next_event == current_time or next_event == max_time:
                    break
                current_time = next_event
                continue

            # Find next event time
            next_times = []

            # Time slice for each running process
            for core_id, proc in enumerate(core_running):
                if proc:
                    run_time = min(time_slice, proc.remaining_time)
                    next_times.append(current_time + run_time)

            # I/O events
            for io_time, _ in io_events:
                next_times.append(io_time)

            # Process arrivals
            if process_idx < n_procs:
                next_times.append(procs[process_idx].arrival_time)

            if not next_times:
                break

            next_time = min(next_times)
            delta = next_time - current_time

            # Advance running processes
            for core_id, proc in enumerate(core_running):
                if proc:
                    proc.cpu_time_used += delta
                    proc.remaining_time -= delta
                    core_busy_time[core_id] += delta
                    proc.cpu_since_io += delta

                    # Check I/O trigger
                    if proc.io_frequency > 0 and proc.cpu_since_io >= proc.io_frequency:
                        proc.cpu_since_io = 0.0
                        io_time = random.uniform(0.5, 3.0)
                        io_completion = current_time + io_time

                        proc.record_state_change(current_time, ProcessState.WAITING, TransitionReason.IO_REQUEST.value)

                        core_schedules[core_id].append(CPUScheduleEvent(
                            time=current_time, event_type="io",
                            process_id=proc.pid, core_id=core_id,
                            details=f"I/O request ({io_time:.1f})"
                        ))
                        io_events.append((io_completion, proc))
                        # Context switch
                        if last_pid_per_core[core_id] is not None and last_pid_per_core[core_id] != proc.pid:
                            context_switches += 1
                        last_pid_per_core[core_id] = None
                        core_running[core_id] = None

            current_time = next_time

            # Handle time slice expiration
            for core_id in range(num_cores):
                proc = core_running[core_id]
                if proc is None:
                    continue
                if proc.remaining_time <= 0.001:
                    # Completed
                    proc.completion_time = current_time
                    proc.turnaround_time = current_time - proc.arrival_time
                    proc.waiting_time = waiting_accum.get(proc.pid, 0.0)

                    proc.record_state_change(current_time, ProcessState.TERMINATED, TransitionReason.TERMINATED.value)

                    core_schedules[core_id].append(CPUScheduleEvent(
                        time=current_time, event_type="complete",
                        process_id=proc.pid, core_id=core_id, details="Terminated"
                    ))

                    completed.append(proc)
                    # Context switch
                    if last_pid_per_core[core_id] is not None and last_pid_per_core[core_id] != proc.pid:
                        context_switches += 1
                    last_pid_per_core[core_id] = None
                    core_running[core_id] = None
                elif abs(proc.cpu_time_used % time_slice) < 0.001 and proc.remaining_time > 0:
                    # Time slice expired
                    add_waiting(proc.pid, current_time)
                    proc.record_state_change(current_time, ProcessState.READY, TransitionReason.TIMEOUT.value)
                    ready_queue.append(proc)

                    # Context switch: only if different PID
                    if last_pid_per_core[core_id] is not None and last_pid_per_core[core_id] != proc.pid:
                        context_switches += 1
                    last_pid_per_core[core_id] = None
                    core_running[core_id] = None

                    core_schedules[core_id].append(CPUScheduleEvent(
                        time=current_time, event_type="preempt",
                        process_id=proc.pid, core_id=core_id,
                        details=f"Time slice expired"
                    ))

        # Calculate metrics
        total_time = current_time
        core_utils = {}
        for i in range(num_cores):
            core_utils[i] = (core_busy_time[i] / total_time * 100) if total_time > 0 else 0

        overall_busy = sum(core_busy_time)
        overall_util = (overall_busy / (total_time * num_cores) * 100) if total_time > 0 else 0
        throughput = len(completed) / total_time if total_time > 0 else 0

        avg_turnaround = sum(p.turnaround_time for p in completed) / len(completed) if completed else 0
        avg_waiting = sum(p.waiting_time for p in completed) / len(completed) if completed else 0
        avg_response = sum(p.response_time for p in completed) / len(completed) if completed else 0

        return MultiprocessingResult(
            processes=procs,
            core_schedules=core_schedules,
            core_utilizations=core_utils,
            total_time=total_time,
            overall_cpu_utilization=overall_util,
            throughput=throughput,
            avg_turnaround=avg_turnaround,
            avg_waiting=avg_waiting,
            avg_response=avg_response
        )


def generate_sample_processes() -> List[SimulatedProcess]:
    """Generate sample processes for simulation."""
    return [
        SimulatedProcess("P1", 0.0, 10.0, io_frequency=5.0, priority=2),
        SimulatedProcess("P2", 1.0, 8.0, io_frequency=3.0, priority=1),
        SimulatedProcess("P3", 2.0, 12.0, io_frequency=0.0, priority=3),
        SimulatedProcess("P4", 3.0, 6.0, io_frequency=4.0, priority=2),
        SimulatedProcess("P5", 5.0, 9.0, io_frequency=6.0, priority=1),
    ]

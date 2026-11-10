"""
Process Manager - Multiprogramming and Multiprocessing Simulation.

Simulates process state transitions, multiprogramming, and multiprocessing.
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


@dataclass
class SimulatedProcess:
    """Process in the simulation."""
    pid: str
    arrival_time: float
    burst_time: float
    io_frequency: float = 0.0  # How often I/O occurs (0 = never)
    priority: int = 0
    
    # Dynamic state
    state: ProcessState = ProcessState.NEW
    remaining_time: float = 0.0
    cpu_time_used: float = 0.0
    io_time_remaining: float = 0.0
    start_time: float = -1.0
    completion_time: float = 0.0
    turnaround_time: float = 0.0
    waiting_time: float = 0.0
    response_time: float = 0.0
    core_id: int = -1  # Which core it's running on (-1 = none)
    
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
        time_slice: float = 2.0,
        max_time: float = 1000.0
    ) -> MultiprogrammingResult:
        """
        Simulate multiprogramming on a single CPU.
        
        Uses Round Robin with I/O handling.
        """
        # Copy processes
        procs = [deepcopy(p) for p in processes]
        procs.sort(key=lambda p: p.arrival_time)
        
        schedule = []
        current_time = 0.0
        ready_queue = []
        running_proc = None
        completed = []
        context_switches = 0
        last_switch_time = 0.0
        max_in_memory = 0
        
        # Track I/O completions
        io_events = []  # (completion_time, process)
        
        process_idx = 0
        n_procs = len(procs)
        
        while len(completed) < n_procs and current_time < max_time:
            # Check for process arrivals
            while process_idx < n_procs and procs[process_idx].arrival_time <= current_time:
                proc = procs[process_idx]
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.CREATED.value)
                ready_queue.append(proc)
                process_idx += 1
            
            # Check for I/O completions
            io_events.sort(key=lambda x: x[0])
            while io_events and io_events[0][0] <= current_time:
                _, proc = io_events.pop(0)
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.IO_COMPLETE.value)
                ready_queue.append(proc)
            
            # Update max multiprogramming degree
            in_memory = len([p for p in procs if p.state != ProcessState.NEW and p.state != ProcessState.TERMINATED])
            max_in_memory = max(max_in_memory, in_memory)
            
            # Schedule next process if CPU free
            if running_proc is None and ready_queue:
                running_proc = ready_queue.pop(0)
                if running_proc.start_time < 0:
                    running_proc.start_time = current_time
                    running_proc.response_time = current_time - running_proc.arrival_time
                
                running_proc.record_state_change(current_time, ProcessState.RUNNING, TransitionReason.SCHEDULED.value)
                running_proc.core_id = 0
                last_switch_time = current_time
                
                schedule.append(CPUScheduleEvent(
                    time=current_time,
                    event_type="start",
                    process_id=running_proc.pid,
                    core_id=0,
                    details=f"Started on CPU"
                ))
            
            if running_proc is None:
                # CPU idle, advance to next event
                next_event_time = max_time
                if process_idx < n_procs:
                    next_event_time = min(next_event_time, procs[process_idx].arrival_time)
                if io_events:
                    next_event_time = min(next_event_time, io_events[0][0])
                
                if next_event_time == current_time:
                    break  # Avoid infinite loop
                
                if next_event_time == max_time:
                    break
                
                current_time = next_event_time
                continue
            
            # Determine how long to run
            run_time = min(time_slice, running_proc.remaining_time)
            
            # Check if I/O should occur during this time slice
            if running_proc.io_frequency > 0:
                # Simulate I/O occurring randomly based on frequency
                io_probability = run_time / running_proc.io_frequency
                if random.random() < io_probability and running_proc.remaining_time > run_time:
                    # I/O occurs
                    io_time = random.uniform(0.5, 3.0)  # I/O duration
                    io_completion = current_time + run_time + io_time
                    
                    running_proc.record_state_change(
                        current_time + run_time, ProcessState.WAITING, TransitionReason.IO_REQUEST.value
                    )
                    running_proc.remaining_time -= run_time
                    running_proc.cpu_time_used += run_time
                    
                    schedule.append(CPUScheduleEvent(
                        time=current_time + run_time,
                        event_type="io",
                        process_id=running_proc.pid,
                        core_id=0,
                        details=f"I/O request (duration: {io_time:.1f})"
                    ))
                    
                    io_events.append((io_completion, running_proc))
                    running_proc = None
                    context_switches += 1
                    current_time += run_time
                    continue
            
            # Normal execution
            current_time += run_time
            running_proc.remaining_time -= run_time
            running_proc.cpu_time_used += run_time
            
            if running_proc.remaining_time <= 0.001:
                # Process completed
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
                running_proc = None
                context_switches += 1
            else:
                # Time slice expired - preempt
                running_proc.record_state_change(current_time, ProcessState.READY, TransitionReason.TIMEOUT.value)
                ready_queue.append(running_proc)
                
                schedule.append(CPUScheduleEvent(
                    time=current_time,
                    event_type="preempt",
                    process_id=running_proc.pid,
                    core_id=0,
                    details=f"Time slice expired ({time_slice})"
                ))
                
                running_proc = None
                context_switches += 1
        
        # Calculate metrics
        total_time = current_time
        busy_time = sum(e.time for e in schedule if e.event_type in ("start", "preempt", "io", "complete"))
        # Actually calculate busy time from execution
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
            degree_of_multiprogramming=max_in_memory
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
        """
        procs = [deepcopy(p) for p in processes]
        procs.sort(key=lambda p: p.arrival_time)
        
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
        
        while len(completed) < n_procs and current_time < max_time:
            # Process arrivals
            while process_idx < n_procs and procs[process_idx].arrival_time <= current_time:
                proc = procs[process_idx]
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.CREATED.value)
                ready_queue.append(proc)
                process_idx += 1
            
            # I/O completions
            io_events.sort(key=lambda x: x[0])
            while io_events and io_events[0][0] <= current_time:
                _, proc = io_events.pop(0)
                proc.record_state_change(current_time, ProcessState.READY, TransitionReason.IO_COMPLETE.value)
                ready_queue.append(proc)
            
            # Schedule on free cores
            for core_id in range(num_cores):
                if core_running[core_id] is None and ready_queue:
                    proc = ready_queue.pop(0)
                    if proc.start_time < 0:
                        proc.start_time = current_time
                        proc.response_time = current_time - proc.arrival_time
                    
                    proc.record_state_change(current_time, ProcessState.RUNNING, TransitionReason.SCHEDULED.value)
                    proc.core_id = core_id
                    core_running[core_id] = proc
                    
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
            
            # Find next event time (minimum of: time slice, I/O, process arrival)
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
            
            current_time = next_time
            
            # Handle events at this time
            # 1. Time slice expiration
            for core_id in range(num_cores):
                proc = core_running[core_id]
                if proc and proc.remaining_time <= 0.001:
                    # Completed
                    proc.completion_time = current_time
                    proc.turnaround_time = current_time - proc.arrival_time
                    proc.waiting_time = proc.turnaround_time - proc.burst_time
                    
                    proc.record_state_change(current_time, ProcessState.TERMINATED, TransitionReason.TERMINATED.value)
                    
                    core_schedules[core_id].append(CPUScheduleEvent(
                        time=current_time, event_type="complete",
                        process_id=proc.pid, core_id=core_id, details="Terminated"
                    ))
                    
                    completed.append(proc)
                    core_running[core_id] = None
                    context_switches += 1
                elif proc and abs(proc.cpu_time_used % time_slice) < 0.001 and proc.remaining_time > 0:
                    # Time slice expired (check if this time slice just ended)
                    # More accurate: check if we just hit a time slice boundary
                    if proc.cpu_time_used >= time_slice and (proc.cpu_time_used - delta) < proc.cpu_time_used:
                        # Check if there's an I/O trigger
                        io_triggered = False
                        if proc.io_frequency > 0:
                            io_prob = delta / proc.io_frequency
                            if random.random() < io_prob:
                                io_time = random.uniform(0.5, 3.0)
                                io_completion = current_time + io_time
                                proc.record_state_change(current_time, ProcessState.WAITING, TransitionReason.IO_REQUEST.value)
                                io_events.append((io_completion, proc))
                                
                                core_schedules[core_id].append(CPUScheduleEvent(
                                    time=current_time, event_type="io",
                                    process_id=proc.pid, core_id=core_id,
                                    details=f"I/O request ({io_time:.1f})"
                                ))
                                core_running[core_id] = None
                                io_triggered = True
                                context_switches += 1
                        
                        if not io_triggered:
                            proc.record_state_change(current_time, ProcessState.READY, TransitionReason.TIMEOUT.value)
                            ready_queue.append(proc)
                            
                            core_schedules[core_id].append(CPUScheduleEvent(
                                time=current_time, event_type="preempt",
                                process_id=proc.pid, core_id=core_id,
                                details=f"Time slice expired"
                            ))
                            core_running[core_id] = None
                            context_switches += 1
            
            # 2. I/O completions (already handled at top of loop)
            # 3. Process arrivals (already handled at top of loop)
        
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
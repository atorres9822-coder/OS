#!/usr/bin/env python3
"""Run all 6 CPU Scheduler algorithms on identical inputs."""
import sys
sys.path.insert(0, '.')

from modules.cpu_scheduling.algorithms import (
    CPUScheduler, Process, AlgorithmType
)

processes = [
    Process(pid="P1", arrival_time=0, burst_time=8, priority=2),
    Process(pid="P2", arrival_time=1, burst_time=4, priority=1),
    Process(pid="P3", arrival_time=2, burst_time=6, priority=3),
    Process(pid="P4", arrival_time=3, burst_time=3, priority=2),
]

algos = [
    ("FCFS", AlgorithmType.FCFS),
    ("SJF", AlgorithmType.SJF),
    ("SRTF", AlgorithmType.SRTF),
    ("Priority NP", AlgorithmType.PRIORITY_NONPREEMPTIVE),
    ("Priority P", AlgorithmType.PRIORITY_PREEMPTIVE),
    ("RR(q=2)", AlgorithmType.ROUND_ROBIN),
]

for name, algo in algos:
    procs = [Process(p.pid, p.arrival_time, p.burst_time, p.priority) for p in processes]
    r = CPUScheduler.run_algorithm(algo, procs)
    print(f"\n=== {name} ===")
    print(f"  total_time={r.total_time}  ctx_switches={r.context_switches}")
    print(f"  avg_turnaround={r.avg_turnaround_time:.2f}  avg_waiting={r.avg_waiting_time:.2f}  avg_response={r.avg_response_time:.2f}")
    print(f"  cpu_util={r.cpu_utilization:.2f}%  throughput={r.throughput:.4f}")
    print(f"  gantt={[f'{g.pid}:{g.start_time}-{g.end_time}' for g in r.gantt_chart]}")

#!/usr/bin/env python3
"""Compare CPU Scheduler vs Process Manager on identical inputs."""
import sys
sys.path.insert(0, '.')

from modules.cpu_scheduling.algorithms import (
    CPUScheduler, Process as CPUProcess, AlgorithmType as CPUAlgo
)
from modules.process_manager.algorithms import (
    ProcessManager, SimulatedProcess as PMProcess, SchedulingAlgorithm as PMAlgo
)

def make_processes():
    cpu = [
        CPUProcess(pid="P1", arrival_time=0, burst_time=8, priority=2),
        CPUProcess(pid="P2", arrival_time=1, burst_time=4, priority=1),
        CPUProcess(pid="P3", arrival_time=2, burst_time=6, priority=3),
        CPUProcess(pid="P4", arrival_time=3, burst_time=3, priority=2),
    ]
    pm = [
        PMProcess(pid="P1", arrival_time=0, burst_time=8, io_frequency=0.0, priority=2),
        PMProcess(pid="P2", arrival_time=1, burst_time=4, io_frequency=0.0, priority=1),
        PMProcess(pid="P3", arrival_time=2, burst_time=6, io_frequency=0.0, priority=3),
        PMProcess(pid="P4", arrival_time=3, burst_time=3, io_frequency=0.0, priority=2),
    ]
    return cpu, pm

def make_processes_all0():
    cpu = [
        CPUProcess(pid="P1", arrival_time=0, burst_time=8, priority=2),
        CPUProcess(pid="P2", arrival_time=0, burst_time=4, priority=1),
        CPUProcess(pid="P3", arrival_time=0, burst_time=6, priority=3),
        CPUProcess(pid="P4", arrival_time=0, burst_time=3, priority=2),
    ]
    pm = [
        PMProcess(pid="P1", arrival_time=0, burst_time=8, io_frequency=0.0, priority=2),
        PMProcess(pid="P2", arrival_time=0, burst_time=4, io_frequency=0.0, priority=1),
        PMProcess(pid="P3", arrival_time=0, burst_time=6, io_frequency=0.0, priority=3),
        PMProcess(pid="P4", arrival_time=0, burst_time=3, io_frequency=0.0, priority=2),
    ]
    return cpu, pm


def print_result(name, r_cpu, r_pm):
    print(f"  CPU Scheduler ({name}):")
    print(f"    total_time={r_cpu.total_time}  ctx_switches={r_cpu.context_switches}")
    print(f"    avg_turnaround={r_cpu.avg_turnaround_time:.2f}  avg_waiting={r_cpu.avg_waiting_time:.2f}  avg_response={r_cpu.avg_response_time:.2f}")
    print(f"    cpu_util={r_cpu.cpu_utilization:.2f}%  throughput={r_cpu.throughput:.4f}")
    print(f"    gantt={[f'{g.pid}:{g.start_time}-{g.end_time}' for g in r_cpu.gantt_chart]}")
    print(f"  Process Manager ({name}):")
    print(f"    total_time={r_pm.total_time}  ctx_switches={r_pm.context_switches}")
    print(f"    avg_turnaround={r_pm.avg_turnaround:.2f}  avg_waiting={r_pm.avg_waiting:.2f}  avg_response={r_pm.avg_response:.2f}")
    print(f"    cpu_util={r_pm.cpu_utilization:.2f}%  throughput={r_pm.throughput:.4f}")
    gantt_pm = []
    if hasattr(r_pm, 'gantt_chart') and r_pm.gantt_chart:
        gantt_pm = [(g.pid, g.start_time, g.end_time) for g in r_pm.gantt_chart]
    elif hasattr(r_pm, 'schedule') and r_pm.schedule:
        current_proc = None
        start_time = 0
        for e in r_pm.schedule:
            if e.event_type == 'start' or e.event_type.startswith('start'):
                if current_proc is not None:
                    gantt_pm.append((current_proc, start_time, e.time))
                current_proc = e.process_id
                start_time = e.time
            elif e.event_type in ('preempt', 'io', 'complete'):
                if current_proc is not None:
                    gantt_pm.append((current_proc, start_time, e.time))
                current_proc = None
    print(f"    gantt_pm={[f'{p}:{s}-{e}' for p,s,e in gantt_pm]}")
    match = (
        abs(r_cpu.total_time - r_pm.total_time) < 0.001
        and r_cpu.context_switches == r_pm.context_switches
        and abs(r_cpu.avg_turnaround_time - r_pm.avg_turnaround) < 0.01
        and abs(r_cpu.avg_waiting_time - r_pm.avg_waiting_time) < 0.01
    )
    print(f"  MATCH: {match}")


pairs = [
    ("FCFS", CPUAlgo.FCFS, PMAlgo.FCFS),
    ("SJF", CPUAlgo.SJF, PMAlgo.SJF),
    ("SRTF", CPUAlgo.SRTF, PMAlgo.SRTF),
    ("RR(q=2)", CPUAlgo.ROUND_ROBIN, PMAlgo.ROUND_ROBIN),
]

for name, cpu_algo, pm_algo in pairs:
    print(f"\n=== {name} (staggered arrivals) ===")
    cpu_p, pm_p = make_processes()
    r_cpu = CPUScheduler.run_algorithm(cpu_algo, cpu_p)
    r_pm = ProcessManager.simulate_multiprogramming(pm_p, pm_algo, 2.0)
    print_result(name, r_cpu, r_pm)

print("\n=== All algorithms with ALL arrivals at 0 ===")
for name, cpu_algo, pm_algo in pairs:
    cpu_p0, pm_p0 = make_processes_all0()
    r_cpu = CPUScheduler.run_algorithm(cpu_algo, cpu_p0)
    r_pm = ProcessManager.simulate_multiprogramming(pm_p0, pm_algo, 2.0)
    print(f"\n--- {name} ---")
    print_result(name, r_cpu, r_pm)

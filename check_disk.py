#!/usr/bin/env python3
"""Run all 6 disk scheduling algorithms on identical inputs."""
import sys
sys.path.insert(0, '.')

from modules.disk_scheduling.algorithms import (
    DiskScheduler, DiskConfig, DiskAlgorithm
)

config = DiskConfig(
    initial_head=50,
    cylinder_range=(0, 199),
    requests=[98, 183, 37, 122, 14, 124, 65, 67],
    initial_direction="up",
)

algos = [
    ("FCFS", DiskAlgorithm.FCFS),
    ("SSTF", DiskAlgorithm.SSTF),
    ("SCAN", DiskAlgorithm.SCAN),
    ("C-SCAN", DiskAlgorithm.CSCAN),
    ("LOOK", DiskAlgorithm.LOOK),
    ("C-LOOK", DiskAlgorithm.CLOOK),
]

print(f"Initial head: {config.initial_head}, Range: {config.cylinder_range}, Requests: {config.requests}")
print()

results = DiskScheduler.compare_all(config)
for algo, r in results.items():
    print(f"=== {algo.value.upper()} ===")
    print(f"  service_order={r.service_order}")
    print(f"  total_head_movement={r.total_head_movement}  avg_seek={r.avg_seek_distance:.2f}")
    print(f"  execution_path={r.execution_path}")
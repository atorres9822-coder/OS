#!/usr/bin/env python3
"""Banker's Algorithm tests on the app's sample state."""
import sys
sys.path.insert(0, '.')

from modules.deadlock.algorithms import (
    BankersAlgorithm, generate_sample_state, BankerState
)

state = generate_sample_state()
print("=== Sample State (classic textbook example) ===")
print(f"  num_processes={state.num_processes}  num_resources={state.num_resources}")
print(f"  available={state.available}")
print(f"  maximum={state.maximum}")
print(f"  allocation={state.allocation}")
print(f"  need={state.need}")
print()

# Safety check
safety = BankersAlgorithm.safety_algorithm(state)
print("=== Safety Algorithm ===")
print(f"  is_safe={safety.is_safe}")
print(f"  safe_sequence={safety.safe_sequence}")
print(f"  work_vector={safety.work_vector}")
print(f"  finish_vector={safety.finish_vector}")
print()

# Resource requests
requests = [
    (1, [1, 0, 2]),   # P1 requests [1, 0, 2]
    (4, [3, 3, 0]),   # P4 requests [3, 3, 0]
    (0, [0, 2, 0]),   # P0 requests [0, 2, 0]
]

for pid, req in requests:
    print(f"=== Resource Request: P{pid} requests {req} ===")
    result = BankersAlgorithm.request_algorithm(state, pid, req)
    print(f"  granted={result.granted}")
    print(f"  new_state is None: {result.new_state is None}")
    if result.safety_result:
        print(f"  safety.is_safe={result.safety_result.is_safe}")
        print(f"  safety.safe_sequence={result.safety_result.safe_sequence}")
    for line in result.explanation:
        print(f"  {line}")
    print()

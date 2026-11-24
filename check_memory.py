#!/usr/bin/env python3
"""Check memory management algorithms."""
import sys
sys.path.insert(0, '.')
from modules.memory.algorithms import (
    PageReplacementSimulator, PageReplacementAlgorithm,
    FragmentationSimulator, AllocationAlgorithm,
    MemoryBlock,
)

ref_string = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
num_frames = 3

print("=== Page Replacement ===")
print(f"Reference string: {ref_string}")
print(f"Number of frames: {num_frames}\n")

for algo in [PageReplacementAlgorithm.FIFO, PageReplacementAlgorithm.LRU, PageReplacementAlgorithm.OPTIMAL]:
    result = PageReplacementSimulator.run_algorithm(algo, ref_string, num_frames)
    print(f"  {algo.value.upper()}:")
    print(f"    total_faults={result.total_faults}  total_hits={result.total_hits}")
    print(f"    fault_rate={result.fault_rate:.2%}  hit_rate={result.hit_rate:.2%}")
    print(f"  frame_states={result.frame_states}")
    print(f"  replaced_pages={result.replaced_pages}")
print()

blocks = [
    MemoryBlock(0, 100),
    MemoryBlock(100, 500),
    MemoryBlock(600, 200),
    MemoryBlock(800, 300),
    MemoryBlock(1100, 600),
]
requests = [
    ("P1", 212),
    ("P2", 417),
    ("P3", 112),
    ("P4", 426),
]

print("=== Memory Fragmentation ===")
print(f"Memory blocks: {[(b.start, b.size) for b in blocks]}")
print(f"Process requests: {requests}")
print()

for algo in [AllocationAlgorithm.FIRST_FIT, AllocationAlgorithm.BEST_FIT, AllocationAlgorithm.WORST_FIT]:
    result = FragmentationSimulator.allocate(algo, blocks, requests)
    print(f"  {algo.value.replace('_', ' ').title()}:")
    print(f"    allocations={result.allocations}")
    final_blocks_str = ", ".join([f"({b.start},{b.size},{b.allocated},{b.process_id})" for b in result.final_blocks])
    print(f"    final_blocks=[{final_blocks_str}]")
    print(f"    allocated_memory={result.allocated_memory}  free_memory={result.free_memory}")
    print(f"    internal_fragmentation={result.internal_fragmentation}  external_fragmentation={result.external_fragmentation}")
    print()

"""
Deadlock Management - Banker's Algorithm for Mini OS Simulator.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from copy import deepcopy
import numpy as np


@dataclass
class BankerState:
    """State of the Banker's algorithm."""
    num_processes: int
    num_resources: int
    available: List[int]
    maximum: List[List[int]]
    allocation: List[List[int]]
    need: List[List[int]]
    
    def __post_init__(self):
        # Calculate need matrix if not provided
        if not self.need:
            self.need = [
                [self.maximum[i][j] - self.allocation[i][j] for j in range(self.num_resources)]
                for i in range(self.num_processes)
            ]
    
    def copy(self) -> 'BankerState':
        return BankerState(
            num_processes=self.num_processes,
            num_resources=self.num_resources,
            available=self.available.copy(),
            maximum=[row.copy() for row in self.maximum],
            allocation=[row.copy() for row in self.allocation],
            need=[row.copy() for row in self.need]
        )


@dataclass
class SafetyResult:
    """Result of safety algorithm."""
    is_safe: bool
    safe_sequence: List[int]
    explanation: List[str]
    work_vector: List[int]
    finish_vector: List[bool]


@dataclass
class RequestResult:
    """Result of resource request algorithm."""
    granted: bool
    new_state: Optional[BankerState]
    safety_result: Optional[SafetyResult]
    explanation: List[str]


class BankersAlgorithm:
    """Banker's Algorithm implementation for deadlock avoidance."""
    
    @staticmethod
    def validate_state(state: BankerState) -> List[str]:
        """Validate the banker state."""
        errors = []
        
        if state.num_processes <= 0:
            errors.append("Number of processes must be positive")
        if state.num_resources <= 0:
            errors.append("Number of resources must be positive")
        if len(state.available) != state.num_resources:
            errors.append("Available vector size mismatch")
        if len(state.maximum) != state.num_processes:
            errors.append("Maximum matrix row count mismatch")
        if len(state.allocation) != state.num_processes:
            errors.append("Allocation matrix row count mismatch")
        if len(state.need) != state.num_processes:
            errors.append("Need matrix row count mismatch")
        
        for i in range(state.num_processes):
            if len(state.maximum[i]) != state.num_resources:
                errors.append(f"Process {i}: Maximum row size mismatch")
            if len(state.allocation[i]) != state.num_resources:
                errors.append(f"Process {i}: Allocation row size mismatch")
            if len(state.need[i]) != state.num_resources:
                errors.append(f"Process {i}: Need row size mismatch")
            
            for j in range(state.num_resources):
                if state.allocation[i][j] > state.maximum[i][j]:
                    errors.append(f"Process {i}, Resource {j}: Allocation exceeds maximum")
                if state.need[i][j] != state.maximum[i][j] - state.allocation[i][j]:
                    errors.append(f"Process {i}, Resource {j}: Need doesn't match Maximum - Allocation")
                if state.allocation[i][j] < 0 or state.maximum[i][j] < 0 or state.need[i][j] < 0:
                    errors.append(f"Process {i}, Resource {j}: Negative values not allowed")
        
        for j in range(state.num_resources):
            if state.available[j] < 0:
                errors.append(f"Resource {j}: Available cannot be negative")
            total_allocated = sum(state.allocation[i][j] for i in range(state.num_processes))
            # Note: We don't know total instances, so can't validate available + allocated <= total
        
        return errors
    
    @staticmethod
    def safety_algorithm(state: BankerState) -> SafetyResult:
        """
        Safety Algorithm - Determines if system is in a safe state.
        
        Returns SafetyResult with safe sequence if safe.
        """
        work = state.available.copy()
        finish = [False] * state.num_processes
        safe_sequence = []
        explanation = []
        
        explanation.append("=== Safety Algorithm Execution ===")
        explanation.append(f"Initial Work = Available = {work}")
        explanation.append(f"Initial Finish = {finish}")
        explanation.append("")
        
        iteration = 0
        while True:
            iteration += 1
            found = False
            
            explanation.append(f"--- Iteration {iteration} ---")
            
            for i in range(state.num_processes):
                if not finish[i]:
                    # Check if Need[i] <= Work
                    need_i = state.need[i]
                    can_allocate = all(need_i[j] <= work[j] for j in range(state.num_resources))
                    
                    if can_allocate:
                        explanation.append(f"Process P{i}: Need = {need_i} <= Work = {work} ✓")
                        explanation.append(f"  -> Simulating completion of P{i}")
                        
                        # Process can finish - add its allocation to work
                        new_work = [work[j] + state.allocation[i][j] for j in range(state.num_resources)]
                        explanation.append(f"  -> Work = Work + Allocation[{i}] = {work} + {state.allocation[i]} = {new_work}")
                        
                        work = new_work
                        finish[i] = True
                        safe_sequence.append(i)
                        found = True
                        explanation.append(f"  -> Finish[{i}] = True")
                        explanation.append("")
                        break
                    else:
                        explanation.append(f"Process P{i}: Need = {need_i} <= Work = {work} ✗")
            
            if not found:
                if all(finish):
                    explanation.append("All processes can finish safely.")
                else:
                    explanation.append("No process found that can complete with current Work.")
                break
        
        is_safe = all(finish)
        
        explanation.append("=== Result ===")
        if is_safe:
            explanation.append(f"System is in a SAFE state.")
            explanation.append(f"Safe Sequence: {' -> '.join(f'P{i}' for i in safe_sequence)}")
            explanation.append("This means there exists an execution order where all processes can complete.")
        else:
            unfinished = [i for i, f in enumerate(finish) if not f]
            explanation.append(f"System is in an UNSAFE state.")
            explanation.append(f"Processes that cannot be guaranteed to complete: {', '.join(f'P{i}' for i in unfinished)}")
            explanation.append("NOTE: An unsafe state does NOT mean deadlock has occurred.")
            explanation.append("It means the system MIGHT enter deadlock depending on future requests.")
        
        return SafetyResult(
            is_safe=is_safe,
            safe_sequence=safe_sequence,
            explanation=explanation,
            work_vector=work,
            finish_vector=finish
        )
    
    @staticmethod
    def request_algorithm(state: BankerState, process_id: int, request: List[int]) -> RequestResult:
        """
        Resource Request Algorithm - Handles resource requests.
        
        Returns RequestResult indicating if request can be granted.
        """
        explanation = []
        explanation.append("=== Resource Request Algorithm ===")
        explanation.append(f"Process P{process_id} requests: {request}")
        explanation.append("")
        
        # Validate request
        if process_id < 0 or process_id >= state.num_processes:
            return RequestResult(
                granted=False,
                new_state=None,
                safety_result=None,
                explanation=explanation + [f"Error: Invalid process ID {process_id}"]
            )
        
        if len(request) != state.num_resources:
            return RequestResult(
                granted=False,
                new_state=None,
                safety_result=None,
                explanation=explanation + [f"Error: Request vector size mismatch"]
            )
        
        # Check 1: Request <= Need
        need_p = state.need[process_id]
        explanation.append(f"Step 1: Check if Request <= Need[P{process_id}]")
        explanation.append(f"  Request = {request}")
        explanation.append(f"  Need[P{process_id}] = {need_p}")
        
        if any(request[j] > need_p[j] for j in range(state.num_resources)):
            explanation.append("  Result: Request exceeds Need - ERROR (process exceeded maximum claim)")
            return RequestResult(
                granted=False,
                new_state=None,
                safety_result=None,
                explanation=explanation
            )
        explanation.append("  Result: Request <= Need ✓")
        explanation.append("")
        
        # Check 2: Request <= Available
        explanation.append(f"Step 2: Check if Request <= Available")
        explanation.append(f"  Request = {request}")
        explanation.append(f"  Available = {state.available}")
        
        if any(request[j] > state.available[j] for j in range(state.num_resources)):
            explanation.append("  Result: Insufficient resources currently available - Process must wait")
            return RequestResult(
                granted=False,
                new_state=None,
                safety_result=None,
                explanation=explanation
            )
        explanation.append("  Result: Request <= Available ✓")
        explanation.append("")
        
        # Step 3: Pretend to allocate and check safety
        explanation.append("Step 3: Simulate allocation and check safety")
        explanation.append("  Pretending to allocate resources...")
        
        # Create tentative new state
        new_state = state.copy()
        for j in range(state.num_resources):
            new_state.available[j] -= request[j]
            new_state.allocation[process_id][j] += request[j]
            new_state.need[process_id][j] -= request[j]
        
        explanation.append(f"  New Available = {new_state.available}")
        explanation.append(f"  New Allocation[P{process_id}] = {new_state.allocation[process_id]}")
        explanation.append(f"  New Need[P{process_id}] = {new_state.need[process_id]}")
        explanation.append("")
        
        # Run safety algorithm on new state
        safety_result = BankersAlgorithm.safety_algorithm(new_state)
        explanation.extend(safety_result.explanation)
        
        if safety_result.is_safe:
            explanation.append("")
            explanation.append("RESULT: Request GRANTED - System remains in safe state")
            return RequestResult(
                granted=True,
                new_state=new_state,
                safety_result=safety_result,
                explanation=explanation
            )
        else:
            explanation.append("")
            explanation.append("RESULT: Request DENIED - Would lead to unsafe state")
            return RequestResult(
                granted=False,
                new_state=None,
                safety_result=safety_result,
                explanation=explanation
            )
    
    @staticmethod
    def create_state(
        num_processes: int,
        num_resources: int,
        available: List[int],
        maximum: List[List[int]],
        allocation: List[List[int]]
    ) -> BankerState:
        """Create a BankerState with validation."""
        need = [
            [maximum[i][j] - allocation[i][j] for j in range(num_resources)]
            for i in range(num_processes)
        ]
        return BankerState(
            num_processes=num_processes,
            num_resources=num_resources,
            available=available,
            maximum=maximum,
            allocation=allocation,
            need=need
        )


def generate_sample_state() -> BankerState:
    """Generate a sample state for demonstration."""
    # Classic textbook example
    num_processes = 5
    num_resources = 3
    
    available = [3, 3, 2]
    maximum = [
        [7, 5, 3],  # P0
        [3, 2, 2],  # P1
        [9, 0, 2],  # P2
        [2, 2, 2],  # P3
        [4, 3, 3],  # P4
    ]
    allocation = [
        [0, 1, 0],  # P0
        [2, 0, 0],  # P1
        [3, 0, 2],  # P2
        [2, 1, 1],  # P3
        [0, 0, 2],  # P4
    ]
    
    return BankersAlgorithm.create_state(num_processes, num_resources, available, maximum, allocation)
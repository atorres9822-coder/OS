"""
Disk Scheduling Algorithms for Mini OS Simulator.

Implements:
- FCFS (First Come First Serve)
- SSTF (Shortest Seek Time First)
- SCAN (Elevator)
- C-SCAN (Circular SCAN)
- LOOK
- C-LOOK
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from copy import deepcopy


class DiskAlgorithm(Enum):
    FCFS = "fcfs"
    SSTF = "sstf"
    SCAN = "scan"
    CSCAN = "cscan"
    LOOK = "look"
    CLOOK = "clook"


@dataclass
class DiskConfig:
    """Disk configuration."""
    initial_head: int
    cylinder_range: Tuple[int, int]  # (min, max)
    requests: List[int]
    initial_direction: str = "up"  # "up" or "down"
    
    def __post_init__(self):
        self.min_cylinder, self.max_cylinder = self.cylinder_range
        
        # Validate
        if not (self.min_cylinder <= self.initial_head <= self.max_cylinder):
            raise ValueError(f"Initial head {self.initial_head} out of range {self.cylinder_range}")
        
        for req in self.requests:
            if not (self.min_cylinder <= req <= self.max_cylinder):
                raise ValueError(f"Request {req} out of range {self.cylinder_range}")
        
        if self.initial_direction not in ("up", "down"):
            raise ValueError("Direction must be 'up' or 'down'")


@dataclass
class DiskResult:
    """Result of disk scheduling simulation."""
    algorithm: DiskAlgorithm
    config: DiskConfig
    service_order: List[int]
    seek_distances: List[int]
    total_head_movement: int
    avg_seek_distance: float
    execution_path: List[Tuple[int, int, int]]  # (from, to, distance)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm.value,
            "initial_head": self.config.initial_head,
            "cylinder_range": self.config.cylinder_range,
            "requests": self.config.requests,
            "initial_direction": self.config.initial_direction,
            "service_order": self.service_order,
            "seek_distances": self.seek_distances,
            "total_head_movement": self.total_head_movement,
            "avg_seek_distance": self.avg_seek_distance,
            "execution_path": self.execution_path,
        }


class DiskScheduler:
    """Disk scheduling algorithm implementations."""
    
    @staticmethod
    def fcfs(config: DiskConfig) -> DiskResult:
        """First Come First Serve."""
        current = config.initial_head
        service_order = []
        seek_distances = []
        execution_path = []
        
        for request in config.requests:
            distance = abs(request - current)
            seek_distances.append(distance)
            execution_path.append((current, request, distance))
            service_order.append(request)
            current = request
        
        total = sum(seek_distances)
        avg = total / len(seek_distances) if seek_distances else 0
        
        return DiskResult(
            algorithm=DiskAlgorithm.FCFS,
            config=config,
            service_order=service_order,
            seek_distances=seek_distances,
            total_head_movement=total,
            avg_seek_distance=avg,
            execution_path=execution_path
        )
    
    @staticmethod
    def sstf(config: DiskConfig) -> DiskResult:
        """Shortest Seek Time First."""
        current = config.initial_head
        remaining = config.requests.copy()
        service_order = []
        seek_distances = []
        execution_path = []
        
        while remaining:
            # Find closest request
            closest = min(remaining, key=lambda r: abs(r - current))
            distance = abs(closest - current)
            
            seek_distances.append(distance)
            execution_path.append((current, closest, distance))
            service_order.append(closest)
            current = closest
            remaining.remove(closest)
        
        total = sum(seek_distances)
        avg = total / len(seek_distances) if seek_distances else 0
        
        return DiskResult(
            algorithm=DiskAlgorithm.SSTF,
            config=config,
            service_order=service_order,
            seek_distances=seek_distances,
            total_head_movement=total,
            avg_seek_distance=avg,
            execution_path=execution_path
        )
    
    @staticmethod
    def scan(config: DiskConfig) -> DiskResult:
        """SCAN (Elevator) - goes to end then reverses."""
        current = config.initial_head
        direction = config.initial_direction  # "up" or "down"
        remaining = config.requests.copy()
        service_order = []
        seek_distances = []
        execution_path = []
        
        min_cyl, max_cyl = config.cylinder_range
        
        while remaining:
            # Find requests in current direction
            if direction == "up":
                candidates = [r for r in remaining if r >= current]
                if candidates:
                    next_req = min(candidates)
                else:
                    # No requests in current direction, go to end and reverse
                    if current != max_cyl:
                        distance = max_cyl - current
                        execution_path.append((current, max_cyl, distance))
                        seek_distances.append(distance)
                        current = max_cyl
                    direction = "down"
                    continue
            else:  # down
                candidates = [r for r in remaining if r <= current]
                if candidates:
                    next_req = max(candidates)
                else:
                    if current != min_cyl:
                        distance = current - min_cyl
                        execution_path.append((current, min_cyl, distance))
                        seek_distances.append(distance)
                        current = min_cyl
                    direction = "up"
                    continue
            
            distance = abs(next_req - current)
            execution_path.append((current, next_req, distance))
            seek_distances.append(distance)
            service_order.append(next_req)
            current = next_req
            remaining.remove(next_req)
        
        total = sum(seek_distances)
        avg = total / len(seek_distances) if seek_distances else 0
        
        return DiskResult(
            algorithm=DiskAlgorithm.SCAN,
            config=config,
            service_order=service_order,
            seek_distances=seek_distances,
            total_head_movement=total,
            avg_seek_distance=avg,
            execution_path=execution_path
        )
    
    @staticmethod
    def cscan(config: DiskConfig) -> DiskResult:
        """C-SCAN (Circular SCAN) - goes to end, jumps to start."""
        current = config.initial_head
        direction = "up"  # C-SCAN always goes up
        remaining = config.requests.copy()
        service_order = []
        seek_distances = []
        execution_path = []
        
        min_cyl, max_cyl = config.cylinder_range
        
        while remaining:
            candidates = [r for r in remaining if r >= current]
            
            if candidates:
                next_req = min(candidates)
                distance = abs(next_req - current)
                execution_path.append((current, next_req, distance))
                seek_distances.append(distance)
                service_order.append(next_req)
                current = next_req
                remaining.remove(next_req)
            else:
                # Go to max, then jump to min
                if current != max_cyl:
                    distance = max_cyl - current
                    execution_path.append((current, max_cyl, distance))
                    seek_distances.append(distance)
                    current = max_cyl
                
                # Jump from max to min (this is a seek too)
                if remaining:
                    distance = max_cyl - min_cyl
                    execution_path.append((max_cyl, min_cyl, distance))
                    seek_distances.append(distance)
                    current = min_cyl
        
        total = sum(seek_distances)
        avg = total / len(seek_distances) if seek_distances else 0
        
        return DiskResult(
            algorithm=DiskAlgorithm.CSCAN,
            config=config,
            service_order=service_order,
            seek_distances=seek_distances,
            total_head_movement=total,
            avg_seek_distance=avg,
            execution_path=execution_path
        )
    
    @staticmethod
    def look(config: DiskConfig) -> DiskResult:
        """LOOK - like SCAN but only goes to last request."""
        current = config.initial_head
        direction = config.initial_direction
        remaining = config.requests.copy()
        service_order = []
        seek_distances = []
        execution_path = []
        
        while remaining:
            if direction == "up":
                candidates = [r for r in remaining if r >= current]
                if candidates:
                    next_req = min(candidates)
                else:
                    # Reverse direction
                    direction = "down"
                    continue
            else:
                candidates = [r for r in remaining if r <= current]
                if candidates:
                    next_req = max(candidates)
                else:
                    direction = "up"
                    continue
            
            distance = abs(next_req - current)
            execution_path.append((current, next_req, distance))
            seek_distances.append(distance)
            service_order.append(next_req)
            current = next_req
            remaining.remove(next_req)
        
        total = sum(seek_distances)
        avg = total / len(seek_distances) if seek_distances else 0
        
        return DiskResult(
            algorithm=DiskAlgorithm.LOOK,
            config=config,
            service_order=service_order,
            seek_distances=seek_distances,
            total_head_movement=total,
            avg_seek_distance=avg,
            execution_path=execution_path
        )
    
    @staticmethod
    def clook(config: DiskConfig) -> DiskResult:
        """C-LOOK - like C-SCAN but only to last request."""
        current = config.initial_head
        direction = "up"
        remaining = config.requests.copy()
        service_order = []
        seek_distances = []
        execution_path = []
        
        while remaining:
            candidates = [r for r in remaining if r >= current]
            
            if candidates:
                next_req = min(candidates)
                distance = abs(next_req - current)
                execution_path.append((current, next_req, distance))
                seek_distances.append(distance)
                service_order.append(next_req)
                current = next_req
                remaining.remove(next_req)
            else:
                # Jump to lowest request
                if remaining:
                    next_req = min(remaining)
                    distance = abs(next_req - current)
                    execution_path.append((current, next_req, distance))
                    seek_distances.append(distance)
                    service_order.append(next_req)
                    current = next_req
                    remaining.remove(next_req)
        
        total = sum(seek_distances)
        avg = total / len(seek_distances) if seek_distances else 0
        
        return DiskResult(
            algorithm=DiskAlgorithm.CLOOK,
            config=config,
            service_order=service_order,
            seek_distances=seek_distances,
            total_head_movement=total,
            avg_seek_distance=avg,
            execution_path=execution_path
        )
    
    @staticmethod
    def run_algorithm(algorithm: DiskAlgorithm, config: DiskConfig) -> DiskResult:
        """Run specified disk scheduling algorithm."""
        if algorithm == DiskAlgorithm.FCFS:
            return DiskScheduler.fcfs(config)
        elif algorithm == DiskAlgorithm.SSTF:
            return DiskScheduler.sstf(config)
        elif algorithm == DiskAlgorithm.SCAN:
            return DiskScheduler.scan(config)
        elif algorithm == DiskAlgorithm.CSCAN:
            return DiskScheduler.cscan(config)
        elif algorithm == DiskAlgorithm.LOOK:
            return DiskScheduler.look(config)
        elif algorithm == DiskAlgorithm.CLOOK:
            return DiskScheduler.clook(config)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    @staticmethod
    def compare_all(config: DiskConfig) -> Dict[DiskAlgorithm, DiskResult]:
        """Run all algorithms for comparison."""
        results = {}
        for algo in DiskAlgorithm:
            results[algo] = DiskScheduler.run_algorithm(algo, config)
        return results


def generate_sample_disk_config() -> DiskConfig:
    """Generate sample disk configuration."""
    return DiskConfig(
        initial_head=50,
        cylinder_range=(0, 199),
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
        initial_direction="up"
    )
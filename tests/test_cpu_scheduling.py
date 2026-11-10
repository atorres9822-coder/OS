"""
Unit tests for CPU Scheduling algorithms.
"""

import unittest
from modules.cpu_scheduling.algorithms import (
    CPUScheduler, Process, AlgorithmType
)


class TestCPUScheduler(unittest.TestCase):
    """Test cases for CPU scheduling algorithms."""
    
    def setUp(self):
        """Set up test processes."""
        self.processes = [
            Process("P1", 0, 8, 3),
            Process("P2", 1, 4, 1),
            Process("P3", 2, 9, 4),
            Process("P4", 3, 5, 2),
        ]
    
    def test_fcfs(self):
        """Test FCFS scheduling."""
        result = CPUScheduler.fcfs(self.processes)
        
        # Check completion times
        self.assertEqual(result.processes[0].completion_time, 8)   # P1
        self.assertEqual(result.processes[1].completion_time, 12)  # P2
        self.assertEqual(result.processes[2].completion_time, 21)  # P3
        self.assertEqual(result.processes[3].completion_time, 26)  # P4
        
        # Check turnaround times
        self.assertEqual(result.processes[0].turnaround_time, 8)
        self.assertEqual(result.processes[1].turnaround_time, 11)
        self.assertEqual(result.processes[2].turnaround_time, 19)
        self.assertEqual(result.processes[3].turnaround_time, 23)
        
        # Check averages
        self.assertAlmostEqual(result.avg_turnaround_time, 15.25, places=2)
        self.assertAlmostEqual(result.avg_waiting_time, 8.75, places=2)
    
    def test_sjf(self):
        """Test SJF scheduling."""
        result = CPUScheduler.sjf(self.processes)
        
        # P1 (8), P2 (4), P3 (9), P4 (5) arrive at 0,1,2,3
        # At time 0: only P1 -> runs 8
        # At time 8: P2(4), P3(9), P4(5) -> SJF picks P2(4)
        # At time 12: P3(9), P4(5) -> picks P4(5)
        # At time 17: P3(9) -> runs
        
        self.assertEqual(result.processes[0].pid, "P1")
        self.assertEqual(result.processes[0].completion_time, 8)
        self.assertEqual(result.processes[1].pid, "P2")
        self.assertEqual(result.processes[1].completion_time, 12)
        self.assertEqual(result.processes[2].pid, "P4")
        self.assertEqual(result.processes[2].completion_time, 17)
        self.assertEqual(result.processes[3].pid, "P3")
        self.assertEqual(result.processes[3].completion_time, 26)
    
    def test_srtf(self):
        """Test SRTF scheduling."""
        result = CPUScheduler.srtf(self.processes)
        
        # SRTF is preemptive
        # Time 0: P1 starts (rem=8)
        # Time 1: P2 arrives (rem=4) < P1(7) -> preempt, P2 runs
        # Time 2: P3 arrives (rem=9) > P2(3) -> P2 continues
        # Time 3: P4 arrives (rem=5) > P2(2) -> P2 continues
        # Time 5: P2 completes
        # Time 5: P4(5) < P1(7) < P3(9) -> P4 runs
        # Time 10: P4 completes
        # Time 10: P1(7) < P3(9) -> P1 runs
        # Time 17: P1 completes
        # Time 17: P3 runs
        # Time 26: P3 completes
        
        p1 = next(p for p in result.processes if p.pid == "P1")
        p2 = next(p for p in result.processes if p.pid == "P2")
        p3 = next(p for p in result.processes if p.pid == "P3")
        p4 = next(p for p in result.processes if p.pid == "P4")
        
        self.assertEqual(p2.completion_time, 5)
        self.assertEqual(p4.completion_time, 10)
        self.assertEqual(p1.completion_time, 17)
        self.assertEqual(p3.completion_time, 26)
    
    def test_priority_nonpreemptive(self):
        """Test Priority Non-preemptive scheduling."""
        result = CPUScheduler.priority_nonpreemptive(self.processes)
        
        # Lower priority number = higher priority
        # At time 0: P1 (pri=3) runs
        # At time 8: P2(1), P3(4), P4(2) -> P2 runs (pri=1)
        # At time 12: P4(2), P3(4) -> P4 runs
        # At time 17: P3 runs
        
        p1 = next(p for p in result.processes if p.pid == "P1")
        p2 = next(p for p in result.processes if p.pid == "P2")
        p3 = next(p for p in result.processes if p.pid == "P3")
        p4 = next(p for p in result.processes if p.pid == "P4")
        
        self.assertEqual(p1.completion_time, 8)
        self.assertEqual(p2.completion_time, 12)
        self.assertEqual(p4.completion_time, 17)
        self.assertEqual(p3.completion_time, 26)
    
    def test_priority_preemptive(self):
        """Test Priority Preemptive scheduling."""
        result = CPUScheduler.priority_preemptive(self.processes)
        
        # Time 0: P1(pri=3) starts
        # Time 1: P2(pri=1) arrives -> preempts P1
        # Time 2: P3(pri=4) arrives -> P2 continues
        # Time 3: P4(pri=2) arrives -> P2 continues
        # Time 5: P2 completes
        # Time 5: P4(pri=2) highest -> runs
        # Time 10: P4 completes
        # Time 10: P1(pri=3) vs P3(pri=4) -> P1 runs
        # Time 17: P1 completes
        # Time 17: P3 runs
        # Time 26: P3 completes
        
        p1 = next(p for p in result.processes if p.pid == "P1")
        p2 = next(p for p in result.processes if p.pid == "P2")
        p3 = next(p for p in result.processes if p.pid == "P3")
        p4 = next(p for p in result.processes if p.pid == "P4")
        
        self.assertEqual(p2.completion_time, 5)
        self.assertEqual(p4.completion_time, 10)
        self.assertEqual(p1.completion_time, 17)
        self.assertEqual(p3.completion_time, 26)
    
    def test_round_robin(self):
        """Test Round Robin scheduling."""
        result = CPUScheduler.round_robin(self.processes, 2.0)
        
        # Time quantum = 2
        # Should have multiple context switches
        self.assertGreater(result.context_switches, 0)
        self.assertEqual(len(result.processes), 4)
        
        # All processes should complete
        for p in result.processes:
            self.assertGreater(p.completion_time, 0)
            self.assertEqual(p.turnaround_time, p.completion_time - p.arrival_time)
            self.assertEqual(p.waiting_time, p.turnaround_time - p.burst_time)
    
    def test_validation(self):
        """Test input validation."""
        # Negative arrival time
        bad_processes = [Process("P1", -1, 5)]
        errors = CPUScheduler.validate_processes(bad_processes)
        self.assertTrue(any("negative" in e.lower() for e in errors))
        
        # Zero burst time
        bad_processes = [Process("P1", 0, 0)]
        errors = CPUScheduler.validate_processes(bad_processes)
        self.assertTrue(any("positive" in e.lower() for e in errors))
        
        # Duplicate PIDs
        bad_processes = [Process("P1", 0, 5), Process("P1", 1, 3)]
        errors = CPUScheduler.validate_processes(bad_processes)
        self.assertTrue(any("duplicate" in e.lower() for e in errors))
    
    def test_empty_processes(self):
        """Test empty process list."""
        errors = CPUScheduler.validate_processes([])
        self.assertTrue(any("required" in e.lower() for e in errors))
    
    def test_single_process(self):
        """Test with single process."""
        processes = [Process("P1", 0, 10)]
        result = CPUScheduler.fcfs(processes)
        
        self.assertEqual(result.processes[0].completion_time, 10)
        self.assertEqual(result.processes[0].turnaround_time, 10)
        self.assertEqual(result.processes[0].waiting_time, 0)
        self.assertEqual(result.avg_turnaround_time, 10)
        self.assertEqual(result.avg_waiting_time, 0)
    
    def test_simultaneous_arrival(self):
        """Test processes arriving at same time."""
        processes = [
            Process("P1", 0, 5),
            Process("P2", 0, 3),
            Process("P3", 0, 8),
        ]
        result = CPUScheduler.fcfs(processes)
        
        # FCFS should maintain order
        self.assertEqual(result.processes[0].pid, "P1")
        self.assertEqual(result.processes[1].pid, "P2")
        self.assertEqual(result.processes[2].pid, "P3")


class TestSchedulingResult(unittest.TestCase):
    """Test scheduling result serialization."""
    
    def test_to_dict(self):
        """Test result to dict conversion."""
        processes = [Process("P1", 0, 5)]
        result = CPUScheduler.fcfs(processes)
        
        d = result.to_dict()
        
        self.assertIn("algorithm", d)
        self.assertIn("processes", d)
        self.assertIn("gantt_chart", d)
        self.assertIn("avg_turnaround_time", d)
        self.assertEqual(d["algorithm"], "fcfs")


if __name__ == "__main__":
    unittest.main()
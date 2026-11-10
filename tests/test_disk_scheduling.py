"""
Unit tests for Disk Scheduling algorithms.
"""

import unittest
from modules.disk_scheduling.algorithms import (
    DiskScheduler, DiskConfig, DiskAlgorithm, generate_sample_disk_config
)


class TestDiskScheduling(unittest.TestCase):
    """Test cases for Disk Scheduling algorithms."""
    
    def setUp(self):
        """Set up disk configuration."""
        self.config = generate_sample_disk_config()
        # Initial head: 50
        # Requests: [98, 183, 37, 122, 14, 124, 65, 67]
        # Range: 0-199
    
    def test_fcfs(self):
        """Test FCFS disk scheduling."""
        result = DiskScheduler.fcfs(self.config)
        
        self.assertEqual(result.algorithm, DiskAlgorithm.FCFS)
        self.assertEqual(result.service_order, self.config.requests)
        self.assertEqual(len(result.seek_distances), len(self.config.requests))
        self.assertEqual(len(result.execution_path), len(self.config.requests))
        
        # Verify first seek: 50 -> 98 = 48
        self.assertEqual(result.seek_distances[0], 48)
        self.assertEqual(result.execution_path[0], (50, 98, 48))
        
        # Total movement should be sum of distances
        self.assertEqual(result.total_head_movement, sum(result.seek_distances))
    
    def test_sstf(self):
        """Test SSTF disk scheduling."""
        result = DiskScheduler.sstf(self.config)
        
        self.assertEqual(result.algorithm, DiskAlgorithm.SSTF)
        self.assertEqual(len(result.service_order), len(self.config.requests))
        
        # First should be closest to 50
        # Distances from 50: 98(48), 183(133), 37(13), 122(72), 14(36), 124(74), 65(15), 67(17)
        # Closest is 37 (distance 13)
        self.assertEqual(result.service_order[0], 37)
    
    def test_scan(self):
        """Test SCAN disk scheduling."""
        result = DiskScheduler.scan(self.config)
        
        self.assertEqual(result.algorithm, DiskAlgorithm.SCAN)
        
        # Initial direction is "up", head at 50
        # Should serve requests >= 50 in ascending order, then go to 199, then serve < 50 descending
        # Requests >= 50: 65, 67, 98, 122, 124, 183
        # Then go to 199
        # Then requests < 50: 37, 14
        
        # First served should be 65 (smallest >= 50)
        self.assertEqual(result.service_order[0], 65)
        
        # Last served should be 14 (smallest overall after reversing)
        self.assertEqual(result.service_order[-1], 14)
    
    def test_cscan(self):
        """Test C-SCAN disk scheduling."""
        result = DiskScheduler.cscan(self.config)
        
        self.assertEqual(result.algorithm, DiskAlgorithm.CSCAN)
        
        # C-SCAN goes up, serves >= 50 ascending, jumps to 0, serves < 50 ascending
        # First served: 65
        self.assertEqual(result.service_order[0], 65)
        
        # After reaching 199, jumps to 0, then serves 14, 37
        # Last served: 37
        self.assertEqual(result.service_order[-1], 37)
    
    def test_look(self):
        """Test LOOK disk scheduling."""
        result = DiskScheduler.look(self.config)
        
        self.assertEqual(result.algorithm, DiskAlgorithm.LOOK)
        
        # LOOK is like SCAN but only goes to last request, not end of disk
        # First served: 65 (smallest >= 50)
        self.assertEqual(result.service_order[0], 65)
        
        # Last served: 14 (smallest < 50 after reversing)
        self.assertEqual(result.service_order[-1], 14)
    
    def test_clook(self):
        """Test C-LOOK disk scheduling."""
        result = DiskScheduler.clook(self.config)
        
        self.assertEqual(result.algorithm, DiskAlgorithm.CLOOK)
        
        # C-LOOK goes up to last request, jumps to first request
        # First served: 65
        self.assertEqual(result.service_order[0], 65)
        
        # Last served: 37 (last request < 50)
        self.assertEqual(result.service_order[-1], 37)
    
    def test_compare_all(self):
        """Test comparison of all algorithms."""
        results = DiskScheduler.compare_all(self.config)
        
        self.assertEqual(len(results), 6)
        for algo in DiskAlgorithm:
            self.assertIn(algo, results)
            self.assertEqual(len(results[algo].service_order), len(self.config.requests))
    
    def test_total_movement_calculation(self):
        """Test that total movement equals sum of individual seeks."""
        for algo in DiskAlgorithm:
            result = DiskScheduler.run_algorithm(algo, self.config)
            self.assertEqual(result.total_head_movement, sum(result.seek_distances))
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Head out of range
        with self.assertRaises(ValueError):
            DiskConfig(200, (0, 199), [50], "up")
        
        # Request out of range
        with self.assertRaises(ValueError):
            DiskConfig(50, (0, 199), [200], "up")
        
        # Invalid direction
        with self.assertRaises(ValueError):
            DiskConfig(50, (0, 199), [50], "left")
    
    def test_empty_requests(self):
        """Test with empty request queue."""
        config = DiskConfig(50, (0, 199), [], "up")
        result = DiskScheduler.fcfs(config)
        
        self.assertEqual(result.total_head_movement, 0)
        self.assertEqual(result.avg_seek_distance, 0)
        self.assertEqual(len(result.service_order), 0)
    
    def test_single_request(self):
        """Test with single request."""
        config = DiskConfig(50, (0, 199), [100], "up")
        result = DiskScheduler.fcfs(config)
        
        self.assertEqual(result.service_order, [100])
        self.assertEqual(result.seek_distances, [50])
        self.assertEqual(result.total_head_movement, 50)
        self.assertEqual(result.avg_seek_distance, 50)
    
    def test_request_at_head(self):
        """Test request at initial head position."""
        config = DiskConfig(50, (0, 199), [50, 100], "up")
        result = DiskScheduler.fcfs(config)
        
        # First seek should be 0
        self.assertEqual(result.seek_distances[0], 0)
        self.assertEqual(result.service_order[0], 50)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases."""
    
    def test_all_requests_same_direction(self):
        """Test when all requests are in one direction."""
        config = DiskConfig(50, (0, 199), [60, 70, 80, 90], "up")
        
        for algo in [DiskAlgorithm.SCAN, DiskAlgorithm.LOOK]:
            result = DiskScheduler.run_algorithm(algo, config)
            # Should serve in ascending order
            self.assertEqual(result.service_order, [60, 70, 80, 90])
    
    def test_requests_both_sides(self):
        """Test requests on both sides of head."""
        config = DiskConfig(50, (0, 199), [40, 60], "up")
        
        scan_result = DiskScheduler.scan(config)
        # SCAN: serves 60 (up), then 40 (after reversing)
        self.assertEqual(scan_result.service_order[0], 60)
        self.assertEqual(scan_result.service_order[1], 40)


if __name__ == "__main__":
    unittest.main()
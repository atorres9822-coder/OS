"""
Unit tests for Memory Management algorithms.
"""

import unittest
from modules.memory.algorithms import (
    PagingConfig, PagingSimulator, PageTableEntry,
    PageReplacementAlgorithm, PageReplacementSimulator,
    Segment, SegmentationSimulator,
    AllocationAlgorithm, MemoryBlock, FragmentationSimulator,
    generate_sample_page_references
)


class TestPaging(unittest.TestCase):
    """Test cases for Paging."""
    
    def setUp(self):
        """Set up paging configuration."""
        self.config = PagingConfig(
            logical_memory_size=64 * 1024,  # 64 KB
            physical_memory_size=32 * 1024,  # 32 KB
            page_size=4 * 1024  # 4 KB
        )
        
        # Page table with some mappings
        self.page_table = [
            PageTableEntry(frame_number=2, valid=True),   # Page 0 -> Frame 2
            PageTableEntry(frame_number=0, valid=True),   # Page 1 -> Frame 0
            PageTableEntry(frame_number=5, valid=True),   # Page 2 -> Frame 5
            PageTableEntry(),                              # Page 3 invalid
            PageTableEntry(),                              # Page 4 invalid
        ]
    
    def test_translate_valid_address(self):
        """Test translation of valid address."""
        # Page 0, offset 100 -> Frame 2, offset 100 = 8192 + 100 = 8292
        phys, valid, _ = PagingSimulator.translate_address(
            self.config, 100, self.page_table
        )
        self.assertTrue(valid)
        self.assertEqual(phys, 2 * 4096 + 100)
    
    def test_translate_page_boundary(self):
        """Test translation at page boundary."""
        # Page 1 starts at 4096
        phys, valid, _ = PagingSimulator.translate_address(
            self.config, 4096, self.page_table
        )
        self.assertTrue(valid)
        self.assertEqual(phys, 0 * 4096 + 0)  # Frame 0, offset 0
    
    def test_translate_invalid_page(self):
        """Test translation of invalid page."""
        # Page 3 is invalid
        phys, valid, _ = PagingSimulator.translate_address(
            self.config, 3 * 4096 + 100, self.page_table
        )
        self.assertFalse(valid)
        self.assertIsNone(phys)
    
    def test_translate_out_of_bounds(self):
        """Test translation beyond logical memory."""
        phys, valid, _ = PagingSimulator.translate_address(
            self.config, 64 * 1024, self.page_table
        )
        self.assertFalse(valid)
    
    def test_create_page_table(self):
        """Test page table creation."""
        assignments = {0: 2, 1: 0, 2: 5}
        page_table = PagingSimulator.create_page_table(self.config, assignments)
        
        self.assertEqual(len(page_table), 16)  # 64KB / 4KB = 16 pages
        self.assertTrue(page_table[0].valid)
        self.assertEqual(page_table[0].frame_number, 2)
        self.assertTrue(page_table[1].valid)
        self.assertFalse(page_table[3].valid)


class TestPageReplacement(unittest.TestCase):
    """Test cases for Page Replacement algorithms."""
    
    def setUp(self):
        """Set up reference string."""
        self.ref_string = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
        self.num_frames = 3
    
    def test_fifo(self):
        """Test FIFO page replacement."""
        result = PageReplacementSimulator.fifo(self.ref_string, self.num_frames)
        
        self.assertEqual(result.algorithm, PageReplacementAlgorithm.FIFO)
        self.assertEqual(result.num_frames, self.num_frames)
        self.assertEqual(len(result.frame_states), len(self.ref_string))
        self.assertEqual(len(result.page_faults), len(self.ref_string))
        
        # First 3 references should be faults
        self.assertTrue(result.page_faults[0])
        self.assertTrue(result.page_faults[1])
        self.assertTrue(result.page_faults[2])
        
        # Total faults should be > 0
        self.assertGreater(result.total_faults, 0)
        self.assertEqual(result.total_faults + result.total_hits, len(self.ref_string))
    
    def test_lru(self):
        """Test LRU page replacement."""
        result = PageReplacementSimulator.lru(self.ref_string, self.num_frames)
        
        self.assertEqual(result.algorithm, PageReplacementAlgorithm.LRU)
        self.assertEqual(result.num_frames, self.num_frames)
        self.assertGreater(result.total_faults, 0)
    
    def test_optimal(self):
        """Test Optimal page replacement."""
        result = PageReplacementSimulator.optimal(self.ref_string, self.num_frames)
        
        self.assertEqual(result.algorithm, PageReplacementAlgorithm.OPTIMAL)
        self.assertEqual(result.num_frames, self.num_frames)
        self.assertGreater(result.total_faults, 0)
    
    def test_optimal_better_than_fifo(self):
        """Test that Optimal has fewer or equal faults than FIFO."""
        fifo_result = PageReplacementSimulator.fifo(self.ref_string, self.num_frames)
        optimal_result = PageReplacementSimulator.optimal(self.ref_string, self.num_frames)
        
        # Optimal should never have more faults than FIFO
        self.assertLessEqual(optimal_result.total_faults, fifo_result.total_faults)
    
    def test_compare_all(self):
        """Test comparison of all algorithms."""
        results = PageReplacementSimulator.compare_all(self.ref_string, self.num_frames)
        
        self.assertEqual(len(results), 3)
        for algo in PageReplacementAlgorithm:
            self.assertIn(algo, results)
    
    def test_single_frame(self):
        """Test with single frame."""
        result = PageReplacementSimulator.fifo([1, 2, 3, 1, 2], 1)
        
        # Every reference should be a fault except repeats immediately after
        self.assertEqual(result.total_faults, 5)  # All different pages
    
    def test_all_same_page(self):
        """Test with all same page references."""
        result = PageReplacementSimulator.fifo([1, 1, 1, 1], 3)
        
        self.assertEqual(result.total_faults, 1)  # Only first is fault
        self.assertEqual(result.total_hits, 3)


class TestSegmentation(unittest.TestCase):
    """Test cases for Segmentation."""
    
    def setUp(self):
        """Set up segments."""
        self.segments = [
            Segment(0, "Code", 0, 1024),
            Segment(1, "Data", 1024, 2048),
            Segment(2, "Stack", 4096, 1024),
        ]
    
    def test_translate_valid(self):
        """Test valid address translation."""
        # Segment 0, offset 100 -> physical 100
        result = SegmentationSimulator.translate_address(self.segments, (0, 100))
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_address, 100)
        
        # Segment 1, offset 500 -> physical 1024 + 500 = 1524
        result = SegmentationSimulator.translate_address(self.segments, (1, 500))
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_address, 1524)
    
    def test_translate_invalid_segment(self):
        """Test invalid segment."""
        result = SegmentationSimulator.translate_address(self.segments, (5, 100))
        self.assertFalse(result.valid)
        self.assertIsNone(result.physical_address)
        self.assertIn("not exist", result.error.lower())
    
    def test_translate_offset_overflow(self):
        """Test offset exceeding segment limit."""
        # Segment 0 limit is 1024, offset 1024 is invalid
        result = SegmentationSimulator.translate_address(self.segments, (0, 1024))
        self.assertFalse(result.valid)
        self.assertIn("exceeds segment limit", result.error.lower())
    
    def test_explain_translation(self):
        """Test explanation generation."""
        explanation = SegmentationSimulator.explain_translation(self.segments, (1, 500))
        
        self.assertIn("Segment=1", explanation)
        self.assertIn("Offset=500", explanation)
        self.assertIn("1524", explanation)
        self.assertIn("Physical Address", explanation)


class TestFragmentation(unittest.TestCase):
    """Test cases for Memory Fragmentation."""
    
    def setUp(self):
        """Set up memory blocks and requests."""
        self.blocks = [
            MemoryBlock(0, 100),
            MemoryBlock(100, 500),
            MemoryBlock(600, 200),
            MemoryBlock(800, 300),
            MemoryBlock(1100, 400),
        ]
        self.requests = [
            ("P1", 212),
            ("P2", 417),
            ("P3", 112),
            ("P4", 426),
        ]
    
    def test_first_fit(self):
        """Test First Fit allocation."""
        result = FragmentationSimulator.allocate(
            AllocationAlgorithm.FIRST_FIT, self.blocks, self.requests
        )
        
        self.assertEqual(result.algorithm, AllocationAlgorithm.FIRST_FIT)
        self.assertEqual(len(result.allocations), 4)
        
        # Check first allocation (P1=212) -> first block that fits is 500 at 100
        self.assertTrue(result.allocations[0][3])  # success
        self.assertEqual(result.allocations[0][2], 100)  # start address
    
    def test_best_fit(self):
        """Test Best Fit allocation."""
        result = FragmentationSimulator.allocate(
            AllocationAlgorithm.BEST_FIT, self.blocks, self.requests
        )
        
        self.assertEqual(result.algorithm, AllocationAlgorithm.BEST_FIT)
        # Best fit should find smallest block that fits
    
    def test_worst_fit(self):
        """Test Worst Fit allocation."""
        result = FragmentationSimulator.allocate(
            AllocationAlgorithm.WORST_FIT, self.blocks, self.requests
        )
        
        self.assertEqual(result.algorithm, AllocationAlgorithm.WORST_FIT)
        # Worst fit should find largest block
    
    def test_allocation_failure(self):
        """Test allocation failure when no block fits."""
        # Add a huge request
        requests = self.requests + [("P5", 10000)]
        result = FragmentationSimulator.allocate(
            AllocationAlgorithm.FIRST_FIT, self.blocks, requests
        )
        
        # Last request should fail
        self.assertFalse(result.allocations[-1][3])
    
    def test_compare_all(self):
        """Test comparison of all algorithms."""
        results = FragmentationSimulator.compare_all(self.blocks, self.requests)
        
        self.assertEqual(len(results), 3)
        for algo in AllocationAlgorithm:
            self.assertIn(algo, results)
    
    def test_external_fragmentation(self):
        """Test external fragmentation calculation."""
        result = FragmentationSimulator.allocate(
            AllocationAlgorithm.FIRST_FIT, self.blocks, self.requests
        )
        
        # External fragmentation is sum of free blocks
        self.assertGreaterEqual(result.external_fragmentation, 0)
        self.assertEqual(
            result.allocated_memory + result.free_memory,
            sum(b.size for b in self.blocks)
        )


if __name__ == "__main__":
    unittest.main()
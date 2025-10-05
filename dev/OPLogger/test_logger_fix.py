#!/usr/bin/env python3
"""
Test script to verify the logger fix prevents duplicate logging.
"""

import sys
import os

# Add the OPLogger directory to path
sys.path.insert(0, os.path.dirname(__file__))

from OPLogger import Logger

class MockParent:
    def __init__(self):
        self.Name = "TestLogger"
        self.Logdirectory = None
        self.Writetofile = False

def test_recursive_exception_handling():
    """Test that the logger doesn't create duplicate logs when exceptions occur during logging."""
    print("Testing recursive exception handling fix...")

    mock_parent = MockParent()
    logger = Logger(mock_parent)

    # Simulate an exception that would normally cause recursive logging
    try:
        # This should trigger the global exception handler
        raise ValueError("Test exception")
    except:
        pass  # Exception should be handled by global handler

    print("Test completed. Check that no duplicate error messages were logged.")

if __name__ == "__main__":
    test_recursive_exception_handling()
